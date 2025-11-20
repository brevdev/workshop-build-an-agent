"""Main entry point for the report generation workflow."""

import asyncio
from typing import Any

from .agent import AgentState, graph


async def async_write_report(
    topic: str, report_structure: str
) -> Any | dict[str, Any] | None:
    """Write a report."""
    state = AgentState(topic=topic, report_structure=report_structure)
    result = await graph.ainvoke(state)
    return result


def write_report(topic: str, report_structure: str) -> Any | dict[str, Any] | None:
    """Write a report."""
    return asyncio.run(async_write_report(topic, report_structure))
