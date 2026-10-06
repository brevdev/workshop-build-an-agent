"""Give the general bash agent your fine-tuned LangGraph CLI model as a tool.

The hosted model plans and runs ordinary bash commands, exactly like the base
agent. For LangGraph CLI requests it calls `langgraph_cli`, which asks the
locally fine-tuned model for the exact command. A small specialist model behind
a tool adds depth without taking away the general agent's breadth.
"""

import json

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from .config import Config
from .helpers import Messages
from .main_langgraph import ExecOnConfirm
from .prompts import get_combined_system_prompt

ROUTING_INSTRUCTIONS = """
## The fine-tuned LangGraph CLI model

For every LangGraph CLI request (create a project, start the dev server, launch the server
in Docker, build an image, or write a Dockerfile), call `langgraph_cli` with the user's
request in their own words, then run the exact command it returns with `exec_bash_command`.
Do not write `langgraph` commands yourself.
"""


def make_langgraph_cli_tool(cli_llm, config: Config):
    """Wrap the fine-tuned model as a tool that returns, but does not run, a command."""

    @tool
    def langgraph_cli(request: str) -> str:
        """Translate a LangGraph CLI request into the exact `langgraph` command with the
        fine-tuned local model. Returns the command to run; it does not run it."""
        # The model only answers well with the exact prompt it was trained on.
        messages = Messages(config.json_system_prompt)
        messages.add_user_message(request)
        _, tool_calls = cli_llm.query(messages)
        if not tool_calls:
            return "The fine-tuned model did not produce a valid LangGraph CLI command for this request."
        call = tool_calls[0]
        arguments = call["function"]["arguments"] if isinstance(call, dict) else call.function.arguments
        command = json.loads(arguments)["cmd"]
        # This tool only ever proposes LangGraph CLI commands.
        if not command.startswith("langgraph "):
            return "The fine-tuned model did not produce a valid LangGraph CLI command for this request."
        return command

    return langgraph_cli


def build_combined_agent(config: Config, cli_llm, bash):
    """Create the hosted ReAct agent with confirmed bash execution and the CLI specialist."""
    config.enable_langgraph_cli()
    llm = ChatOpenAI(
        model=config.llm_model_name,
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        temperature=config.llm_temperature,
        top_p=config.llm_top_p,
    )
    return create_react_agent(
        model=llm,
        tools=[ExecOnConfirm(bash).exec_bash_command, make_langgraph_cli_tool(cli_llm, config)],
        prompt=get_combined_system_prompt(config.allowed_commands) + ROUTING_INSTRUCTIONS,
        checkpointer=InMemorySaver(),
    )


def run_agent_loop(agent, bash, thread_id: str = "combined"):
    """Chat with the agent until the user types quit or exit."""
    print("[INFO] Type 'quit' or 'exit' to stop.\n")
    conversation = 0
    while True:
        try:
            user = input(f"['{bash.cwd}' 🙂] ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[🤖] Shutting down. Bye!\n")
            break
        if user.lower() in ("quit", "exit"):
            print("\n[🤖] Shutting down. Bye!\n")
            break
        if not user:
            continue
        print("\n[🤖] Thinking...")
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": f"{user}\n Current working directory: `{bash.cwd}`"}]},
                config={"configurable": {"thread_id": f"{thread_id}-{conversation}"}},
            )
        except (Exception, KeyboardInterrupt) as error:
            # A failed turn can leave an unanswered tool call that breaks the thread.
            conversation += 1
            print(f"\n[🤖] That request failed ({type(error).__name__}). Starting a new conversation; "
                  "ask again.\n")
            continue
        response = result["messages"][-1].content.strip()
        if "</think>" in response:
            response = response.split("</think>")[-1].strip()
        if response:
            print(f"\n[🤖] {response}")
        print("-" * 60 + "\n")
