"""Verify the client/daemon boundary used by the actual compatibility gateway."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys

import pytest


path = Path(__file__).resolve().parents[1] / 'scripts/workbench_docker.py'
spec = importlib.util.spec_from_file_location('workbench_docker', path)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def test_gateway_and_supervisor_use_daemon_visible_files(tmp_path):
    installed = tmp_path / 'client-bin'
    installed.mkdir()
    gateway = installed / 'openshell-gateway'
    sandbox = installed / 'openshell-sandbox'
    gateway.write_bytes(b'gateway-binary')
    sandbox.write_bytes(b'supervisor-binary')
    shared = tmp_path / 'shared'
    state = shared / 'state'
    state.mkdir(parents=True)
    socket = tmp_path / 'docker.sock'
    socket.touch()
    mounts = [
        {'Source': '/daemon/volume', 'Destination': str(shared)},
        {'Source': '/run/docker.sock', 'Destination': str(socket)},
    ]
    env = {'WORKSHOP_NEMOCLAW_SHARED_DIR': str(shared),
           'WORKSHOP_DOCKER_HOST_IP': '172.18.0.1',
           'OPENSHELL_BIND_ADDRESS': '0.0.0.0',
           'NEMOCLAW_OPENSHELL_GATEWAY_STATE_DIR': str(state),
           'OPENSHELL_DOCKER_SUPERVISOR_BIN': str(sandbox),
           'OPENSHELL_DB_URL': 'sqlite:' + str(state / 'openshell.db')}
    args = ['run', '--name', 'nemoclaw-openshell-gateway',
            '--volume', f'{gateway}:/opt/nemoclaw/openshell-gateway:ro',
            '--volume', f'{state}:{state}:rw',
            '--volume', f'{installed}:{installed}:ro',
            '--volume', f'{socket}:/var/run/docker.sock:rw']
    result, child_env = adapter.adapt_gateway(args, env, mounts)
    assert '/daemon/volume/bin/openshell-gateway:/opt/nemoclaw/openshell-gateway:ro' in result
    assert '/daemon/volume/state:/daemon/volume/state:rw' in result
    assert '/daemon/volume/bin:/daemon/volume/bin:ro' in result
    assert '/run/docker.sock:/var/run/docker.sock:rw' in result
    assert child_env['OPENSHELL_DOCKER_SUPERVISOR_BIN'] == '/daemon/volume/bin/openshell-sandbox'
    assert child_env['OPENSHELL_DB_URL'] == 'sqlite:/daemon/volume/state/openshell.db'
    assert child_env['OPENSHELL_BIND_ADDRESS'] == '172.18.0.1'
    assert (shared / 'bin/openshell-gateway').read_bytes() == b'gateway-binary'
    assert (shared / 'bin/openshell-sandbox').read_bytes() == b'supervisor-binary'
    assert args[4].startswith(str(gateway))  # caller arguments remain intact


def test_mount_translation_uses_longest_boundary_match(tmp_path):
    shared = tmp_path / 'shared'
    nested = shared / 'nested'
    mounts = [{'Source': '/outer', 'Destination': str(shared)},
              {'Source': '/inner', 'Destination': str(nested)}]
    assert adapter.host_path(nested / 'file', mounts) == '/inner/file'
    with pytest.raises(ValueError):
        adapter.host_path(tmp_path / 'shared-other/file', mounts)
    with pytest.raises(ValueError):
        adapter.host_path(shared / '../outside', mounts)


def test_restage_keeps_running_binary_valid(tmp_path):
    source = tmp_path / 'source'
    target = tmp_path / 'running'
    shutil.copy2('/bin/sleep', source)
    adapter.stage_binary(source, target)
    process = subprocess.Popen([str(target), '30'])
    try:
        inode = target.stat().st_ino
        adapter.stage_binary(source, target)
        assert target.stat().st_ino != inode
        assert target.read_bytes() == source.read_bytes()
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_symlinked_socket_mount_is_resolved(tmp_path):
    target = tmp_path / 'socket-real'
    target.touch()
    link = tmp_path / 'socket-link'
    link.symlink_to(target)
    assert adapter.host_path(link, [{'Source': '/run/docker.sock',
                                     'Destination': str(link)}]) == '/run/docker.sock'


def test_other_docker_commands_survive_filtered_environment(tmp_path):
    real = tmp_path / 'real-docker'
    real.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]));sys.exit(7)\n')
    real.chmod(0o755)
    proxy = tmp_path / 'docker'
    proxy.write_text(path.read_text())
    (tmp_path / 'config.json').write_text(json.dumps({
        'WORKSHOP_REAL_DOCKER': str(real),
        'NEMOCLAW_OPENSHELL_GATEWAY_COMPAT_CONTAINER_NAME': 'nemoclaw-openshell-gateway',
    }))
    result = subprocess.run([sys.executable, str(proxy), 'info', '--format', '{{json .}}'],
                            env={'PATH': os.environ['PATH']}, capture_output=True, text=True)
    assert result.returncode == 7
    assert json.loads(result.stdout) == ['info', '--format', '{{json .}}']
