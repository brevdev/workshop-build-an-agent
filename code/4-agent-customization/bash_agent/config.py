import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Config:
    """
    Configuration class for the Bash Computer Use Agent.
    
    Supports both:
    1. API-based inference (NVIDIA NIM endpoints)
    2. Local HuggingFace model inference (after customization training)
    """

    # -------------------------------------
    # API-based LLM configuration (for base agent)
    # -------------------------------------

    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    llm_model_name: str = "nvidia/nvidia-nemotron-nano-9b-v2"
    llm_api_key: str = field(default_factory=lambda: os.environ.get("NVIDIA_API_KEY", ""))
    
    # Sampling parameters (reduced temperature for deterministic outputs)
    llm_temperature: float = 0.1
    llm_top_p: float = 0.95

    # -------------------------------------
    # HuggingFace model configuration (for customized agent)
    # -------------------------------------
    
    # Path to the trained model checkpoint (from GRPO training)
    model_path: str = field(default_factory=lambda: os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "outputs/grpo_langgraph_cli/merged_model"
    ))
    
    # Maximum sequence length for generation
    max_seq_length: int = 2048
    max_new_tokens: int = 1024
    
    # Device configuration
    device: str = "cuda"  # or "cpu"
    
    # Whether to use API or local HuggingFace model
    use_api: bool = True  # Set to False after customization training
    api_base_url: str = "http://localhost:8000/v1"  # For vLLM or similar
    api_key: str = "not-needed-for-local"
    api_model_name: str = "local-model"

    # -------------------------------------
    # Agent configuration
    # -------------------------------------

    # The directory path that the agent can access and operate in
    root_dir: str = field(default_factory=lambda: os.path.dirname(os.path.abspath(__file__)))

    # The list of commands that the agent can execute.
    #
    # WARNING: Be very careful about which commands you allow here.
    #          By running this code you assume all responsibility for
    #          unintended consequences of command execution.
    #
    # NOTE: This is the BASE set of commands. After customization,
    #       you can add "langgraph" to enable LangGraph CLI commands.
    allowed_commands: List[str] = field(default_factory=lambda: [
        "cd", "cp", "ls", "cat", "find", "touch", "echo", "grep", "pwd",
        "mkdir", "wget", "sort", "head", "tail", "du", "wc", "file",
    ])

    @property
    def system_prompt(self) -> str:
        """Generate the system prompt for the LLM based on allowed commands."""
        return f"""/think

You are a helpful and very concise Bash assistant with the ability to execute commands in the shell.
You engage with users to help answer questions about bash commands, or execute their intent.
If user intent is unclear, keep engaging with them to figure out what they need and how to best help
them. If they ask questions that are not relevant to bash or computer use, decline to answer.

When a command is executed, you will be given the output from that command and any errors. Based on
that, either take further actions or yield control to the user.

The bash interpreter's output and current working directory will be given to you every time a
command is executed. Take that into account for the next conversation.
If there was an error during execution, tell the user what that error was exactly.

## Skills System

You have access to skills that provide structured workflows for complex tasks.
- Use `list_available_skills()` to see what skills are available
- Use `get_skill(name)` to load a skill before starting complex work
- Skills include: systematic-debugging, test-driven-development, brainstorming, writing-plans, executing-plans

When facing complex tasks like debugging issues, planning implementations, or writing tests,
ALWAYS load the relevant skill first and follow its instructions.

## Bash Commands

You are only allowed to execute the following commands. Break complex tasks into shorter commands from this list:

```
{self.allowed_commands}
```

**Never** attempt to execute a command not in this list. **Never** attempt to execute dangerous commands
like `rm`, `mv`, `rmdir`, `sudo`, etc. If the user asks you to do so, politely refuse.
"""

    @property
    def json_system_prompt(self) -> str:
        """The EXACT system prompt the model was trained with during GRPO.

        The customized model learned to emit structured LangGraph CLI JSON
        *conditioned on this specific prompt* (see 02_grpo_training.ipynb and the
        lesson in run_customized.md), so inference must use the same text. We
        return the single canonical copy in ``prompts.JSON_SYSTEM_PROMPT`` rather
        than duplicating it here, so the training prompt and the inference prompt
        cannot silently drift apart.
        """
        # config.py is imported both as a package (`from .config import Config`,
        # e.g. main_hf.py) and directly (`from config import Config` after adding
        # bash_agent/ to sys.path, e.g. 03_run_agent.ipynb). Support both.
        try:
            from .prompts import JSON_SYSTEM_PROMPT
        except ImportError:
            from prompts import JSON_SYSTEM_PROMPT
        return JSON_SYSTEM_PROMPT

    def enable_langgraph_cli(self):
        """Enable LangGraph CLI commands after customization training."""
        if "langgraph" not in self.allowed_commands:
            self.allowed_commands.append("langgraph")
