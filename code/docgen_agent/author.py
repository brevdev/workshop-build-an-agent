"""Authoring workflow for writing sections of a report."""

import os, json
import logging
from typing import Annotated, Any, Sequence

from langchain_core.runnables import RunnableConfig
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from . import tools
from .prompts import section_research_prompt, section_writing_prompt

_LOGGER = logging.getLogger(__name__)
_MAX_LLM_RETRIES = 3

llm = ChatNVIDIA(
    base_url="https://openrouter.ai/api/v1",
    model="nvidia/nemotron-nano-9b-v2", 
    temperature=0.0,
    api_key=os.getenv("OPENROUTER_API_KEY")
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
    user_prompt = section_research_prompt.format(
        section_name=state.section.name,
        section_description=state.section.description,
        overall_topic=state.topic,
    )

    for count in range(_MAX_LLM_RETRIES):
        messages = [{"role": "system", "content": "/no_think"}, {"role": "user", "content": user_prompt}] + list(state.messages)
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
    user_prompt = section_writing_prompt.format(
        section_name=state.section.name,
        section_description=state.section.description,
        overall_topic=state.topic,
    )

    for count in range(_MAX_LLM_RETRIES):
        # Extract research information from messages and clean it up
        research_context = ""
        for msg in state.messages:
            if hasattr(msg, 'content') and msg.content:
                # Debug: log message details
                _LOGGER.info("Processing message - type: %s, has name: %s, name value: %s, content preview: %s", 
                           type(msg).__name__, 
                           hasattr(msg, 'name'), 
                           getattr(msg, 'name', 'N/A'),
                           str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content))
                
                # Check for tool results - look for both name attribute and content patterns
                is_tool_result = False
                if hasattr(msg, 'name') and msg.name == 'search_tavily':
                    is_tool_result = True
                elif isinstance(msg.content, str) and "Sources:" in msg.content:
                    is_tool_result = True
                elif hasattr(msg, 'role') and getattr(msg, 'role') == 'tool':
                    is_tool_result = True
                
                if is_tool_result:
                    content_str = str(msg.content)
                    # If content is JSON string, try to parse it
                    if content_str.startswith('{') or content_str.startswith('['):
                        try:
                            import json
                            parsed_content = json.loads(content_str)
                            if isinstance(parsed_content, str):
                                content_str = parsed_content
                        except:
                            pass  # Keep original content if JSON parsing fails
                    
                    research_context += f"\nResearch Information:\n{content_str}\n"
        
        # Create clean messages with research context embedded in the user prompt
        enhanced_prompt = user_prompt
        if research_context:
            enhanced_prompt += f"\n\nAvailable Research Context:\n{research_context[:2000]}..."  # Limit context size
        else:
            # For sections without research, emphasize writing from general knowledge
            enhanced_prompt += "\n\nNOTE: No specific research context is available. Write this section using your general knowledge about the topic. Do not mention the lack of research or use placeholder text."
        
        messages = [
            {"role": "system", "content": "/no_think You are a technical writer. Your task is to write the actual section content immediately - not to plan, outline, or suggest what should be written. Write complete paragraphs with specific details, examples, and technical information. Never use placeholder text like 'Note: content will be drafted' or similar phrases. Start writing the section content immediately."},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        # Log the full prompt being sent for debugging
        _LOGGER.info("Writing prompt for section '%s':", state.section.name)
        _LOGGER.info("User prompt length: %d characters", len(enhanced_prompt))
        _LOGGER.info("Research context included: %s", "Yes" if research_context else "No")
        _LOGGER.info("First 300 chars of prompt: %s", enhanced_prompt[:300] + "...")
        
        response = await llm.ainvoke(messages, config)

        if response:
            # Log the response for debugging
            _LOGGER.info("Model response for section '%s': %s", state.section.name, 
                        str(response.content)[:300] + "..." if len(str(response.content)) > 300 else str(response.content))
            
            # Check if the response contains placeholder text
            response_text = str(response.content) if response.content else ""
            if "Note: The actual section content will be drafted" in response_text:
                _LOGGER.warning("Model returned placeholder content instead of actual section content!")
                _LOGGER.warning("Full response: %s", response_text)
                _LOGGER.warning("Research context was: %s", "Yes" if research_context else "No")
                if research_context:
                    _LOGGER.warning("Research context preview: %s", research_context[:500] + "...")
            
            # Update the section content with the written content
            updated_section = state.section.model_copy()
            updated_section.content = response_text
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
