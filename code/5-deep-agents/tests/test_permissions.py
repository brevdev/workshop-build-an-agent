import importlib.util
import json
import os
from pathlib import Path
import shlex
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

REPO=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(REPO/'demo/backend'),str(REPO/'code')]
from capabilities import CapabilityMiddleware, restrict_backend
from deepagents.backends import FilesystemBackend
from deepagents.backends.protocol import SandboxBackendProtocol


def factory():
    path=REPO/'code/5-deep-agents/deep_agent.answers.py'
    spec=importlib.util.spec_from_file_location('tested_deep_agent',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def test_requested_sandbox_failure_never_creates_local_backend():
    mod=factory()
    with patch('docker_sandbox.DockerSandboxBackend',side_effect=RuntimeError('unavailable')), \
         patch.object(mod,'LocalShellBackend') as local:
        with pytest.raises(RuntimeError,match='No agent was created'):
            mod._build_backend(['execute'],{'execute':True})
        local.assert_not_called()


def test_rag_setup_error_does_not_expose_provider_details():
    mod = factory()
    def fail():
        raise RuntimeError("Provider failed: https://example.test/?api_key=TEST-SECRET")
    with patch.dict(sys.modules, {'rag': SimpleNamespace(get_retriever_tool=fail)}):
        with pytest.raises(RuntimeError, match='Could not load the selected RAG tool') as error:
            mod._build_extra_tools(['rag'])
    assert 'TEST-SECRET' not in str(error.value)
    assert 'example.test' not in str(error.value)


def test_file_only_boundaries_and_disabled_backend(tmp_path):
    root=tmp_path/'root';root.mkdir();outside=tmp_path/'secret';outside.write_text('CANARY')
    (root/'link').symlink_to(outside)
    backend=restrict_backend(FilesystemBackend(root_dir=root,virtual_mode=True),['fileio'])
    assert not isinstance(backend,SandboxBackendProtocol)
    assert backend.write('/hello.txt','Hello').error is None
    assert 'Hello' in backend.read('/hello.txt')
    for path in ['../secret',str(outside),'/link']:
        try:result=backend.read(path)
        except (ValueError,PermissionError):continue
        assert 'CANARY' not in result
    disabled=restrict_backend(FilesystemBackend(root_dir=root,virtual_mode=True),[])
    with pytest.raises(PermissionError):disabled.write('/unselected.txt','bad')
    assert not (root/'unselected.txt').exists()


def test_local_file_and_shell_tools_share_the_prompt_workspace(tmp_path, monkeypatch):
    mod = factory()
    workspace = tmp_path / 'workspace with spaces'
    workspace.mkdir()
    monkeypatch.setattr(mod, 'WORKSPACE_DIR', str(workspace))
    backend, sandbox = mod._build_backend(['fileio', 'execute'], {})
    prompt = mod._build_system_prompt(['fileio', 'execute'], 'nemotron', False)
    assert sandbox is None and f'Your workspace is: {workspace}' in prompt
    script = workspace / 'hello.py'
    assert backend.write(str(script), 'print("Hello World")\n').error is None
    assert 'Hello World' in backend.read(str(script))
    result = backend.execute(f'python3 {shlex.quote(str(script))}')
    assert result.exit_code == 0 and 'Hello World' in result.output.splitlines()
    # File-only mode keeps its virtual paths and existing boundary protections.
    files, _ = mod._build_backend(['fileio'], {})
    assert 'Hello World' in files.read('/hello.py')
    assert 'Your workspace is: /\n' in mod._build_system_prompt(['fileio'], 'nemotron', False)
    assert 'Your workspace is: /workspace\n' in mod._build_system_prompt(
        ['fileio', 'execute'], 'nemotron', False, sandbox_enabled=True)


def test_model_view_and_guessed_tool_calls_are_restricted():
    middleware=CapabilityMiddleware([])
    tools=[SimpleNamespace(name=x) for x in ['ls','write_file','execute','write_todos','task']]
    request=SimpleNamespace(tools=tools,override=lambda **kw:kw)
    assert [t.name for t in middleware.wrap_model_call(request,lambda x:x)['tools']]==['write_todos','task']
    request=SimpleNamespace(tool_call={'name':'write_file','id':'bad'})
    result=middleware.wrap_tool_call(request,lambda x:pytest.fail('Disabled tool executed'))
    assert result.status=='error'


@pytest.mark.skipif(os.environ.get('RUN_DOCKER_TESTS')!='1',reason='Explicit opt-in creates one disposable512MiB container')
def test_real_docker_byte_safety_and_boundaries():
    from docker_sandbox import DockerSandboxBackend
    backend=DockerSandboxBackend()
    try:
        content=" leading\nDEEPAGENT_EOF\ntouch /workspace/INJECTED\n# ' $(printf bad) \\ tail\n\n"
        name='/workspace/quotes\"; touch INJECTED; #.txt'
        assert backend.write(name,content).error is None
        assert backend.read(name)==content
        assert backend.read('/workspace/INJECTED').startswith('Error:')
        assert backend.edit(name,' leading','changed').error is None
        assert backend.read(name)==content.replace(' leading','changed')
        blob=b'\x00\xff\n\x80'
        assert backend.upload_files([('/workspace/binary',blob)])[0].error is None
        assert backend.download_files(['/workspace/binary'])[0].content==blob
        assert backend.write('/etc/audit','blocked').error
        assert backend.write('/workspace/../escape','blocked').error
        assert backend.execute('ln -s /etc/passwd /workspace/link').exit_code==0
        assert backend.read('/workspace/link').startswith('Error:')
        output=backend.execute('python -c "print(\'x\'*100000)"')
        assert output.truncated and len(output.output)<51000
        backend._container.reload();host=backend._container.attrs['HostConfig']
        assert host['NetworkMode']=='none' and host['ReadonlyRootfs']
        assert host['PidsLimit']==64 and host['Memory']==512*1024*1024
        assert backend._container.attrs['Config']['User']=='65534:65534'
        assert not backend._container.attrs['Mounts']
        network=backend.execute("python -c 'import socket; socket.create_connection((\"1.1.1.1\",443),timeout=2)'")
        assert network.exit_code != 0
        assert backend.id
    finally:backend.delete()


def test_real_graph_denies_unselected_write_and_preserves_hitl(tmp_path, monkeypatch):
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    from langgraph.types import Command
    class Scripted(FakeMessagesListChatModel):
        tools_seen: list = []
        def bind_tools(self, tools, **kwargs):
            self.tools_seen = [tool.name for tool in tools]
            return self
    mod = factory()
    monkeypatch.setattr(mod, 'WORKSPACE_DIR', str(tmp_path))
    for selected in (False, True):
        fake = Scripted(responses=[AIMessage(content='', tool_calls=[{
            'name':'write_file', 'args':{'file_path':'/canary.txt','content':'fixture'},
            'id':'write', 'type':'tool_call'}]), AIMessage(content='Finished')])
        monkeypatch.setattr(mod, '_get_model', lambda _: fake)
        agent, sandbox = mod.create_agent(['fileio'] if selected else [], hitl_enabled=True)
        config = {'configurable': {'thread_id': f'guard-{selected}'}}
        state = agent.invoke({'messages':[{'role':'user','content':'Write canary'}]}, config)
        assert not (tmp_path/'canary.txt').exists()
        assert ('write_file' in fake.tools_seen) is selected
        assert bool(state.get('__interrupt__')) is selected
        if selected:
            agent.invoke(Command(resume={'decisions':[{'type':'approve'}]}),config)
            assert (tmp_path/'canary.txt').read_text()=='fixture'


def test_delegated_backend_cannot_use_disabled_files(tmp_path, monkeypatch):
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    class Scripted(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs): return self
    fake=Scripted(responses=[
        AIMessage(content='',tool_calls=[{'name':'task','args':{'description':'Write a file','subagent_type':'general-purpose'},'id':'delegate','type':'tool_call'}]),
        AIMessage(content='',tool_calls=[{'name':'write_file','args':{'file_path':'/canary.txt','content':'fixture'},'id':'write','type':'tool_call'}]),
        AIMessage(content='Finished'),AIMessage(content='Finished')])
    mod=factory();monkeypatch.setattr(mod,'WORKSPACE_DIR',str(tmp_path));monkeypatch.setattr(mod,'_get_model',lambda _:fake)
    agent,_=mod.create_agent([])
    try:
        state=agent.invoke({'messages':[{'role':'user','content':'Delegate a write'}]}, {'configurable':{'thread_id':'delegated-denial'}})
    except PermissionError as exc:
        assert 'disabled' in str(exc)
    assert not (tmp_path/'canary.txt').exists()


def test_creation_api_reports_actual_permissions_and_fails_closed(monkeypatch):
    import server
    from fastapi.testclient import TestClient
    server.sessions.clear()
    monkeypatch.setattr(server, 'create_agent', lambda *args: (object(), None))
    with TestClient(server.app) as client:
        choices = client.get('/api/models').json()['models']
        assert {choice['id'] for choice in choices} == {'nemotron', 'nemotron_fast'}
        response = client.post('/api/agent', json={'skill_ids':['fileio']})
        assert response.status_code == 200
        body = response.json()
        assert body['capabilities']['execution'] == 'disabled'
        assert 'execute' not in body['enabled_tools']
        assert not body['sandbox_active']
        client.delete('/api/agent/' + body['session_id'])
        for error, status in [(ValueError('Unsupported model'),422), (RuntimeError('Docker unavailable; no agent created'),503)]:
            def failed(*args): raise error
            monkeypatch.setattr(server, 'create_agent', failed)
            response = client.post('/api/agent', json={'skill_ids':['execute'], 'sandbox_map':{'execute':True}})
            assert response.status_code == status
            assert not server.sessions


def test_shutdown_removes_owned_sandboxes(monkeypatch):
    import server
    from fastapi.testclient import TestClient
    deleted = []
    sandbox = SimpleNamespace(delete=lambda: deleted.append(True))
    monkeypatch.setattr(server, 'create_agent', lambda *args: (object(), sandbox))
    with TestClient(server.app) as client:
        response = client.post('/api/agent', json={'skill_ids':['fileio'], 'sandbox_map':{'fileio':True}})
        assert response.json()['sandbox_active'] is True
        assert response.json()['capabilities']['file_root'] == '/workspace'
    assert deleted == [True]
    assert not server.sessions


def test_tool_events_preserve_structured_errors_without_guessing_from_text():
    from langchain_core.messages import ToolMessage
    from server import _process_event
    cases = [
        ('on_tool_end', {'output': ToolMessage(content='Disabled', tool_call_id='call', status='error')}, 'error'),
        ('on_tool_error', {'error': PermissionError('Denied')}, 'error'),
        ('on_tool_end', {'output': ToolMessage(content='The file describes an error.', tool_call_id='call')}, 'success'),
        ('on_tool_end', {'output': 'error is a word in this file'}, 'success'),
    ]
    for kind, data, expected in cases:
        timers = {'call': 0}
        event = _process_event({'event': kind, 'name': 'read_file', 'run_id': 'call', 'data': data}, timers)
        assert event['event'] == 'tool_end'
        assert json.loads(event['data'])['status'] == expected
        assert not timers


def test_model_transport_limits_and_fast_model_reasoning(monkeypatch):
    mod = factory()
    monkeypatch.setattr(mod, 'ChatNVIDIA', lambda **kwargs: kwargs)
    fast = mod._get_model('nemotron_fast')
    assert fast['timeout'] == 90 and fast['max_tokens'] == 4096
    assert fast['model_kwargs']['chat_template_kwargs']['enable_thinking'] is False
    assert mod._get_model('nemotron')['model_kwargs'] == {}


def test_stream_errors_do_not_expose_provider_payloads(capsys):
    import asyncio
    import server
    secret = 'TEST-PROVIDER-CREDENTIAL'
    class FailingAgent:
        async def astream_events(self, *args, **kwargs):
            raise Exception('[429] https://provider.test/?api_key=' + secret)
            yield
    session = server.AgentSession(FailingAgent(), 'nemotron_fast', [], 'test', True)
    session.pending_interrupt = {'action_requests': [{'name': 'write_file'}]}
    async def collect():
        return ([event async for event in server._stream_response(session, 'Hello')],
                [event async for event in server._stream_resume(session, 'approve', None)])
    for events in asyncio.run(collect()):
        assert events[-1]['event'] == 'error'
        message = json.loads(events[-1]['data'])['message']
        assert 'HTTP 429' in message and secret not in message and 'provider.test' not in message
    assert secret not in capsys.readouterr().out
    event = server._process_event({'event': 'on_tool_error', 'data': {'error': RuntimeError(secret)}}, {})
    assert secret not in event['data']
