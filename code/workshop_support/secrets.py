"""Save widget-managed keys without overwriting other workshop settings."""

import os
from pathlib import Path
import tempfile

from dotenv import set_key


def save_secrets(values: dict[str, str], path: str | Path) -> None:
    path = Path(path)
    updates = {key: value.strip() for key, value in values.items()}
    if "NVIDIA_API_KEY" in updates:
        for alias in ("NGC_API_KEY", "NGC_CLI_API_KEY", "NVIDIA_NIM_API_KEY"):
            updates[alias] = updates["NVIDIA_API_KEY"]
    # Replace the file only after every update succeeds. Blank entries clear keys
    # and override stale values when another notebook reloads the file.
    fd, temporary = tempfile.mkstemp(prefix=".secrets-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as target:
            target.write(path.read_text() if path.exists() else "")
        for key, value in updates.items():
            set_key(temporary, key, value, quote_mode="always")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    for key, value in updates.items():
        if value:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)
