"""
FastAPI server with session-based agent management, SSE streaming,
human-in-the-loop approval, and skills support.
"""

import json
import re
import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Literal

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from agent import create_agent, MODEL_MAP, MODEL_DISPLAY_NAMES  # noqa: E402
from capabilities import enabled_tools

def _safe_error_message(error: BaseException, action: str = "Agent run") -> str:
    """Expose error type/status, never provider payloads or credential-bearing URLs."""
    status = getattr(error, "status_code", None) or getattr(error, "status", None)
    if status is None:
        response = getattr(error, "response", None)
        status = getattr(response, "status_code", None) or getattr(response, "status", None)
    # NVIDIA's SDK may raise a plain Exception with a leading HTTP status.
    if status is None:
        match = re.match(r"^\[([45]\d{2})\]", str(error))
        status = int(match.group(1)) if match else None
    code = f"; HTTP {status}" if isinstance(status, int) and 400 <= status <= 599 else ""
    hint = " Wait and retry." if status == 429 else " Check the service and configuration."
    return f"{action} failed ({type(error).__name__}{code}).{hint}"


@asynccontextmanager
async def lifespan(app):
    yield
    for session in list(sessions.values()):
        if session.sandbox is not None:
            try:
                await asyncio.to_thread(session.sandbox.delete)
            except Exception as e:
                print(_safe_error_message(e, "Sandbox cleanup"))
    sessions.clear()


app = FastAPI(title="Deep Agent Backend", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Session store ────────────────────────────────────────────────────────────

class AgentSession:
    def __init__(self, agent, model_id: str, skill_ids: list[str], thread_id: str, hitl_enabled: bool, sandbox=None):
        self.agent = agent
        self.model_id = model_id
        self.skill_ids = skill_ids
        self.thread_id = thread_id
        self.hitl_enabled = hitl_enabled
        self.sandbox = sandbox  # Docker sandbox reference for cleanup
        self.messages: list = []
        self.pending_interrupt: dict | None = None
        self.created_at = time.time()

    @property
    def config(self):
        return {"configurable": {"thread_id": self.thread_id}, "recursion_limit": 120}

sessions: dict[str, AgentSession] = {}


# ── Request models ───────────────────────────────────────────────────────────

class CreateAgentRequest(BaseModel):
    model_id: str = "nemotron"
    skill_ids: list[str] = []
    hitl_enabled: bool = False
    sandbox_map: dict[str, bool] = {}

class ChatRequest(BaseModel):
    message: str

class ApprovalRequest(BaseModel):
    decision: Literal["approve", "reject", "edit"] = "approve"  # "approve" | "reject" | "edit"
    edited_args: dict | None = None


# ── Tool mappings ────────────────────────────────────────────────────────────

ICON_MAP = {
    "tavily_search_results_json": "🌐", "tavily_search_results": "🌐",
    "read_file": "📖", "write_file": "✏️", "edit_file": "📝",
    "ls": "📂", "glob": "🔍", "grep": "🔎",
    "execute": "💻",
    "write_todos": "📋", "read_todos": "📋",
    "task": "🤖",
    "it_knowledge_base": "📚",
}

SKILL_ID_MAP = {
    "tavily_search_results_json": "websearch", "tavily_search_results": "websearch",
    "read_file": "fileio", "write_file": "fileio", "edit_file": "fileio",
    "ls": "fileio", "glob": "fileio", "grep": "fileio",
    "execute": "execute",
    "write_todos": "planning", "read_todos": "planning",
    "task": "task",
    "it_knowledge_base": "rag",
}


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "deep-agent-backend", "sessions": len(sessions)}


@app.get("/api/models")
async def model_choices():
    return {"models": [{"id": key, "name": MODEL_DISPLAY_NAMES[key], "model": value}
                       for key, value in MODEL_MAP.items()]}


@app.post("/api/agent")
async def create_agent_session(request: CreateAgentRequest):
    """Create a new agent session."""
    try:
        session_id = str(uuid.uuid4())[:8]
        thread_id = f"thread-{session_id}"
        agent, sandbox = await asyncio.to_thread(
            create_agent, request.skill_ids, request.model_id, request.hitl_enabled, request.sandbox_map
        )
        sessions[session_id] = AgentSession(
            agent, request.model_id, request.skill_ids, thread_id, request.hitl_enabled, sandbox=sandbox
        )
        sandboxed_tools = [k for k, v in request.sandbox_map.items() if v]
        # Report the ACTUAL sandbox state, not what was requested. `sandbox` is
        # non-None only when the Docker container was really created.
        # The UI drives its badge from these so it never shows "🔒 Sandboxed"
        # over unsandboxed execution.
        sandbox_requested = bool(sandboxed_tools)
        sandbox_active = sandbox is not None
        print(f"[Session] Created {session_id} model={request.model_id} hitl={request.hitl_enabled} "
              f"sandbox_requested={sandbox_requested} sandbox_active={sandbox_active}")
        return {
            "session_id": session_id,
            "hitl_enabled": request.hitl_enabled,
            "sandbox_requested": sandbox_requested,
            "sandbox_active": sandbox_active,
            "enabled_tools": sorted(enabled_tools(request.skill_ids)),
            "capabilities": {
                "file_root": ("/workspace" if sandbox_active else "/") if "fileio" in request.skill_ids else None,
                "execution": ("container" if sandbox_active else "host user") if "execute" in request.skill_ids else "disabled",
                "container_network": "none" if sandbox_active else None,
                "web_and_rag": "application-side tools",
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        message = _safe_error_message(e, "Agent creation")
        print(message)
        raise HTTPException(status_code=500, detail=message) from e


@app.delete("/api/agent/{session_id}")
async def delete_agent_session(session_id: str):
    """Destroy an agent session and its sandbox if any."""
    if session_id in sessions:
        session = sessions[session_id]
        # Clean up Docker sandbox container
        if session.sandbox:
            try:
                session.sandbox.delete()
                print(f"[Session] Deleted sandbox for {session_id}")
            except Exception as e:
                print(_safe_error_message(e, "Sandbox cleanup"))
        del sessions[session_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.post("/api/agent/{session_id}/chat")
async def chat_with_session(session_id: str, request: ChatRequest):
    """Stream a response from an agent session. May pause for approval if HITL is enabled."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.messages.append(HumanMessage(content=request.message))
    return EventSourceResponse(_stream_response(session, request.message))


@app.post("/api/agent/{session_id}/approve")
async def approve_tool_call(session_id: str, request: ApprovalRequest):
    """Resume an interrupted agent with approval/rejection."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.pending_interrupt:
        raise HTTPException(status_code=400, detail="No pending interrupt")

    if request.decision == "edit":
        actions = session.pending_interrupt.get("action_requests", [])
        if len(actions) != 1 or not request.edited_args:
            raise HTTPException(status_code=422, detail="Editing requires one pending action and its edited arguments.")

    return EventSourceResponse(_stream_resume(session, request.decision, request.edited_args))


# ── Streaming helpers ────────────────────────────────────────────────────────

async def _stream_response(session: AgentSession, user_message: str) -> AsyncGenerator[dict, None]:
    try:
        tool_timers: dict[str, float] = {}
        full_response = ""

        async for event in session.agent.astream_events(
            {"messages": [HumanMessage(content=user_message)]},
            version="v2",
            config=session.config,
        ):
            result = _process_event(event, tool_timers)
            if result:
                if result["event"] == "token":
                    full_response += json.loads(result["data"])["content"]
                yield result

        # Check for interrupt
        state = await session.agent.aget_state(session.config)
        if state.next and state.tasks:
            for task in state.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    for intr in task.interrupts:
                        interrupt_data = intr.value
                        session.pending_interrupt = interrupt_data
                        yield {
                            "event": "interrupt",
                            "data": json.dumps({
                                "action_requests": interrupt_data.get("action_requests", []),
                                "review_configs": interrupt_data.get("review_configs", []),
                            }),
                        }
                        return  # Don't send done — waiting for approval

        if full_response:
            session.messages.append(AIMessage(content=full_response))

        yield {"event": "done", "data": "{}"}

    except Exception as e:
        message = _safe_error_message(e)
        print(message)
        yield {"event": "error", "data": json.dumps({"message": message})}


async def _stream_resume(session: AgentSession, decision: str, edited_args: dict | None) -> AsyncGenerator[dict, None]:
    try:
        interrupt_data = session.pending_interrupt
        session.pending_interrupt = None

        # Count how many action_requests need a decision
        num_actions = len(interrupt_data.get("action_requests", [])) if interrupt_data else 1

        # Build decision list — one decision per interrupted tool call
        decisions = [{"type": decision} for _ in range(num_actions)]
        if decision == "edit" and edited_args and num_actions == 1:
            decisions = [{"type": "edit", "edited_action": edited_args}]

        tool_timers: dict[str, float] = {}
        full_response = ""

        async for event in session.agent.astream_events(
            Command(resume={"decisions": decisions}),
            version="v2",
            config=session.config,
        ):
            result = _process_event(event, tool_timers)
            if result:
                if result["event"] == "token":
                    full_response += json.loads(result["data"])["content"]
                yield result

        # Check for another interrupt (chained)
        state = await session.agent.aget_state(session.config)
        if state.next and state.tasks:
            for task in state.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    for intr in task.interrupts:
                        interrupt_data = intr.value
                        session.pending_interrupt = interrupt_data
                        yield {
                            "event": "interrupt",
                            "data": json.dumps({
                                "action_requests": interrupt_data.get("action_requests", []),
                                "review_configs": interrupt_data.get("review_configs", []),
                            }),
                        }
                        return

        if full_response:
            session.messages.append(AIMessage(content=full_response))

        yield {"event": "done", "data": "{}"}

    except Exception as e:
        message = _safe_error_message(e)
        print(message)
        yield {"event": "error", "data": json.dumps({"message": message})}


def _process_event(event: dict, tool_timers: dict[str, float]) -> dict | None:
    """Process a single astream_events event into an SSE dict."""
    kind = event.get("event", "")

    if kind == "on_chat_model_stream":
        chunk = event.get("data", {}).get("chunk")
        if chunk and hasattr(chunk, "content") and chunk.content:
            content = chunk.content
            if isinstance(content, list):
                content = "".join(block.get("text", "") for block in content
                                  if isinstance(block, dict) and block.get("type") == "text")
            if content:
                return {"event": "token", "data": json.dumps({"content": content})}

    elif kind == "on_tool_start":
        tool_name = event.get("name", "unknown")
        run_id = event.get("run_id", "")
        tool_input = event.get("data", {}).get("input", "")
        tool_timers[run_id] = time.time()
        print(f"[Tool] START {tool_name}: {str(tool_input)[:150]}")

        input_str = str(tool_input)
        if len(input_str) > 200:
            input_str = input_str[:200] + "..."

        return {
            "event": "tool_start",
            "data": json.dumps({
                "id": run_id,
                "name": tool_name,
                "skillId": SKILL_ID_MAP.get(tool_name, "api"),
                "icon": ICON_MAP.get(tool_name, "🔧"),
                "action": tool_name.replace("_", " "),
                "input": input_str,
            }),
        }

    elif kind in ("on_tool_end", "on_tool_error"):
        run_id = event.get("run_id", "")
        tool_name = event.get("name", "unknown")
        data = event.get("data", {})
        output = data.get("output", "")
        if kind == "on_tool_error":
            error = data.get("error")
            output = _safe_error_message(error, "Tool execution") if isinstance(error, BaseException) else "Tool execution failed."
        # ToolMessage status is structured metadata; ordinary file text may contain
        # words such as "error" without indicating a failed tool call.
        status = "error" if kind == "on_tool_error" or getattr(output, "status", None) == "error" else "success"
        start_time = tool_timers.pop(run_id, time.time())
        duration_ms = int((time.time() - start_time) * 1000)
        print(f"[Tool] END   {tool_name} ({duration_ms}ms): {str(output)[:150]}")

        output_str = str(output)
        if len(output_str) > 300:
            output_str = output_str[:300] + "..."

        return {
            "event": "tool_end",
            "data": json.dumps({
                "id": run_id,
                "name": tool_name,
                "output": output_str,
                "duration": duration_ms,
                "status": status,
            }),
        }

    elif kind == "on_chat_model_end":
        message = event.get("data", {}).get("output")
        if message and hasattr(message, "usage_metadata") and message.usage_metadata:
            usage = message.usage_metadata
            output_tok = usage.get("output_tokens", 0)

            # Try standard LangChain field first (future-proof)
            output_details = usage.get("output_token_details") or {}
            reasoning_tokens = output_details.get("reasoning", 0)

            if not reasoning_tokens:
                # Find reasoning text: prefer additional_kwargs, fall back to <think> tags
                reasoning_text = ""
                if hasattr(message, "additional_kwargs"):
                    reasoning_text = message.additional_kwargs.get("reasoning_content", "")
                content_str = str(message.content) if hasattr(message, "content") and message.content else ""
                if not reasoning_text and content_str:
                    think_matches = re.findall(r'<think>([\s\S]*?)</think>', content_str)
                    reasoning_text = ''.join(think_matches)

                # Estimate reasoning tokens as a proportion of output_tokens
                # so that reasoning + output-only always == output_tokens
                if reasoning_text and output_tok:
                    output_only_text = re.sub(r'<think>[\s\S]*?</think>', '', content_str).strip()
                    total_chars = len(reasoning_text) + len(output_only_text)
                    if total_chars > 0:
                        reasoning_tokens = max(1, int(output_tok * len(reasoning_text) / total_chars))

            return {
                "event": "usage",
                "data": json.dumps({
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": output_tok,
                    "total_tokens": usage.get("total_tokens", 0),
                    "reasoning_tokens": reasoning_tokens,
                }),
            }

    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
