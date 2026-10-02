"""
Simple LangGraph Client - A Streamlit interface for LangGraph assistants.

This application provides a clean web interface for interacting with LangGraph
assistants, featuring streaming responses, reasoning tags, and debug information.
"""

import os
import time
from typing import Any, Dict, List

import httpx
import streamlit as st
import streamlit.components.v1 as components
from langgraph_sdk import get_sync_client
from client_messages import normalize_message, stream_error

BASE_URL = os.getenv("LANGGRAPH_API_URL", "http://127.0.0.1:2024")
CLIENT = get_sync_client(url=BASE_URL)
AVATARS = {"ai": "assistant", "user": "user", "tool": "🛠️"}



# Configure Streamlit page
st.set_page_config(page_title="Simple Client", layout="wide", page_icon="🤖")
if "threads" not in st.session_state:
    st.session_state.threads: Dict[str, str] = {}
if "history" not in st.session_state:
    st.session_state.history: Dict[str, List[Dict[str, str]]] = {}


# Define a helper function to list assistants
@st.cache_data(show_spinner=False, ttl=90)
def list_assistants() -> List[Dict[str, Any]]:
    """Fetch available assistants from the server."""
    try:
        return CLIENT.assistants.search(limit=50)
    except httpx.HTTPError:
        st.error("The LangGraph API is unavailable. Start the agent server or check Workshop Health, then reload this page.")
        st.stop()


# Load the list of assistants hosted on the LangGraph API server
ALL_ASSISTANTS = list_assistants()
if not ALL_ASSISTANTS:
    st.warning("No assistants found on the server. Create one first.")
    st.stop()


# Create the sidebar
with st.sidebar:
    # Select Assistant
    ASSISTANT = st.selectbox(
        "Select Assistant",
        ALL_ASSISTANTS,
        format_func=lambda a: a.get("name") or a["assistant_id"],
    )
    ASSISTANT_ID = ASSISTANT["assistant_id"]

    # Conversation management
    if st.sidebar.button("New conversation", use_container_width=True):
        st.session_state.threads[ASSISTANT_ID] = None
        st.session_state.history[ASSISTANT_ID] = None

    # Ensure a conversation exists
    if (
        ASSISTANT_ID not in st.session_state.threads
        or st.session_state.threads[ASSISTANT_ID] is None
    ):
        try:
            st.session_state.threads[ASSISTANT_ID] = CLIENT.threads.create()["thread_id"]
            st.session_state.history[ASSISTANT_ID] = []
        except httpx.HTTPError:
            st.error("Could not create a conversation. Check the agent server and reload this page.")
            st.stop()
    THREAD_ID = st.session_state.threads[ASSISTANT_ID]
    st.markdown(f"**Current Thread ID: `{THREAD_ID[:8]}...`**")


# Create a container for running JavaScript code
JS_CONTAINER = st.container(height=1, border=False)


# Helper functions for creating UI elements
def _create_message_box(persona, tool_name):
    """Create an empty message box with placeholder for reasoning and message contents."""
    # Close all reasoning expanders (technically, this closes all expanders on the page)
    with JS_CONTAINER:
        components.html(
            """
            <script>
            parent.document.querySelectorAll('details[open]').forEach(details => {
                details.removeAttribute('open');
            });
            </script>
            """,
            height=1,
        )
        time.sleep(0.1)

    # Create new message box
    message_box = CHAT.chat_message(AVATARS.get(persona, "🤖"))

    # Add some extra decorations for tool calls
    if persona == "tool":
        message_box = message_box.expander(f"Using {tool_name}...", expanded=False)

    # Create placeholders for reasoning and message contents
    return message_box.empty(), message_box.empty()


# Create the chat interface and recall history
CHAT = st.container()
USER_INPUT = st.chat_input("🪵 Say anything")
for msg in st.session_state.history.get(ASSISTANT_ID, []):
    reasoning_contents, message_contents = _create_message_box(
        msg["role"], msg.get("name")
    )
    if "think" in msg:
        reasoning_expander = reasoning_contents.expander("🧠 Reasoning", expanded=False)
        reasoning_expander.markdown(msg["think"])
    if msg["role"] == "error":
        message_contents.error(msg["content"])
    else:
        message_contents.markdown(msg["content"])


# Handle user input
if USER_INPUT:
    # Add user message to history and display
    st.session_state.history.setdefault(ASSISTANT_ID, []).append(
        {"role": "user", "content": USER_INPUT}
    )
    with CHAT.chat_message("user"):
        st.markdown(USER_INPUT)

    # State snapshots include full history. Message IDs prevent duplicate turns.
    history = st.session_state.history[ASSISTANT_ID]
    seen = {message.get("id") for message in history if message.get("id")}
    try:
        for event in CLIENT.runs.stream(
            thread_id=THREAD_ID,
            assistant_id=ASSISTANT_ID,
            input={"messages": [{"role": "user", "content": USER_INPUT}]},
            stream_mode=["values"],
        ):
            event_type = event.event.split("/")[0]
            if event_type == "error":
                error = {"role": "error", "content": stream_error(event.data)}
                history.append(error)
                st.error(error["content"])
                break
            if event_type != "values" or not isinstance(event.data, dict):
                continue
            for raw_message in event.data.get("messages", []):
                message = normalize_message(raw_message)
                if message is None or message["id"] in seen:
                    continue
                seen.add(message["id"])
                history.append(message)
                reasoning_contents, message_contents = _create_message_box(message["role"], message["name"])
                if message["think"]:
                    reasoning_contents.expander("🧠 Reasoning", expanded=False).markdown(message["think"])
                message_contents.markdown(message["content"])
    except Exception as exc:
        error = {"role": "error", "content": stream_error({"error": type(exc).__name__, "message": str(exc)})}
        history.append(error)
        st.error(error["content"])
