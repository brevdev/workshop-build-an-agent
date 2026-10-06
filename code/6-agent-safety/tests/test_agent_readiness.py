"""The live readiness check must verify file effects, not trust model claims."""
import importlib.util
from pathlib import Path
import subprocess

import pytest


path = Path(__file__).resolve().parents[1] / 'scripts/check-nemoclaw-agent.py'
spec = importlib.util.spec_from_file_location('agent_readiness', path)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def test_hook_failure_is_not_hidden_by_zero_exit_status(monkeypatch):
    monkeypatch.setattr(check.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(
        a, 0, '{}', '[agents/tools] before_tool_call hook failed: TypeError includes'))
    with pytest.raises(check.CheckFailed, match='tool-hook failure'):
        check.run_cli('my-assistant', ['openclaw', 'agent'], 5)


def test_unrequested_embedded_fallback_is_not_a_gateway_success(monkeypatch):
    monkeypatch.setattr(check, 'run_cli', lambda *a: '{"payloads":[{"text":"hello"}]}')
    with pytest.raises(check.CheckFailed, match='gateway result'):
        check.ask_agent('my-assistant', 'hello', 5)


def test_pending_scope_upgrade_is_reported_separately(monkeypatch):
    monkeypatch.setattr(check.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(
        a, 0, '{"payloads":[{"text":"hello"}]}', 'scope upgrade pending approval'))
    with pytest.raises(check.PairingPending):
        check.ask_agent('my-assistant', 'hello', 5)


@pytest.mark.parametrize('diagnostic', [
    'EMBEDDED FALLBACK: Gateway agent failed; running embedded agent',
    'Gateway agent failed; falling back to embedded',
])
def test_any_embedded_fallback_fails_even_with_valid_gateway_shaped_json(monkeypatch, diagnostic):
    monkeypatch.setattr(check.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(
        a, 0, '{"result":{"payloads":[{"text":"hello"}]}}', diagnostic))
    with pytest.raises(check.CheckFailed, match='embedded mode'):
        check.ask_agent('my-assistant', 'hello', 5)


def test_cleanup_error_does_not_hide_the_original_failure(monkeypatch, capsys):
    def ask(*args):
        raise check.CheckFailed('original inference failure')

    def cleanup(*args):
        raise check.CheckFailed('cleanup connection lost')

    monkeypatch.setattr(check, 'ask_agent', ask)
    monkeypatch.setattr(check, 'run_cli', cleanup)
    with pytest.raises(check.CheckFailed, match='original inference failure'):
        check.check_agent('my-assistant', 5)
    assert 'cleanup connection lost' in capsys.readouterr().err


def test_persistent_pairing_failure_has_bounded_retry(monkeypatch):
    prompts, waits, cleanup = [], [], []

    def ask(sandbox, prompt, timeout):
        prompts.append(prompt)
        raise check.PairingPending('still pending')

    monkeypatch.setattr(check, 'ask_agent', ask)
    monkeypatch.setattr(check.time, 'sleep', waits.append)
    monkeypatch.setattr(check, 'run_cli', lambda *args: cleanup.append(args))
    with pytest.raises(check.PairingPending):
        check.check_agent('my-assistant', 5)
    assert len(prompts) == 3
    assert waits == [30, 30]
    assert all('Do not use tools' in prompt for prompt in prompts)
    assert 'unlink' in cleanup[-1][1][2]


def test_claimed_write_without_file_effect_fails_and_cleans_up(monkeypatch):
    calls = []
    monkeypatch.setattr(check, 'ask_agent', lambda *a: 'Done, I wrote the file.')

    def run(sandbox, args, timeout):
        calls.append(args)
        if 'unlink' not in args[2]:
            raise check.CheckFailed('Requested file is absent')
        return ''

    monkeypatch.setattr(check, 'run_cli', run)
    with pytest.raises(check.CheckFailed, match='absent'):
        check.check_agent('my-assistant', 5)
    assert 'unlink' in calls[-1][2]


@pytest.mark.parametrize('reads_current_content', [True, False])
def test_read_requires_the_independent_file_content(monkeypatch, reads_current_content):
    state = {'content': '', 'prompts': [], 'cleaned': False}

    def ask(sandbox, prompt, timeout):
        state['prompts'].append(prompt)
        if 'read tool' in prompt:
            return state['content'] if reads_current_content else 'I read it successfully.'
        return 'Hello, done.'

    def run(sandbox, args, timeout):
        if 'unlink' in args[2]:
            state['cleaned'] = True
        else:
            state['content'] = args[-1]
        return ''

    monkeypatch.setattr(check, 'ask_agent', ask)
    monkeypatch.setattr(check, 'run_cli', run)
    if reads_current_content:
        check.check_agent('my-assistant', 5)
    else:
        with pytest.raises(check.CheckFailed, match='current file contents'):
            check.check_agent('my-assistant', 5)
    assert state['cleaned']
    assert state['content']
    assert all(state['content'] not in prompt for prompt in state['prompts'])


def test_greeting_retries_an_exec_timeout(monkeypatch):
    calls = {'greet': 0}

    def ask(sandbox, prompt, timeout):
        if 'hello' in prompt:
            calls['greet'] += 1
            if calls['greet'] == 1:
                raise check.subprocess.TimeoutExpired(['nemoclaw'], timeout)
            return 'Hello.'
        if 'read tool' in prompt:
            return state['content']
        return 'Done.'

    state = {'content': ''}

    def run(sandbox, args, timeout):
        if 'unlink' not in args[2]:
            state['content'] = args[-1]
        return ''

    monkeypatch.setattr(check, 'ask_agent', ask)
    monkeypatch.setattr(check, 'run_cli', run)
    check.check_agent('my-assistant', 5)
    assert calls['greet'] == 2


def test_read_accepts_a_reply_split_across_payloads(monkeypatch):
    state = {'content': ''}

    def ask(sandbox, prompt, timeout):
        if 'read tool' in prompt:  # OpenClaw joins separate text payloads with blank lines
            return state['content'][:12] + '\n\n' + state['content'][12:]
        return 'Done.'

    def run(sandbox, args, timeout):
        if 'unlink' not in args[2]:
            state['content'] = args[-1]
        return ''

    monkeypatch.setattr(check, 'ask_agent', ask)
    monkeypatch.setattr(check, 'run_cli', run)
    check.check_agent('my-assistant', 5)
