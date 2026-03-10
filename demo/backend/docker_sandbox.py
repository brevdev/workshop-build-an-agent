"""
Docker-based sandbox backend for deepagents.

Implements the SandboxBackendProtocol by routing all file I/O and shell
execution through an isolated Docker container.  When sandbox mode is ON
the agent literally cannot see or touch the host filesystem.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass

import docker

from deepagents.backends.protocol import (
    BackendProtocol,
    SandboxBackendProtocol,
    ExecuteResponse,
    EditResult,
    WriteResult,
    FileInfo,
)


DOCKER_IMAGE = "python:3.11-slim"
WORKSPACE_IN_CONTAINER = "/workspace"


class DockerSandboxBackend(SandboxBackendProtocol):
    """
    A deepagents-compatible backend that runs *everything* inside a Docker
    container.  The host filesystem is completely invisible to the agent.
    """

    def __init__(self, docker_host: str | None = None):
        socket = docker_host or os.getenv(
            "DOCKER_HOST",
            f"unix://{os.path.expanduser('~')}/.colima/default/docker.sock",
        )
        self._client = docker.DockerClient(base_url=socket)
        self._container = self._client.containers.run(
            DOCKER_IMAGE,
            command="sleep infinity",
            detach=True,
            working_dir=WORKSPACE_IN_CONTAINER,
            # No host mounts — fully isolated
            mem_limit="512m",
            nano_cpus=1_000_000_000,  # 1 CPU
            labels={"gtc-demo": "sandbox"},
        )
        # Pre-create workspace dir inside the container
        self._exec("mkdir -p /workspace")
        print(f"[DockerSandbox] Container {self._container.short_id} started ({DOCKER_IMAGE})")

    # ── internal helpers ──────────────────────────────────────────────────

    def _exec(self, cmd: str, workdir: str | None = None) -> tuple[int, str]:
        """Run a command inside the container and return (exit_code, output)."""
        wd = workdir or WORKSPACE_IN_CONTAINER
        result = self._container.exec_run(
            ["bash", "-c", cmd],
            workdir=wd,
            demux=True,
        )
        stdout = (result.output[0] or b"").decode("utf-8", errors="replace") if result.output else ""
        stderr = (result.output[1] or b"").decode("utf-8", errors="replace") if result.output else ""
        combined = stdout
        if stderr:
            combined = f"{stdout}\n{stderr}" if stdout else stderr
        return result.exit_code, combined.strip()

    def _resolve(self, path: str) -> str:
        """Ensure paths are absolute inside the container workspace."""
        if not path or path == ".":
            return WORKSPACE_IN_CONTAINER
        if path.startswith("/workspace"):
            return path
        if path.startswith("/"):
            return path  # Absolute container path
        return f"{WORKSPACE_IN_CONTAINER}/{path}"

    # ── SandboxBackendProtocol: execute ───────────────────────────────────

    def execute(self, command: str) -> ExecuteResponse:
        exit_code, output = self._exec(command)
        truncated = len(output) > 50000
        if truncated:
            output = output[:50000] + "\n... (truncated)"
        return ExecuteResponse(output=output, exit_code=exit_code, truncated=truncated)

    async def aexecute(self, command: str) -> ExecuteResponse:
        return await asyncio.to_thread(self.execute, command)

    # ── BackendProtocol: ls ───────────────────────────────────────────────

    def ls_info(self, path: str) -> list[FileInfo]:
        resolved = self._resolve(path)
        # Use stat to get proper file info
        code, output = self._exec(
            f'find "{resolved}" -maxdepth 1 -printf "%p\\t%s\\t%T@\\t%y\\n" 2>/dev/null || '
            f'ls -la "{resolved}" 2>&1'
        )
        if code != 0:
            return []

        results: list[FileInfo] = []
        for line in output.strip().split("\n"):
            if not line or line.startswith("total"):
                continue
            parts = line.split("\t")
            if len(parts) >= 4:
                fpath, size_str, mtime_str, ftype = parts[0], parts[1], parts[2], parts[3]
                if fpath == resolved:
                    continue  # skip the directory itself
                name = os.path.basename(fpath)
                if not name:
                    continue
                results.append(FileInfo(
                    path=fpath,
                    is_dir=(ftype == "d"),
                    size=int(size_str) if size_str.isdigit() else 0,
                ))
            else:
                # Fallback: just return file names
                results.append(FileInfo(path=line.strip()))
        return results

    async def als_info(self, path: str) -> list[FileInfo]:
        return await asyncio.to_thread(self.ls_info, path)

    # ── BackendProtocol: read ─────────────────────────────────────────────

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        resolved = self._resolve(file_path)
        if offset > 0 or limit < 2000:
            start = offset + 1
            end = offset + limit
            code, output = self._exec(f'sed -n "{start},{end}p" "{resolved}"')
        else:
            code, output = self._exec(f'cat "{resolved}"')
        if code != 0:
            return f"Error reading file: {output}"
        return output

    async def aread(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        return await asyncio.to_thread(self.read, file_path, offset, limit)

    # ── BackendProtocol: write ────────────────────────────────────────────

    def write(self, file_path: str, content: str) -> WriteResult:
        resolved = self._resolve(file_path)
        # Ensure parent directory exists
        parent = os.path.dirname(resolved)
        self._exec(f'mkdir -p "{parent}"')

        # Use heredoc to write content (handles special chars)
        escaped = content.replace("\\", "\\\\").replace("'", "'\"'\"'")
        code, output = self._exec(f"cat > \"{resolved}\" << 'DEEPAGENT_EOF'\n{content}\nDEEPAGENT_EOF")
        if code != 0:
            return WriteResult(error=f"Write failed: {output}", path=None, files_update=None)
        return WriteResult(error=None, path=resolved, files_update={resolved: {"status": "created"}})

    async def awrite(self, file_path: str, content: str) -> WriteResult:
        return await asyncio.to_thread(self.write, file_path, content)

    # ── BackendProtocol: edit ─────────────────────────────────────────────

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        resolved = self._resolve(file_path)
        # Read current content
        code, current = self._exec(f'cat "{resolved}"')
        if code != 0:
            return EditResult(error=f"File not found: {resolved}", path=None, files_update=None, occurrences=0)

        count = current.count(old_string)
        if count == 0:
            return EditResult(error=f"String not found in {resolved}", path=resolved, files_update=None, occurrences=0)

        if replace_all:
            new_content = current.replace(old_string, new_string)
        else:
            new_content = current.replace(old_string, new_string, 1)

        # Write back
        write_result = self.write(file_path, new_content)
        if write_result.error:
            return EditResult(error=write_result.error, path=resolved, files_update=None, occurrences=0)

        return EditResult(
            error=None,
            path=resolved,
            files_update={resolved: {"status": "edited"}},
            occurrences=count if replace_all else 1,
        )

    async def aedit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        return await asyncio.to_thread(self.edit, file_path, old_string, new_string, replace_all)

    # ── BackendProtocol: glob ─────────────────────────────────────────────

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        resolved = self._resolve(path)
        code, output = self._exec(f'find "{resolved}" -name "{pattern}" -printf "%p\\t%s\\t%y\\n" 2>/dev/null')
        if code != 0 or not output:
            return []

        results: list[FileInfo] = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                results.append(FileInfo(
                    path=parts[0],
                    is_dir=(parts[2] == "d"),
                    size=int(parts[1]) if parts[1].isdigit() else 0,
                ))
        return results

    async def aglob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        return await asyncio.to_thread(self.glob_info, pattern, path)

    # ── BackendProtocol: grep ─────────────────────────────────────────────

    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list:
        search_path = self._resolve(path) if path else WORKSPACE_IN_CONTAINER
        cmd = f'grep -rn "{pattern}" "{search_path}"'
        if glob:
            cmd += f' --include="{glob}"'
        code, output = self._exec(cmd)
        if not output:
            return []
        # Return raw grep output as list of GrepMatch-like dicts
        results = []
        for line in output.strip().split("\n"):
            if ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    results.append({
                        "path": parts[0],
                        "line_number": int(parts[1]) if parts[1].isdigit() else 0,
                        "content": parts[2],
                    })
        return results

    async def agrep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list:
        return await asyncio.to_thread(self.grep_raw, pattern, path, glob)

    # ── BackendProtocol: upload / download (stubs for demo) ───────────────

    def upload_files(self, files):
        return []

    async def aupload_files(self, files):
        return []

    def download_files(self, paths):
        return []

    async def adownload_files(self, paths):
        return []

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def delete(self):
        """Stop and remove the Docker container."""
        try:
            self._container.stop(timeout=5)
            self._container.remove(force=True)
            print(f"[DockerSandbox] Container {self._container.short_id} destroyed")
        except Exception as e:
            print(f"[DockerSandbox] Cleanup error: {e}")

    @property
    def container_id(self) -> str:
        return self._container.short_id

    def __repr__(self):
        return f"<DockerSandboxBackend container={self._container.short_id}>"
