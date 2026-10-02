"""Provided enforcement helpers; the exercises assemble the agent around them."""
from deepagents.backends.protocol import BackendProtocol, SandboxBackendProtocol
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage

FILE_TOOLS = {"ls", "read_file", "write_file", "edit_file", "glob", "grep"}


def enabled_tools(skill_ids):
    names = {"write_todos", "task"}
    if "fileio" in skill_ids:
        names |= FILE_TOOLS
    if "execute" in skill_ids:
        names.add("execute")
    if "websearch" in skill_ids:
        names.add("tavily_search_results_json")
    if "rag" in skill_ids:
        names.add("it_knowledge_base")
    return names


class CapabilityMiddleware(AgentMiddleware):
    """Hide unselected tools and reject calls even if a model guesses a name."""
    def __init__(self, skill_ids):
        self.allowed = enabled_tools(skill_ids)

    def _request(self, request):
        return request.override(tools=[tool for tool in request.tools
                                       if getattr(tool, "name", None) in self.allowed])

    def wrap_model_call(self, request, handler):
        return handler(self._request(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._request(request))

    def _denial(self, request):
        name = request.tool_call["name"]
        if name not in self.allowed:
            return ToolMessage(content=f"Tool {name} is disabled for this session.",
                               tool_call_id=request.tool_call["id"], status="error")

    def wrap_tool_call(self, request, handler):
        return self._denial(request) or handler(request)

    async def awrap_tool_call(self, request, handler):
        denial = self._denial(request)
        return denial if denial is not None else await handler(request)


class _FilePermissions(BackendProtocol):
    """Backend permissions also cover the library's delegated subagents."""
    def __init__(self, backend, fileio):
        self.backend, self.fileio = backend, fileio

    def _file(self, method, *args, **kwargs):
        if not self.fileio:
            raise PermissionError("File I/O is disabled for this session.")
        return getattr(self.backend, method)(*args, **kwargs)

    def ls_info(self, path): return self._file("ls_info", path)
    def read(self, file_path, offset=0, limit=2000): return self._file("read", file_path, offset, limit)
    def write(self, file_path, content): return self._file("write", file_path, content)
    def edit(self, file_path, old_string, new_string, replace_all=False):
        return self._file("edit", file_path, old_string, new_string, replace_all)
    def glob_info(self, pattern, path="/"): return self._file("glob_info", pattern, path)
    def grep_raw(self, pattern, path=None, glob=None): return self._file("grep_raw", pattern, path, glob)
    def upload_files(self, files): return self._file("upload_files", files)
    def download_files(self, paths): return self._file("download_files", paths)


class _ExecutionPermissions(_FilePermissions, SandboxBackendProtocol):
    def execute(self, command): return self.backend.execute(command)
    async def aexecute(self, command): return await self.backend.aexecute(command)
    @property
    def id(self): return getattr(self.backend, "id", "local")


def restrict_backend(backend, skill_ids):
    cls = _ExecutionPermissions if "execute" in skill_ids else _FilePermissions
    return cls(backend, "fileio" in skill_ids)
