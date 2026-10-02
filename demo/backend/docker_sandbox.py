"""Docker backend for the workshop: no host mounts or container network.

File arguments travel as JSON data, never interpolated into shell source.
Only the explicitly selected execute tool accepts shell commands.
"""
import asyncio
import base64
import json
import os

import docker
from deepagents.backends.protocol import (
    SandboxBackendProtocol, ExecuteResponse, EditResult, WriteResult,
    FileDownloadResponse, FileUploadResponse,
)

DOCKER_IMAGE = "python:3.11-slim"
WORKSPACE_IN_CONTAINER = "/workspace"


def _default_docker_host():
    if os.getenv("DOCKER_HOST"):
        return os.environ["DOCKER_HOST"]
    for path in ("/var/host-run/docker.sock", "/var/run/docker.sock"):
        if os.path.exists(path):
            return "unix://" + path
    return "unix:///var/run/docker.sock"


# Runs inside the container. Keeping paths/content in argv avoids heredoc,
# quote, command-substitution, newline and binary-content injection.
_FILE_RPC = r'''
import base64, glob, json, os, pathlib, sys
args = json.loads(sys.argv[1]); root = pathlib.Path('/workspace').resolve()
def path(value):
    value = value or '/workspace'
    if value in ('.', '/'): value = '/workspace'
    p = pathlib.Path(value)
    if '..' in p.parts: raise PermissionError('Parent traversal is not allowed')
    p = (p if p.is_absolute() else root / p).resolve()
    if not p.is_relative_to(root): raise PermissionError('Path is outside /workspace')
    return p

def info(p):
    p = path(str(p))
    return {'path': str(p), 'is_dir': p.is_dir(), 'size': p.stat().st_size}

def read(p):
    if p.stat().st_size > 65536: raise ValueError('File exceeds the 64 KiB lab limit')
    return p.read_bytes()
try:
    p = path(args.get('path')); op = args['op']
    if op == 'ls': result = [info(x) for x in sorted(p.iterdir()) if not x.is_symlink()][:1000]
    elif op == 'read':
        lines = read(p).decode('utf-8').splitlines(keepends=True)
        start = args.get('offset',0); limit = args.get('limit',2000)
        if start < 0 or limit < 0: raise ValueError('offset and limit must be nonnegative')
        result = ''.join(lines[start:start+limit])
    elif op in ('write', 'upload'):
        data = base64.b64decode(args['data'], validate=True)
        if len(data) > 65536: raise ValueError('File exceeds the 64 KiB lab limit')
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb' if op == 'write' else 'wb') as f: f.write(data)
        result = str(p)
    elif op == 'edit':
        current = read(p).decode('utf-8'); old = args['old']; new = args['new']
        if not old: raise ValueError('old_string must not be empty')
        count = current.count(old)
        if not count: raise ValueError('String not found')
        if count > 1 and not args['all']: raise ValueError('Multiple matches; use replace_all or a unique string')
        data = current.replace(old, new, -1 if args['all'] else 1).encode('utf-8')
        if len(data) > 65536: raise ValueError('File exceeds the 64 KiB lab limit')
        p.write_bytes(data); result = count if args['all'] else 1
    elif op == 'glob':
        pattern = args['pattern']
        if pathlib.Path(pattern).is_absolute() or '..' in pathlib.Path(pattern).parts:
            raise PermissionError('Use a relative glob pattern within the workspace')
        result = [info(x) for x in sorted(p.glob(pattern)) if not x.is_symlink()][:1000]
    elif op == 'grep':
        result = []
        files = [p] if p.is_file() else sorted(p.rglob(args.get('glob') or '*'))
        for f in files:
            if not f.is_file() or f.is_symlink(): continue
            f = path(str(f))
            for n, line in enumerate(read(f).decode('utf-8',errors='replace').splitlines(),1):
                if args['pattern'] in line: result.append({'path':str(f),'line':n,'text':line})
                if len(result) >= 1000: break
            if len(result) >= 1000: break
    elif op == 'download': result = base64.b64encode(read(p)).decode('ascii')
    else: raise ValueError('Unknown file operation')
    print(json.dumps({'result': result}))
except Exception as e:
    print(json.dumps({'error': str(e), 'kind': type(e).__name__}))
'''

_EXEC_RPC = r'''
import json, os, selectors, signal, subprocess, sys, time
p = subprocess.Popen(['bash','-c',sys.argv[1]],cwd='/workspace',stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,start_new_session=True)
s = selectors.DefaultSelector(); s.register(p.stdout,selectors.EVENT_READ)
output = bytearray(); truncated = False; deadline = time.monotonic()+60; timed_out = False
while s.get_map():
    if time.monotonic() > deadline:
        os.killpg(p.pid,signal.SIGKILL); timed_out = True
    for key,_ in s.select(.1):
        chunk = os.read(key.fd,8192)
        if not chunk: s.unregister(key.fileobj); continue
        remaining = max(0,50000-len(output))
        output.extend(chunk[:remaining]); truncated |= len(chunk)>remaining
    if timed_out: break
p.wait()
text = output.decode('utf-8',errors='replace')
if timed_out: text += '\nCommand stopped after 60 seconds.'
if truncated: text += '\n... (truncated)'
print(json.dumps({'output':text,'exit_code':124 if timed_out else p.returncode,'truncated':truncated}))
'''


class DockerSandboxBackend(SandboxBackendProtocol):
    """Disposable nonroot container; this is not a separate-kernel VM."""

    def __init__(self, docker_host=None):
        self._container = None
        self._client = docker.DockerClient(base_url=docker_host or _default_docker_host(), timeout=75)
        try:
            self._container = self._client.containers.run(
                DOCKER_IMAGE, command="sleep infinity", detach=True,
                working_dir=WORKSPACE_IN_CONTAINER, user="65534:65534",
                network_mode="none", read_only=True, cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"], pids_limit=64,
                tmpfs={"/workspace": "rw,nosuid,size=64m,mode=1777", "/tmp": "rw,nosuid,size=32m,mode=1777"},
                environment={"PYTHONDONTWRITEBYTECODE": "1"},
                mem_limit="512m", nano_cpus=1_000_000_000,
                labels={"build-an-agent": "sandbox"},
            )
            self._call("ls", path="/workspace")
        except Exception:
            self.delete()
            raise

    def _run(self, code, argument):
        result = self._container.exec_run(["python", "-c", code, argument], demux=True)
        stdout, stderr = result.output
        if result.exit_code:
            raise RuntimeError((stderr or stdout or b"Container operation failed").decode(errors="replace")[:1000])
        return json.loads(stdout)

    def _call(self, op, **kwargs):
        result = self._run(_FILE_RPC, json.dumps({"op": op, **kwargs}))
        if "error" in result:
            raise ValueError(result["error"])
        return result["result"]

    def execute(self, command):
        return ExecuteResponse(**self._run(_EXEC_RPC, command))

    async def aexecute(self, command):
        return await asyncio.to_thread(self.execute, command)

    def ls_info(self, path):
        return self._call("ls", path=path)

    def read(self, file_path, offset=0, limit=2000):
        try:
            return self._call("read", path=file_path, offset=offset, limit=limit)
        except ValueError as e:
            return f"Error: {e}"

    def write(self, file_path, content):
        try:
            path = self._call("write", path=file_path, data=base64.b64encode(content.encode()).decode())
            return WriteResult(path=path)
        except ValueError as e:
            return WriteResult(error=str(e))

    def edit(self, file_path, old_string, new_string, replace_all=False):
        try:
            count = self._call("edit", path=file_path, old=old_string, new=new_string, all=replace_all)
            return EditResult(path=file_path, occurrences=count)
        except ValueError as e:
            return EditResult(error=str(e))

    def glob_info(self, pattern, path="/"):
        return self._call("glob", path=path, pattern=pattern)

    def grep_raw(self, pattern, path=None, glob=None):
        return self._call("grep", path=path, pattern=pattern, glob=glob)

    def upload_files(self, files):
        results = []
        for path, content in files:
            try:
                self._call("upload", path=path, data=base64.b64encode(content).decode())
                results.append(FileUploadResponse(path=path))
            except ValueError:
                results.append(FileUploadResponse(path=path, error="invalid_path"))
        return results

    def download_files(self, paths):
        results = []
        for path in paths:
            try:
                data = base64.b64decode(self._call("download", path=path))
                results.append(FileDownloadResponse(path=path, content=data))
            except ValueError:
                results.append(FileDownloadResponse(path=path, error="invalid_path"))
        return results

    @property
    def id(self):
        return self._container.id

    @property
    def container_id(self):
        return self._container.short_id

    def delete(self):
        if self._container is not None:
            try:
                self._container.remove(force=True)
            finally:
                self._container = None
        self._client.close()
