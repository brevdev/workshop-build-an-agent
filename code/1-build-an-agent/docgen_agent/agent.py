"""
The main agent that orchestrates the report generation process.
"""

import asyncio
import json
import logging
import os
import re
from typing import Annotated, Any, Sequence, cast

from langchain_core.runnables import RunnableConfig
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from . import author, researcher
from .prompts import report_planner_instructions
from .json_utils import parse_json_response

_LOGGER = logging.getLogger(__name__)
_MAX_LLM_RETRIES = 3
_QUERIES_PER_SECTION = 5
_THROTTLE_LLM_CALLS = os.getenv("THROTTLE_LLM_CALLS", "0")

llm = ChatNVIDIA(
    base_url="https://openrouter.ai/api/v1",
    model="nvidia/nemotron-nano-9b-v2", 
    temperature=0.0,
    api_key=os.getenv("OPENROUTER_API_KEY")
)


class Report(BaseModel):
    title: str
    sections: list[author.Section]


class AgentState(BaseModel):
    topic: str
    report_structure: str
    report_plan: Report | None = None
    report: str | None = None
    messages: Annotated[Sequence[Any], add_messages] = []


async def topic_research(state: AgentState, config: RunnableConfig):
    """Research the topic of the document."""
    _LOGGER.info("Performing initial topic research.")

    researcher_state = researcher.ResearcherState(
        topic=state.topic,
        number_of_queries=_QUERIES_PER_SECTION,
        messages=state.messages,
    )

    research = await researcher.graph.ainvoke(researcher_state, config)

    return {"messages": research.get("messages", [])}


async def report_planner(state: AgentState, config: RunnableConfig):
    """Call the model using JSON mode."""
    _LOGGER.info("Calling report planner.")

    user_prompt = report_planner_instructions.format(
        topic=state.topic,
        report_structure=state.report_structure,
    )
    
    for count in range(_MAX_LLM_RETRIES):
        # Use only system and user messages for report planning to avoid confusion from conversation history
        messages = [
            {"role": "system", "content": "/no_think You are a report planner. Respond only with valid JSON in the requested format."},
            {"role": "user", "content": user_prompt}
        ]
        response = await llm.ainvoke(messages, config)
        
        if response and response.content:
            try:
                # Parse JSON response into Report model
                parsed_report = parse_json_response(response.content, Report)
                state.report_plan = parsed_report
                return state
            except ValueError as e:
                _LOGGER.warning("Failed to parse JSON response on attempt %d: %s", count + 1, e)
                if count == _MAX_LLM_RETRIES - 1:
                    _LOGGER.error("Raw response was: %s", response.content)
        else:
            _LOGGER.warning("Empty response on attempt %d", count + 1)
        
        _LOGGER.debug(
            "Retrying LLM call. Attempt %d of %d", count + 1, _MAX_LLM_RETRIES
        )

    raise RuntimeError("Failed to call model after %d attempts.", _MAX_LLM_RETRIES)


async def section_author_orchestrator(state: AgentState, config: RunnableConfig):
    """Orchestrate the section authoring process."""
    if not state.report_plan:
        raise ValueError("Report plan is not set.")

    _LOGGER.info("Orchestrating the section authoring process.")

    writers = []
    for idx, section in enumerate(state.report_plan.sections):
        _LOGGER.info("Creating author agent for section: %s", section.name)

        section_writer_state = author.SectionWriterState(
            index=idx,
            section=section,
            topic=state.topic,
            messages=[],  # Start with empty messages for each section to avoid interference
        )
        writers.append(author.graph.ainvoke(section_writer_state, config))

    all_sections = []
    if _THROTTLE_LLM_CALLS == "1":
        # Throttle LLM calls by writing one section at a time
        _LOGGER.info("Throttling LLM calls.")
        for writer in writers:
            all_sections.append(await writer)
            await asyncio.sleep(30)
    else:
        # Without throttling, write all sections at once
        all_sections = await asyncio.gather(*writers)
    all_sections = cast(list[dict[str, Any]], all_sections)

    for section in all_sections:
        index = section["index"]
        content = section["section"].content
        section_name = state.report_plan.sections[index].name
        
        # Debug: Log section content details
        _LOGGER.info("Finished section: %s", section_name)
        _LOGGER.info("Section content length: %d characters", len(content))
        if "Note: The actual section content will be drafted" in content:
            _LOGGER.warning("Section '%s' contains placeholder content!", section_name)
        _LOGGER.info("Section content preview: %s", content[:200] + "..." if len(content) > 200 else content)
        
        state.report_plan.sections[index].content = content

    return state


async def report_author(state: AgentState, config: RunnableConfig):
    """Write the report."""
    if not state.report_plan:
        raise ValueError("Report plan is not set.")

    _LOGGER.info("Authoring the report.")

    output = f"# {state.report_plan.title}\n\n"
    for section in state.report_plan.sections:
        output += section.content
        output += "\n\n"

    state.report = output
    return state


workflow = StateGraph(AgentState)

workflow.add_node("topic_research", topic_research)
workflow.add_node("report_planner", report_planner)
workflow.add_node("section_author_orchestrator", section_author_orchestrator)
workflow.add_node("report_author", report_author)

workflow.add_edge(START, "topic_research")
workflow.add_edge("topic_research", "report_planner")
workflow.add_edge("report_planner", "section_author_orchestrator")
workflow.add_edge("section_author_orchestrator", "report_author")
workflow.add_edge("report_author", END)

graph = workflow.compile()
