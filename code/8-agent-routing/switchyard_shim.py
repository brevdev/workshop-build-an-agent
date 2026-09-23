"""The ONLY file in Module 8 that imports the Switchyard SDK (spec §8b.3).
If the import or API shifts upstream, fix it HERE — nothing else changes.
Pins live in scripts/install_switchyard.sh; the surface this file was written
against is docs/specs/switchyard-api-notes.md (nemo-switchyard 0.2.0)."""
import asyncio, concurrent.futures

SDK_AVAILABLE = True
try:
    from switchyard.libsy import LlmTarget, algorithms
except Exception:                                # ImportError or any v0.x surprise
    SDK_AVAILABLE = False

# stage_router's two required knobs. "efficient_first" = efficient is the default
# tier, capable only when the trajectory scorer is confidently positive.
PICKER, CONFIDENCE_THRESHOLD = "efficient_first", 0.5

class MockRouter:
    """Deterministic fallback + 'Demo (mock)' strategy. Heuristic stage signal:
    tool activity or short prompts → efficient; otherwise capable."""
    def pick(self, messages, tool_events):
        text = str(messages[-1]) if messages else ""
        if tool_events or len(text) < 200:
            return "efficient"
        return "capable"

class _DecisionOnlyClient:
    """libsy algorithms call their targets' clients themselves; the lab must own
    the call (bill_call is the meter), so the router gets an empty completion —
    pick_target spends zero tokens and no network."""
    def __init__(self, model_id): self.model_id = model_id
    async def call(self, request):
        return {"id": "decision-only", "model": self.model_id,
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "outputs": [{"role": "assistant", "content": [{"type": "text", "text": ""}]}]}

def make_router(capable_meta, efficient_meta):
    if not SDK_AVAILABLE:
        print("⚠️  switchyard SDK unavailable — using MockRouter (see scripts/install_switchyard.sh)")
        return MockRouter()
    try:
        return algorithms.stage_router(                           # capable FIRST, then efficient
            LlmTarget("capable", _DecisionOnlyClient(capable_meta["id"])),
            LlmTarget("efficient", _DecisionOnlyClient(efficient_meta["id"])),
            picker=PICKER, confidence_threshold=CONFIDENCE_THRESHOLD)
    except Exception as exc:                                      # pre-alpha: expect constructor churn
        print(f"⚠️  switchyard stage_router rejected its arguments ({exc}) — using MockRouter")
        return MockRouter()

def _request(messages, tool_events):
    """The neutral request libsy scores: text turns, then one tool_call/tool_result
    pair per tool event — that trajectory IS the stage signal."""
    msgs = [{"role": "user", "content": [{"type": "text", "text": str(m)}]} for m in messages]
    for i, event in enumerate(tool_events):
        msgs += [{"role": "assistant", "content": [
                     {"type": "tool_call", "id": f"t{i}", "name": "tool", "arguments": "{}"}]},
                 {"role": "user", "content": [
                     {"type": "tool_result", "tool_call_id": f"t{i}",
                      "content": [{"type": "text", "text": str(event)}]}]}]
    return {"model": "switchyard", "messages": msgs, "output": {"max_output_tokens": 16}}

def pick_target(router, messages, tool_events):
    if isinstance(router, MockRouter):
        return router.pick(messages, tool_events)
    async def decide():                          # build router.run() INSIDE a running loop, never as
        decisions, _ = await router.run(_request(messages, tool_events))   # an asyncio.run() argument
        return decisions[0]["selected_model"]    # == the LlmTarget name we chose
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        name = asyncio.run(decide())             # plain script: no loop yet
    else:                                        # notebook/server: borrow a thread with its own loop
        with concurrent.futures.ThreadPoolExecutor(1) as pool:
            name = pool.submit(asyncio.run, decide()).result()
    return "capable" if name == "capable" else "efficient"
