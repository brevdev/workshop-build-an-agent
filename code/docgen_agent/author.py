"""Authoring workflow for writing sections of a report."""

import json
import logging
import os
from typing import Annotated, Any, Sequence

from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from . import tools
from .prompts import section_research_prompt, section_writing_prompt

_LOGGER = logging.getLogger(__name__)
_MAX_LLM_RETRIES = 3

llm = ChatOpenAI(
    model="nvidia/nemotron-nano-9b-v2",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://github.com/workshop-build-an-agent",
        "X-Title": "Workshop Build an Agent",
    }
)
llm_with_tools = llm.bind_tools([tools.search_tavily])


class Section(BaseModel):
    name: str
    description: str
    research: bool
    content: str


class SectionWriterState(BaseModel):
    index: int = -1
    section: Section
    topic: str  # Overall report topic for context
    messages: Annotated[Sequence[Any], add_messages] = []


async def tool_node(state: SectionWriterState):
    """Execute tool calls for research."""
    _LOGGER.info("Executing tool calls for section: %s", state.section.name)
    outputs = []
    for tool_call in state.messages[-1].tool_calls:
        _LOGGER.info("Executing tool call: %s", tool_call["name"])
        tool = getattr(tools, tool_call["name"])
        tool_result = await tool.ainvoke(tool_call["args"])
        outputs.append(
            {
                "role": "tool",
                "content": json.dumps(tool_result),
                "name": tool_call["name"],
                "tool_call_id": tool_call["id"],
            }
        )
    return {"messages": outputs}


async def research_model(
    state: SectionWriterState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Call model for research queries if section needs research."""
    _LOGGER.info("Researching section: %s", state.section.name)
    system_prompt = section_research_prompt.format(
        section_name=state.section.name,
        section_description=state.section.description,
        overall_topic=state.topic,
    )

    for count in range(_MAX_LLM_RETRIES):
        messages = [{"role": "system", "content": system_prompt}] + list(state.messages)
        response = await llm_with_tools.ainvoke(messages, config)

        if response:
            return {"messages": [response]}

        _LOGGER.debug(
            "Retrying LLM call. Attempt %d of %d", count + 1, _MAX_LLM_RETRIES
        )

    raise RuntimeError("Failed to call model after %d attempts.", _MAX_LLM_RETRIES)


async def writing_model(
    state: SectionWriterState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Call model to write the section content."""
    _LOGGER.info("Writing section: %s", state.section.name)
    system_prompt = section_writing_prompt.format(
        section_name=state.section.name,
        section_description=state.section.description,
        overall_topic=state.topic,
    )

    for count in range(_MAX_LLM_RETRIES):
        messages = [{"role": "system", "content": system_prompt}] + list(state.messages)
        response = await llm.ainvoke(messages, config)

        if response:
            # Update the section content with the written content
            updated_section = state.section.model_copy()
            updated_section.content = str(response.content) if response.content else ""
            return {"section": updated_section, "messages": [response]}

        _LOGGER.debug(
            "Retrying LLM call. Attempt %d of %d", count + 1, _MAX_LLM_RETRIES
        )

    raise RuntimeError("Failed to call model after %d attempts.", _MAX_LLM_RETRIES)


def needs_research(state: SectionWriterState) -> str:
    """Check if the section needs research."""
    return "research" if state.section.research else "write"


def has_tool_calls(state: SectionWriterState) -> bool:
    """Check if the last message has tool calls."""
    messages = state.messages
    if not messages:
        return False
    last_message = messages[-1]
    return bool(hasattr(last_message, "tool_calls") and last_message.tool_calls)


workflow = StateGraph(SectionWriterState)

workflow.add_node("agent", research_model)
workflow.add_node("tools", tool_node)
workflow.add_node("writer", writing_model)

workflow.add_conditional_edges(
    START,
    needs_research,
    {
        "research": "agent",
        "write": "writer",
    },
)
workflow.add_conditional_edges(
    "agent",
    has_tool_calls,
    {
        True: "tools",
        False: "writer",
    },
)
workflow.add_edge("tools", "agent")
workflow.add_edge("writer", END)

graph = workflow.compile()
