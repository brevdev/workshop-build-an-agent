from routing_lab_answers_import_helper import answers as lab
from conftest import FakeResponse, FakeChat
from constants import STRONG_MODEL, EFFICIENT_MODEL, CLASSIFIER_MODEL, PRICING
import switchyard_shim as shim

def test_bill_call_prices_and_counterfactuals():
    bill = lab.RunningBill()
    # Asymmetric on purpose: 1M/1M would price the same even if in/out rates swapped.
    chat = FakeChat([FakeResponse("hi", in_tok=2_000_000, out_tok=1_000_000)])
    resp, receipt = lab.bill_call(EFFICIENT_MODEL, chat, "prompt", bill)
    p = PRICING[EFFICIENT_MODEL]; pf = PRICING[STRONG_MODEL]
    assert abs(receipt["cost"] - (2 * p["in"] + p["out"])) < 1e-9
    assert abs(receipt["counterfactual_cost"] - (2 * pf["in"] + pf["out"])) < 1e-9
    assert bill.total_cost == receipt["cost"]

def test_running_bill_accumulates_by_model():
    bill = lab.RunningBill()
    bill.add(EFFICIENT_MODEL, {"input_tokens": 10, "output_tokens": 10}, 0.01, 0.5)
    bill.add(STRONG_MODEL, {"input_tokens": 10, "output_tokens": 10}, 0.20, 1.5)
    assert set(bill.by_model) == {EFFICIENT_MODEL, STRONG_MODEL}
    assert abs(bill.total_cost - 0.21) < 1e-9

def test_receipt_carries_every_key_the_client_reads():
    # The client and race mode index these by name -- all eight must be present.
    bill = lab.RunningBill()
    chat = FakeChat([FakeResponse("hi")])
    _, receipt = lab.bill_call(EFFICIENT_MODEL, chat, "prompt", bill)
    assert set(receipt) == {"model", "input_tokens", "output_tokens", "cost",
                            "latency", "counterfactual_cost", "why", "router_tax"}
    assert receipt["model"] == EFFICIENT_MODEL
    assert (receipt["input_tokens"], receipt["output_tokens"]) == (100, 20)
    assert receipt["router_tax"] == 0.0 and receipt["latency"] >= 0.0

def test_default_judge_grades_with_the_strong_model(monkeypatch):
    graded = FakeChat([FakeResponse("PASS -- meets the rubric.")])
    monkeypatch.setattr(lab, "build_model_pool",
                        lambda: {"strong": graded, "efficient": FakeChat([FakeResponse("nope")])})
    assert lab._default_judge("rubric text", "answer text") is True
    assert len(graded.calls) == 1          # the judge asks the strong model, once

    failed = FakeChat([FakeResponse("FAIL: only one bullet.")])
    monkeypatch.setattr(lab, "build_model_pool",
                        lambda: {"strong": failed, "efficient": FakeChat([FakeResponse("nope")])})
    assert lab._default_judge("rubric text", "answer text") is False

def test_run_suite_bills_every_task_under_a_passthrough_strategy(monkeypatch):
    chat = FakeChat([FakeResponse("1969")])   # one queued response, replayed for all 12
    monkeypatch.setattr(lab, "build_model_pool", lambda: {"strong": chat, "efficient": chat})
    bill = lab.RunningBill()
    results = lab.run_suite("efficient_only", bill, judge=lambda rubric, out: True)
    assert len(results) == 12 and len(chat.calls) == 12
    assert set(results[0]) == {"id", "kind", "passed", "cost", "latency", "models", "router_tax"}
    assert bill.by_model[EFFICIENT_MODEL]["calls"] == 12
    assert abs(sum(r["cost"] for r in results) - bill.total_cost) < 1e-9

# --- Exercise 2: the hand-rolled classifier router ---------------------------

def test_classifier_is_built_with_thinking_off(monkeypatch):
    # Load-bearing knob, not a style choice: with thinking ON the classifier spends its whole
    # 8-token budget deliberating, never says COMMODITY, and fail-up routes 100% to the strong
    # model -- a router that looks healthy and routes nothing. Recorded, not constructed for
    # real: building a ChatNVIDIA hits the network and warns.
    seen = {}
    def recorder(**kwargs):
        seen.update(kwargs)
        return "client"
    monkeypatch.setattr(lab, "ChatNVIDIA", recorder)
    assert lab.build_classifier() == "client"
    assert seen["model"] == CLASSIFIER_MODEL
    assert seen["model_kwargs"] == {"chat_template_kwargs": {"thinking": False}}

def test_classifier_parses_and_fails_up(fake_chat):
    bill = lab.RunningBill()
    assert lab.classify_difficulty("q", fake_chat("COMMODITY"), bill)[0] == "COMMODITY"
    assert lab.classify_difficulty("q", fake_chat("frontier."), bill)[0] == "FRONTIER"
    assert lab.classify_difficulty("q", fake_chat("dunno maybe hard?"), bill)[0] == "FRONTIER"  # fail UP

def test_classifier_survives_an_empty_completion(fake_chat):
    # A truncated/thinking-mode reply can come back blank -- parse it, don't crash on it.
    bill = lab.RunningBill()
    assert lab.classify_difficulty("q", fake_chat("   "), bill)[0] == "FRONTIER"
    assert lab.classify_difficulty("q", FakeChat([FakeResponse(None)]), bill)[0] == "FRONTIER"

def test_route_call_dispatches_and_taxes(fake_chat, monkeypatch):
    bill = lab.RunningBill()
    pool = {"strong": fake_chat("strong answer"), "efficient": fake_chat("easy answer")}
    monkeypatch.setattr(lab, "build_classifier", lambda: fake_chat("COMMODITY"))
    resp, receipt = lab.route_call("reformat this", pool, bill)
    assert receipt["model"] == lab.EFFICIENT_MODEL
    assert receipt["router_tax"] > 0
    assert "COMMODITY" in receipt["why"]

def test_route_call_sends_frontier_verdicts_to_the_strong_lane(fake_chat, monkeypatch):
    bill = lab.RunningBill()
    strong, efficient = fake_chat("strong answer"), fake_chat("easy answer")
    monkeypatch.setattr(lab, "build_classifier", lambda: fake_chat("FRONTIER"))
    resp, receipt = lab.route_call("plan the migration", {"strong": strong, "efficient": efficient}, bill)
    assert receipt["model"] == STRONG_MODEL and receipt["why"] == "classifier: FRONTIER"
    assert resp.content == "strong answer"
    assert len(strong.calls) == 1 and len(efficient.calls) == 0   # FakeChat replays: count, don't peek

def test_router_tax_is_real_money_on_the_meter(fake_chat, monkeypatch):
    bill = lab.RunningBill()
    classifier, efficient = fake_chat("COMMODITY"), fake_chat("easy answer")
    monkeypatch.setattr(lab, "build_classifier", lambda: classifier)
    _, receipt = lab.route_call("reformat this", {"strong": fake_chat("strong"), "efficient": efficient}, bill)
    # Two billed calls, one meter: the answer plus its tax, counted once each.
    assert bill.by_model[CLASSIFIER_MODEL]["calls"] == 2   # classifier IS the efficient model, by design
    assert abs(bill.total_cost - (receipt["cost"] + receipt["router_tax"])) < 1e-9
    assert len(classifier.calls) == 1 and len(efficient.calls) == 1
    assert "reformat this" in classifier.calls[0]          # the query reaches the classify prompt

# --- Exercise 3: the Switchyard stage router --------------------------------
# SDK-independent by design: the mock path plus dependency injection cover the
# wiring, and the real SDK is proven by the live smoke, not by pytest.

def test_mock_router_is_deterministic():
    r = shim.MockRouter()
    assert r.pick(["short prompt"], []) == "efficient"
    assert r.pick(["x" * 500], []) == "capable"
    assert r.pick(["x" * 500], ["tool_result"]) == "efficient"
    assert r.pick([], []) == "efficient"      # empty history must not IndexError

def test_shim_request_carries_tool_events_as_the_verified_block_shapes():
    # libsy's Rust deserializer accepts `tool_call`/`tool_result` with a
    # `tool_call_id`; the Anthropic spelling (`tool_use`/`tool_use_id`) raises
    # `unknown variant`/`missing field`. Pinned here so a rename fails loudly.
    req = shim._request(["do the thing"], ["FAILED tests/test_a.py"])
    assert [b["type"] for m in req["messages"] for b in m["content"]] == \
           ["text", "tool_call", "tool_result"]
    result = req["messages"][-1]["content"][0]
    assert result["tool_call_id"] == "t0"
    assert result["content"] == [{"type": "text", "text": "FAILED tests/test_a.py"}]

def test_make_router_falls_back_loudly_when_the_sdk_is_missing(monkeypatch, capsys):
    # The spec's churn armor: an unusable SDK must degrade to a router that still
    # teaches, and it must say so. Silence here is the failure mode we are guarding.
    monkeypatch.setattr(shim, "SDK_AVAILABLE", False)
    router = shim.make_router({"id": STRONG_MODEL}, {"id": EFFICIENT_MODEL})
    out = capsys.readouterr().out
    assert isinstance(router, shim.MockRouter)
    assert out.startswith("⚠️") and "MockRouter" in out and "install_switchyard.sh" in out

def test_make_router_falls_back_when_the_sdk_constructor_churns(monkeypatch, capsys):
    # Pre-alpha upstream: the likelier break is not a missing import but stage_router
    # gaining/renaming a required kwarg. Same landing: banner + MockRouter, never a
    # traceback out of make_router.
    def churned(*args, **kwargs):
        raise TypeError("stage_router() missing 1 required keyword-only argument: 'picker'")
    monkeypatch.setattr(shim, "SDK_AVAILABLE", True)
    monkeypatch.setattr(shim, "LlmTarget", lambda name, client: (name, client), raising=False)
    monkeypatch.setattr(shim, "algorithms",
                        type("algorithms", (), {"stage_router": staticmethod(churned)}), raising=False)
    router = shim.make_router({"id": STRONG_MODEL}, {"id": EFFICIENT_MODEL})
    out = capsys.readouterr().out
    assert isinstance(router, shim.MockRouter)
    assert out.startswith("⚠️") and "picker" in out and "MockRouter" in out

def test_switchyard_call_traces_every_turn(capsys, fake_chat):
    # The [route → …] line is the exercise's visible payload (spec §4 Ex3b): it is how
    # the learner watches the stage transition happen.
    bill = lab.RunningBill()
    pool = {"strong": fake_chat("deep answer"), "efficient": fake_chat("quick answer")}
    lab.switchyard_call("short prompt", pool, bill, router=shim.MockRouter())
    lab.switchyard_call("x" * 500, pool, bill, router=shim.MockRouter())
    traced = capsys.readouterr().out
    assert "[route → efficient]" in traced and "[route → capable]" in traced

def test_make_lab_router_passes_the_pinned_ids_in_the_documented_order(monkeypatch):
    # stage_router(capable, efficient) -- the argument order is easy to get
    # backwards, and swapping it silently inverts every routing decision.
    seen = {}
    monkeypatch.setattr(shim, "make_router",
                        lambda cap, eff: seen.update(capable=cap, efficient=eff) or "router")
    assert lab.make_lab_router() == "router"
    assert seen == {"capable": {"id": STRONG_MODEL}, "efficient": {"id": EFFICIENT_MODEL}}

def test_switchyard_call_routes_via_router(fake_chat):
    bill = lab.RunningBill()
    pool = {"strong": fake_chat("deep answer"), "efficient": fake_chat("quick answer")}
    resp, receipt = lab.switchyard_call("short prompt", pool, bill, router=shim.MockRouter())
    assert receipt["model"] == lab.EFFICIENT_MODEL
    assert receipt["router_tax"] == 0.0        # stage routing: no extra LLM call
    assert receipt["why"].startswith(("stage:", "mock"))
    assert resp.content == "quick answer"

def test_switchyard_call_sends_the_capable_stage_to_the_strong_lane(fake_chat):
    bill = lab.RunningBill()
    strong, efficient = fake_chat("deep answer"), fake_chat("quick answer")
    _, receipt = lab.switchyard_call("x" * 500, {"strong": strong, "efficient": efficient},
                                     bill, router=shim.MockRouter())
    assert receipt["model"] == STRONG_MODEL and receipt["why"] == "mock"
    assert len(strong.calls) == 1 and len(efficient.calls) == 0   # count, don't peek

def test_switchyard_call_names_the_stage_when_the_sdk_decides(monkeypatch, fake_chat):
    # The SDK path's receipt vocabulary, exercised without the SDK: anything that
    # is not a MockRouter takes the `stage:` branch.
    monkeypatch.setattr(shim, "pick_target", lambda router, messages, tool_events: router)
    bill = lab.RunningBill()
    pool = {"strong": fake_chat("deep answer"), "efficient": fake_chat("quick answer")}
    _, capable = lab.switchyard_call("q", pool, bill, router="capable")
    _, efficient = lab.switchyard_call("q", pool, bill, router="efficient")
    assert (capable["model"], capable["why"]) == (STRONG_MODEL, "stage: synthesis")
    assert (efficient["model"], efficient["why"]) == (EFFICIENT_MODEL, "stage: exploration")

def test_stage_routing_bills_one_call_and_charges_no_tax(fake_chat):
    # Honest by construction: the stage signal is already in the trajectory, so
    # there is no second call to bill and no hidden latency to hide.
    bill = lab.RunningBill()
    strong, efficient = fake_chat("deep answer"), fake_chat("quick answer")
    _, receipt = lab.switchyard_call("short prompt", {"strong": strong, "efficient": efficient},
                                     bill, router=shim.MockRouter())
    assert (len(efficient.calls), len(strong.calls)) == (1, 0)
    assert list(bill.by_model) == [EFFICIENT_MODEL] and bill.by_model[EFFICIENT_MODEL]["calls"] == 1
    assert receipt["router_tax"] == 0.0 and abs(bill.total_cost - receipt["cost"]) < 1e-9

def test_run_suite_routes_the_whole_suite_through_the_stage_router(monkeypatch):
    # run_suite's provided branch calls switchyard_call(prompt, pool, bill) -- the
    # router has to come from make_lab_router(), which is the seam patched here.
    chat = FakeChat([FakeResponse("1969")])
    monkeypatch.setattr(lab, "build_model_pool", lambda: {"strong": chat, "efficient": chat})
    monkeypatch.setattr(lab, "make_lab_router", lambda: shim.MockRouter())
    bill = lab.RunningBill()
    results = lab.run_suite("switchyard_stage", bill, judge=lambda rubric, out: True)
    assert len(results) == 12 and len(chat.calls) == 12     # one billed call per task, no tax call
    assert all(r["router_tax"] == 0.0 for r in results)

# --- Exercise 5: the verdict ------------------------------------------------

def _mk(strategy, passed, cost, strong_calls, tax):
    return [{"id": f"t{i}", "kind": "commodity", "passed": i < passed, "cost": cost / 12,
             "latency": 1.0, "models": {lab.STRONG_MODEL if i < strong_calls else lab.EFFICIENT_MODEL: 1},
             "router_tax": tax / 12} for i in range(12)]

def test_routing_verdict_math():
    v = lab.routing_verdict({
        "strong_only": _mk("strong_only", 12, 1.55, 12, 0.0),
        "efficient_only": _mk("efficient_only", 9, 0.10, 0, 0.0),
        "manual_classifier": _mk("manual_classifier", 11, 0.41, 3, 0.04),
    })
    routed = next(r for r in v["rows"] if r["strategy"] == "manual_classifier")
    assert routed["accuracy"] == 11 and abs(routed["frontier_pct"] - 25.0) < 0.1
    assert abs(v["savings_pct"] - (1 - 0.41 / 1.55) * 100) < 0.1
    assert "$" in v["receipt"] and "%" in v["receipt"]
    assert abs(v["monthly"]["strong_only"] - 1.55 * lab.AT_SCALE_TASKS_PER_DAY * 30) < 1e-6
