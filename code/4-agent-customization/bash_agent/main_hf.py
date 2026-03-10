#!/usr/bin/env python3
"""
Bash Computer Use Agent - HuggingFace Implementation

This is the entry point for running the customized bash agent with local
HuggingFace model inference. Uses the trained model checkpoint from
GRPO training (02_grpo_training.ipynb).

Usage:
    python -m bash_agent.main_hf
    python -m bash_agent.main_hf --model-path /path/to/model
    python -m bash_agent.main_hf --use-api  # Use OpenAI-compatible API instead
"""

import argparse
import json
import os
import sys

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .config import Config
from .bash import Bash
from .helpers import Messages, get_llm


def confirm_execution(cmd: str) -> bool:
    """Ask the user whether the suggested command should be executed."""
    response = input(f"    ▶️  Execute '{cmd}'? [y/N]: ").strip().lower()
    return response == "y" or response == "yes"


def main(config: Config):
    """Main agent loop for the customized model."""
    # Enable LangGraph CLI commands (the agent has been trained on these)
    config.enable_langgraph_cli()
    
    # Initialize the bash tool
    bash = Bash(config)

    # Initialize the LLM (HuggingFace or API based on config)
    llm = get_llm(config)

    # Initialize conversation with system prompt
    # Use json_system_prompt for the customized model
    messages = Messages(config.json_system_prompt)

    print("\n" + "=" * 60)
    print("Bash Computer Use Agent (Customized)")
    print("=" * 60)
    print(f"Model: {config.model_path}")
    print(f"Working directory: {bash.cwd}")
    print(f"Allowed commands: {config.allowed_commands}")
    print("Type 'quit' or 'exit' to stop.")
    print("Type 'clear' to reset conversation.")
    print("=" * 60 + "\n")

    # The main agent loop
    while True:
        # Get user message
        try:
            user = input(f"['{bash.cwd}'] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nShutting down. Bye!")
            break

        if user.lower() in ["quit", "exit"]:
            print("\nShutting down. Bye!")
            break
        
        if user.lower() == "clear":
            messages.clear()
            print("Conversation cleared.\n")
            continue

        if not user:
            continue

        # For the trained model, use clean prompts (no extra context)
        # The model was trained on simple natural language -> JSON
        messages.add_user_message(user)

        # The tool-call/response loop
        while True:
            print("\n[🤖] Thinking...")

            try:
                response, tool_calls = llm.query(messages, [bash.to_json_schema()])
            except Exception as e:
                print(f"Error querying model: {e}")
                break

            if response:
                response = response.strip()

                # Remove thinking tags if present (for models that use them)
                if "</think>" in response:
                    response = response.split("</think>")[-1].strip()

                # Add non-empty response to context
                if response:
                    messages.add_assistant_message(response)

            # Process tool calls
            if tool_calls:
                for tc in tool_calls:
                    # Handle different tool call formats
                    if hasattr(tc, "function"):
                        # OpenAI API format
                        function_name = tc.function.name
                        function_args = json.loads(tc.function.arguments)
                        tool_id = tc.id
                    else:
                        # Dict format from HuggingFace parser
                        function_name = tc["function"]["name"]
                        function_args = json.loads(tc["function"]["arguments"])
                        tool_id = tc["id"]

                    # Ensure it's calling the right tool
                    if function_name != "exec_bash_command" or "cmd" not in function_args:
                        tool_call_result = {"error": "Incorrect tool or function argument"}
                    else:
                        command = function_args["cmd"]
                        print(f"\nProposed command: {command}")

                        # Confirm execution with the user
                        if confirm_execution(command):
                            tool_call_result = bash.exec_bash_command(command)

                            # Display output
                            if tool_call_result.get("stdout"):
                                print(f"\nOutput:\n{tool_call_result['stdout']}")
                            if tool_call_result.get("stderr"):
                                print(f"\nError:\n{tool_call_result['stderr']}")
                            if tool_call_result.get("error"):
                                print(f"\nError:\n{tool_call_result['error']}")
                        else:
                            tool_call_result = {"error": "The user declined the execution of this command."}

                    messages.add_tool_message(json.dumps(tool_call_result), tool_id)
            else:
                # No tool calls - display the assistant's message to the user
                if response:
                    print(f"\n{response}")
                print("-" * 60 + "\n")
                break


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Bash Computer Use Agent with HuggingFace inference"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to the model checkpoint (default: outputs/grpo_langgraph_cli/merged_model)"
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Use OpenAI-compatible API instead of local inference"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/v1",
        help="API base URL when using --use-api"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature (default: 0.1)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="Device to run on (default: cuda)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Create configuration
    config = Config()
    
    # For HuggingFace inference, disable API mode
    config.use_api = False

    # Override with command line arguments
    if args.model_path:
        config.model_path = args.model_path
    if args.use_api:
        config.use_api = True
        config.api_base_url = args.api_url
    if args.temperature:
        config.llm_temperature = args.temperature
    if args.device:
        config.device = args.device

    # Run the agent
    main(config)
