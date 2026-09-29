#!/usr/bin/env python3
"""Translate the pinned compatibility gateway's mounts across Workbench Docker.

The Docker daemon resolves bind sources on its host, not in this client container.
Only NemoClaw's named compatibility-gateway launch is adapted; other Docker calls
pass through unchanged. Runtime files live in the existing shared volume.
"""
import ipaddress
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def stage_binary(source, destination):
    """Replace the path atomically; an existing sandbox may execute its inode."""
    descriptor, temporary = tempfile.mkstemp(dir=destination.parent, prefix='.stage-')
    os.close(descriptor)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def host_path(path, mounts):
    """Resolve a client path through its longest matching Docker mount."""
    path = str(Path(path).resolve())
    for mount in sorted(mounts, key=lambda item: len(item['Destination']), reverse=True):
        destination = str(Path(mount['Destination']).resolve()).rstrip('/')
        if path == destination or path.startswith(destination + '/'):
            return mount['Source'].rstrip('/') + path[len(destination):]
    raise ValueError('Gateway runtime path is outside the shared Docker mounts')


def adapt_gateway(args, env, mounts):
    """Stage runtime binaries and translate this gateway's three bind mounts."""
    args = list(args)
    env = dict(env)
    shared = Path(env['WORKSHOP_NEMOCLAW_SHARED_DIR']).resolve()
    binaries = shared / 'bin'
    binaries.mkdir(parents=True, exist_ok=True)
    sandbox = Path(env['OPENSHELL_DOCKER_SUPERVISOR_BIN'])
    binary_host = host_path(binaries, mounts)
    state = Path(env['NEMOCLAW_OPENSHELL_GATEWAY_STATE_DIR']).resolve()
    state_host = host_path(state, mounts)
    gateway_found = False
    for index in range(len(args) - 1):
        if args[index] not in ('-v', '--volume'):
            continue
        source, target, *mode = args[index + 1].split(':')
        if target == '/opt/nemoclaw/openshell-gateway':
            stage_binary(source, binaries / 'openshell-gateway')
            source = binary_host + '/openshell-gateway'
            gateway_found = True
        elif Path(source).resolve() == sandbox.parent.resolve():
            stage_binary(sandbox, binaries / 'openshell-sandbox')
            source = target = binary_host
        elif Path(source).resolve() == state:
            source = target = state_host
        else:
            source = host_path(source, mounts)
        args[index + 1] = ':'.join([source, target, *mode])
    if not gateway_found:
        raise ValueError('Unexpected compatibility gateway mount layout')
    env['OPENSHELL_DOCKER_SUPERVISOR_BIN'] = binary_host + '/openshell-sandbox'
    env['OPENSHELL_DB_URL'] = 'sqlite:' + state_host + '/openshell.db'
    # The pinned compatibility gateway disables TLS/auth. Its operator listener
    # must stay on the bridge used by the Workbench tunnel, not every host NIC.
    address = ipaddress.ip_address(env['WORKSHOP_DOCKER_HOST_IP'])
    if address.is_unspecified or address.is_multicast or address.is_loopback:
        raise ValueError('Expected the Docker host bridge address')
    env['OPENSHELL_BIND_ADDRESS'] = str(address)
    return args, env


def main():
    args = sys.argv[1:]
    # NemoClaw deliberately filters subprocess environment variables. Keep only
    # these non-secret adapter paths in its private temporary directory.
    settings = json.loads(Path(__file__).with_name('config.json').read_text())
    real_docker = settings['WORKSHOP_REAL_DOCKER']
    name = settings['NEMOCLAW_OPENSHELL_GATEWAY_COMPAT_CONTAINER_NAME']
    is_gateway = args[:1] == ['run'] and any(
        args[index:index + 2] == ['--name', name] for index in range(len(args)))
    env = dict(os.environ)
    env.update(settings)
    if is_gateway:
        result = subprocess.run(
            [real_docker, 'inspect', '--format', '{{json .Mounts}}',
             env.get('WORKSHOP_CLIENT_CONTAINER', env.get('HOSTNAME', ''))],
            check=True, capture_output=True, text=True, timeout=15)
        args, env = adapt_gateway(args, env, json.loads(result.stdout))
    os.execve(real_docker, [real_docker, *args], env)


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, OSError, subprocess.SubprocessError) as error:
        print('Workbench gateway mount setup failed (' + type(error).__name__ +
              '). Check the shared-volume mount and Docker access.', file=sys.stderr)
        sys.exit(1)
