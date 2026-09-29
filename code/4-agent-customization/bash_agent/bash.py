from pathlib import Path
from typing import Any, Dict
import shlex
import subprocess

from .config import Config


class Bash:
    """Run one approved command at a time as the current OS user.

    The command allowlist is a teaching guard, not a filesystem sandbox.
    """
    def __init__(self, config: Config):
        self.config = config
        self.cwd = str(Path(config.root_dir).resolve())

    def exec_bash_command(self, cmd: str) -> Dict[str, Any]:
        if not cmd or not cmd.strip():
            return {"error": "No command was provided"}
        if "\n" in cmd or "\r" in cmd:
            return {"error": "Run one command at a time."}
        try:
            args = shlex.split(cmd)
        except ValueError as exc:
            return {"error": str(exc)}
        if not args or args[0] not in self.config.allowed_commands:
            return {"error": "This command is not in the allowlist."}
        if any(token in {";", "&&", "||", "|", "&", ">", ">>", "<"} for token in args):
            return {"error": "Shell operators are not supported. Run separate commands."}
        if args[0] == "find" and any(arg in {"-exec", "-execdir", "-ok", "-okdir", "-delete"} for arg in args[1:]):
            return {"error": "This find action is not allowed."}
        try:
            if args[0] == "cd":
                if len(args) != 2:
                    return {"error": "Use cd with one directory path."}
                path = Path(args[1]).expanduser()
                path = (Path(self.cwd) / path).resolve()
                if not path.is_dir():
                    return {"error": "Directory not found."}
                self.cwd = str(path)
                return {"stdout": "", "stderr": "", "cwd": self.cwd}
            # No shell parser: newlines, substitutions and redirections cannot
            # smuggle a second command past the name check.
            result = subprocess.run(args, cwd=self.cwd, capture_output=True,
                                    text=True, timeout=60, shell=False)
            return {"stdout": result.stdout, "stderr": result.stderr,
                    "cwd": self.cwd, "returncode": result.returncode}
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"error": str(exc), "cwd": self.cwd}

    def to_json_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "exec_bash_command",
                "description": "Execute one allowed command (no shell operators) and return stdout, stderr and working directory",
                "parameters": {
                    "type": "object",
                    "properties": {"cmd": {"type": "string", "description": "One command to execute"}},
                    "required": ["cmd"],
                },
            },
        }
