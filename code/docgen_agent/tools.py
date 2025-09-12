"""Tools for the report generation workflow."""

import asyncio
import logging
import os
from typing import Literal

from langchain_core.tools import tool
from tavily import AsyncTavilyClient

_LOGGER = logging.getLogger(__name__)

tavily_client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
INCLUDE_RAW_CONTENT = False
MAX_TOKENS_PER_SOURCE = 1000
MAX_RESULTS = 2
SEARCH_DAYS = 30


def _deduplicate_and_format_sources(
    search_response, max_tokens_per_source, include_raw_content=True
):
    """
    Takes either a single search response or list of responses from Tavily API and formats them.
    Limits the raw_content to approximately max_tokens_per_source.
    include_raw_content specifies whether to include the raw_content from Tavily in the formatted string.

    Args:
        search_response: Either:
            - A dict with a 'results' key containing a list of search results
            - A list of dicts, each containing search results

    Returns:
        str: Formatted string with deduplicated sources
    """
    # Convert input to list of results
    if isinstance(search_response, dict):
        sources_list = search_response["results"]
    elif isinstance(search_response, list):
        sources_list = []
        for response in search_response:
            if isinstance(response, dict) and "results" in response:
                sources_list.extend(response["results"])
            else:
                sources_list.extend(response)
    else:
        raise ValueError(
            "Input must be either a dict with 'results' or a list of search results"
        )

    # Deduplicate by URL
    unique_sources = {}
    for source in sources_list:
        if source["url"] not in unique_sources:
            unique_sources[source["url"]] = source

    # Format output
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"Source {source['title']}:\n===\n"
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += (
            f"Most relevant content from source: {source['content']}\n===\n"
        )
        if include_raw_content:
            # Using rough estimate of 4 characters per token
            char_limit = max_tokens_per_source * 4
            # Handle None raw_content
            raw_content = source.get("raw_content", "")
            if raw_content is None:
                raw_content = ""
                print(f"Warning: No raw_content found for source {source['url']}")
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"

    return formatted_text.strip()


@tool(parse_docstring=True)
async def search_tavily(
    queries: list[str],
    topic: Literal["general", "news", "finance"] = "news",
) -> str:
    """Search the web using the Tavily API.

    Args:
        queries: List of queries to search.
        topic: The topic of the provided queries.
          general - General search.
          news - News search.
          finance - Finance search.

    Returns:
        A string of the search results.
    """
    _LOGGER.info("Searching the web using the Tavily API")

    days = None
    if topic == "news":
        days = SEARCH_DAYS

    search_jobs = []
    for query in queries:
        _LOGGER.info("Searching for query: %s", query)
        search_jobs.append(
            asyncio.create_task(
                tavily_client.search(
                    query,
                    max_results=MAX_RESULTS,
                    include_raw_content=INCLUDE_RAW_CONTENT,
                    topic=topic,
                    days=days,  # type: ignore[arg-type]
                )
            )
        )

    search_docs = await asyncio.gather(*search_jobs)

    formatted_search_docs = _deduplicate_and_format_sources(
        search_docs,
        max_tokens_per_source=MAX_TOKENS_PER_SOURCE,
        include_raw_content=INCLUDE_RAW_CONTENT,
    )
    _LOGGER.debug("Search results: %s", formatted_search_docs)
    return formatted_search_docs
