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

BASE_URL = os.getenv("LANGGRAPH_API_URL", "http://127.0.0.1:2024")
CLIENT = get_sync_client(url=BASE_URL)
AVATARS = {"ai": "assistant", "user": "user", "tool": "🛠️"}
STREAMING = False  # Not all models support streaming with tool calling


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
    except httpx.ConnectError as e:
        st.markdown(
            """
            # Uh oh! 😱

            It looks like the LangGraph API server is not reachable. Please check if the server is running.
            """
        )
        e
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
        st.session_state.threads[ASSISTANT_ID] = CLIENT.threads.create()["thread_id"]
        st.session_state.history[ASSISTANT_ID] = []
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
    message_contents.markdown(msg["content"])


# Handle user input
if USER_INPUT:
    # Add user message to history and display
    st.session_state.history.setdefault(ASSISTANT_ID, []).append(
        {"role": "user", "content": USER_INPUT}
    )
    with CHAT.chat_message("user"):
        st.markdown(USER_INPUT)

    # Stream the response
    message_contents = None
    reasoning_contents = None
    reasoning_expanded_state_key = None
    stream_mode = ["updates", "messages"] if STREAMING else ["updates", "values"]
    for msg in CLIENT.runs.stream(
        thread_id=THREAD_ID,
        assistant_id=ASSISTANT_ID,
        input={"messages": [{"role": "user", "content": USER_INPUT}]},
        stream_mode=stream_mode,
    ):
        # Extract the event and data
        event = msg.event.split("/")
        if "metadata" in event:
            continue
        data = msg.data

        # Handle final model responses by emulating the streaming responses
        if event[0] == "values":
            # Ensure a message is present
            if not data.get("messages"):
                continue
            new_data = [data.get("messages")[-1]]

            # Skip user messages, they have already been displayed
            if new_data[0].get("type") == "human":
                continue

            # Post-process the content
            raw_content = new_data[0].get("content", "").split("</think>")
            new_data[0]["content"] = raw_content[-1].strip() or None
            if len(raw_content) > 1:
                new_data[0]["additional_kwargs"] = {"reasoning_content": raw_content[0].strip()}

            # Emulate streaming responses
            event[0] = "messages"
            data = new_data

        # Handle streaming message responses
        if event[0] == "messages":
            persona = data[0].get("type", "ai")
            graph_node_name = data[0].get("name", "")

            # Ensure message boxes exist
            if reasoning_contents is None or message_contents is None:
                reasoning_contents, message_contents = _create_message_box(
                    persona, graph_node_name
                )

            # Display model reasoning messages
            reasoning_content = (
                data[0].get("additional_kwargs", {}).get("reasoning_content", "")
            )
            if reasoning_content:
                reasoning_expander = reasoning_contents.expander(
                    "🧠 Reasoning",
                    expanded=True,
                )
                reasoning_expander.markdown(reasoning_content)

            # Display the model responses
            content = data[0].get("content", "")
            if content:
                message_contents.markdown(content)

        # Message is complete, update history and move to the next one
        elif event[0] == "updates":
            message_contents = None
            reasoning_contents = None

            # Add tool call messages to the chat history
            for tool_call in data.get("tools", {}).get("messages", []):
                tool_message = {
                    "role": "tool",
                    "content": tool_call["content"],
                    "name": tool_call["name"],
                }
                st.session_state.history[ASSISTANT_ID].append(tool_message)

            # Add agent messages to the chat history
            for agent_message in data.get("agent", {}).get("messages", []):
                agent_message = {
                    "role": "ai",
                    "content": agent_message["content"],
                    "name": agent_message["name"],
                    "think": agent_message.get("additional_kwargs", {}).get(
                        "reasoning_content", ""
                    ),
                }
                st.session_state.history[ASSISTANT_ID].append(agent_message)
