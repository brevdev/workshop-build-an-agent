"""Exercise the installer without downloading or touching Docker/user services."""
import os
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/install-nemoclaw.sh'


@pytest.mark.parametrize('status,code,ready', [
    ('  Phase: Ready\n', 0, True),
    ('\x1b[2mPhase:\x1b[0m Ready\n', 0, True),
    ('No sandboxes registered\n', 0, False),
    ('Phase: Pending\n', 0, False),
    ('Phase: Readyish\n', 0, False),
    ('Phase: Ready\n', 1, False),
])
def test_installer_requires_successful_ready_target(tmp_path, status, code, ready):
    result, calls = run_installer(tmp_path, status, code)
    assert "nemoclaw ['custom-lab', 'status']" in calls
    if ready:
        assert result.returncode == 0
        assert "sandbox 'custom-lab' is Ready" in result.stdout
        assert 'curl ' not in calls and 'docker [\'run\'' not in calls
    else:
        # A failed download must propagate through curl | bash, not claim success.
        assert result.returncode == 22
        assert "sandbox 'custom-lab' is not Ready" in result.stdout
        assert 'curl ' in calls
        assert 'installed and onboarded' not in result.stdout


@pytest.mark.parametrize('after_status,expected', [('Phase: Pending\n', 1), ('Phase: Ready\n', 0)])
def test_successful_installer_still_requires_ready_sandbox(tmp_path, after_status, expected):
    result, _ = run_installer(tmp_path, 'Phase: Pending\n', 0, download_code=0, after_status=after_status)
    assert result.returncode == expected
    assert ('installed and onboarded' in result.stdout) is (expected == 0)


def test_explicit_base_override_is_preserved(tmp_path):
    result, calls = run_installer(tmp_path, 'Phase: Pending\n', 0, base_override='example.test/chosen:base')
    assert result.returncode == 22
    assert 'base=example.test/chosen:base' in calls


def test_existing_logs_become_private(tmp_path):
    for name in ('install.log', 'tunnel.log'):
        log = tmp_path / name
        log.write_text('existing diagnostic output\n')
        log.chmod(0o644)
    result, _ = run_installer(tmp_path, 'Phase: Ready\n', 0)
    assert result.returncode == 0
    for name in ('install.log', 'tunnel.log'):
        assert (tmp_path / name).stat().st_mode & 0o777 == 0o600


def test_ready_wildcard_gateway_requires_repair(tmp_path):
    result, calls = run_installer(tmp_path, 'Phase: Ready\n', 0, gateway_bind='0.0.0.0')
    assert result.returncode == 22
    assert 'gateway bind needs repair' in result.stdout
    assert 'curl ' in calls


def test_ready_bridge_gateway_takes_fast_path(tmp_path):
    result, calls = run_installer(tmp_path, 'Phase: Ready\n', 0, gateway_bind='bridge')
    assert result.returncode == 0
    assert 'curl ' not in calls


def test_installer_rejects_wildcard_gateway_after_onboarding(tmp_path):
    result, _ = run_installer(tmp_path, 'Phase: Pending\n', 0, download_code=0,
                              after_status='Phase: Ready\n', gateway_bind='0.0.0.0')
    assert result.returncode == 1
    assert 'private gateway bind check failed' in result.stdout


def run_installer(tmp_path, status, code, download_code=22, after_status=None, base_override=None, gateway_bind=None):
    # Relocate only the two log files; all branching and commands are unchanged.
    source = SCRIPT.read_text().replace('LOG=/tmp/nemoclaw-install.log', f'LOG={tmp_path}/install.log')
    source = source.replace('TUNNEL_LOG=/tmp/nemoclaw-tunnel.log', f'TUNNEL_LOG={tmp_path}/tunnel.log')
    script = tmp_path / 'install.sh'
    script.write_text(source)
    (tmp_path / 'workbench_docker.py').write_text(
        (SCRIPT.parent / 'workbench_docker.py').read_text())
    shim = '''#!/usr/bin/env python3
import os, pathlib, sys
name=pathlib.Path(sys.argv[0]).name
with open(os.environ['AUDIT_COMMANDS'],'a') as out:
    out.write(name+' '+repr(sys.argv[1:])+'\\n')
if name=='nemoclaw':
    if sys.argv[1:]==['status']:
        print('cloudflared stopped');sys.exit(0)
    assert sys.argv[1:]==['custom-lab','status']
    count=pathlib.Path(os.environ['AUDIT_COMMANDS']+'.status-count')
    output=os.environ.get('AUDIT_AFTER_STATUS',os.environ['AUDIT_STATUS']) if count.exists() else os.environ['AUDIT_STATUS']
    count.touch()
    print(output,end='');sys.exit(int(os.environ['AUDIT_CODE']))
if name=='docker' and sys.argv[1:2]==['ps']:print('audit-container')
if name=='docker' and sys.argv[1:2]==['inspect']:
    bind=os.environ.get('AUDIT_GATEWAY_BIND')
    if not bind:sys.exit(1)
    if bind=='bridge':
        import socket, struct
        route=next(line.split() for line in pathlib.Path('/proc/net/route').read_text().splitlines()[1:] if line.split()[1]=='00000000')
        bind=socket.inet_ntoa(struct.pack('<I',int(route[2],16)))
    print('OPENSHELL_BIND_ADDRESS='+bind)
if name=='curl':
    with open(os.environ['AUDIT_COMMANDS'],'a') as out:out.write('base='+os.environ.get('NEMOCLAW_SANDBOX_BASE_IMAGE_REF','')+'\\n')
    if os.environ['AUDIT_DOWNLOAD_CODE']=='0':print('exit 0')
    sys.exit(int(os.environ['AUDIT_DOWNLOAD_CODE']))
'''
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    for name in ('nemoclaw', 'docker', 'curl', 'socat', 'pgrep', 'pkill'):
        target = bin_dir / name
        target.write_text(shim)
        target.chmod(0o755)
    command_log = tmp_path / 'commands'
    env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}',
               WORKSHOP_NEMOCLAW_SHARED_DIR=str(tmp_path / 'shared'),
               NEMOCLAW_SANDBOX_NAME='custom-lab', AUDIT_COMMANDS=str(command_log),
               AUDIT_STATUS=status, AUDIT_CODE=str(code), AUDIT_DOWNLOAD_CODE=str(download_code))
    if after_status is not None:
        env['AUDIT_AFTER_STATUS'] = after_status
    if base_override is not None:
        env['NEMOCLAW_SANDBOX_BASE_IMAGE_REF'] = base_override
    if gateway_bind is not None:
        env['AUDIT_GATEWAY_BIND'] = gateway_bind
    result = subprocess.run(['bash', str(script)], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=10)
    return result, command_log.read_text()
