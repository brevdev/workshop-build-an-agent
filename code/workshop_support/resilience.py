"""Keep a transient network failure from ending an agent run.

Hosted model, retrieval and search calls occasionally fail for reasons that a
retry fixes, such as a DNS hiccup, a reset connection or a rate limit. A tool
that raises ends the whole agent run, and the unanswered tool call it leaves in
the conversation makes every later turn in that thread fail too.
"""

import asyncio
import functools
import re
import time

from langchain_core.tools import ToolException

ATTEMPTS = 3
# Failures a retry can fix: lost connections, DNS, timeouts, rate limits, server errors.
TRANSIENT_NAMES = {"ConnectionError", "ConnectError", "ConnectTimeout", "ReadTimeout", "Timeout", "TimeoutError",
                   "ReadError", "RemoteProtocolError", "ServerDisconnectedError", "ClientConnectorError",
                   "ClientConnectorDNSError", "ClientOSError", "APIConnectionError", "APITimeoutError",
                   "RateLimitError", "InternalServerError", "gaierror"}
TRANSIENT_TEXT = re.compile(r"\b(?:429|500|502|503|504)\b|name resolution|Name or service not known|"
                            r"Connection (?:reset|refused|aborted)|timed out", re.IGNORECASE)


def is_transient(error: BaseException) -> bool:
    """True for failures that a retry can fix; False for bad keys, bad requests and code errors."""
    names = {cls.__name__ for cls in type(error).__mro__}
    return bool(names & TRANSIENT_NAMES) or bool(TRANSIENT_TEXT.search(str(error)))


def retry(call, attempts: int = ATTEMPTS, delay: float = 2.0):
    """Return ``call()``, retrying a transient failure with backoff; re-raise anything else."""
    for attempt in range(attempts):
        try:
            return call()
        except Exception as error:
            if attempt == attempts - 1 or not is_transient(error):
                raise
            time.sleep(delay * 2 ** attempt)


async def aretry(call, attempts: int = ATTEMPTS, delay: float = 2.0):
    """Async version of :func:`retry`; ``call`` returns an awaitable."""
    for attempt in range(attempts):
        try:
            return await call()
        except Exception as error:
            if attempt == attempts - 1 or not is_transient(error):
                raise
            await asyncio.sleep(delay * 2 ** attempt)


def resilient_tool(tool, attempts: int = ATTEMPTS):
    """Return a copy of ``tool`` that retries transient failures, then reports the error to the agent.

    The final error becomes a tool message with status "error", so the agent can
    tell the user or try another tool, the conversation stays usable, and
    evaluations can tell a failed lookup from an answer.
    """

    def failure(error):
        if is_transient(error):
            reason = f"failed after {attempts} attempts ({type(error).__name__}), usually a temporary network or service problem"
        else:
            reason = f"failed ({type(error).__name__}: {str(error)[:200]})"
        raise ToolException(f"Tool {tool.name} {reason}. Tell the user the lookup failed and do not guess "
                            "its result.") from error

    update = {}
    if tool.func is not None:
        func = tool.func

        # functools.wraps keeps the signature LangChain inspects for callbacks.
        @functools.wraps(func)
        def run(*args, **kwargs):
            try:
                return retry(lambda: func(*args, **kwargs), attempts)
            except Exception as error:
                failure(error)

        update["func"] = run
    if tool.coroutine is not None:
        coroutine = tool.coroutine

        @functools.wraps(coroutine)
        async def arun(*args, **kwargs):
            try:
                return await aretry(lambda: coroutine(*args, **kwargs), attempts)
            except Exception as error:
                failure(error)

        update["coroutine"] = arun
    update["handle_tool_error"] = True  # turn the final ToolException into a tool message
    return tool.model_copy(update=update)
