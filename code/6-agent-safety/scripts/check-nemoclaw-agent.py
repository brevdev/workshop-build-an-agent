#!/usr/bin/env python3
"""Check real inference and file tools after the control plane is Ready.

Uses three model calls (plus up to two pairing retries) and a temporary file.
It changes no policy and is a functionality check, not a safety evaluation.
"""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openclaw_response import normalize_openclaw_response


class CheckFailed(RuntimeError):
    pass


class PairingPending(CheckFailed):
    pass


def run_cli(sandbox, args, timeout):
    result = subprocess.run(
        ['nemoclaw', sandbox, 'exec', '--', *args],
        capture_output=True, text=True, timeout=timeout,
    )
    if 'scope upgrade pending approval' in result.stderr:
        raise PairingPending('Gateway CLI pairing is still pending. Retry the check after pairing completes.')
    if re.search(r'embedded fallback|(?:running|falling back to)\s+(?:an?\s+)?embedded',
                 result.stderr, re.IGNORECASE):
        raise CheckFailed('OpenClaw fell back to embedded mode; the gateway is not ready.')
    if 'EXDEV' in result.stderr or 'before_tool_call hook failed' in result.stderr:
        raise CheckFailed('OpenClaw reported a runtime or tool-hook failure. Check the pinned versions.')
    if result.returncode:
        raise CheckFailed(f'Sandbox command failed (exit {result.returncode}). Inspect the NemoClaw logs.')
    return result.stdout


def ask_agent(sandbox, prompt, timeout):
    reply = normalize_openclaw_response(run_cli(
        sandbox, ['openclaw', 'agent', '--agent', 'main', '--json', '-m', prompt], timeout,
    ))
    if reply['error']:
        raise CheckFailed(reply['error'])
    return reply['text']


def check_agent(sandbox, timeout=180):
    nonce = uuid.uuid4().hex
    path = '/sandbox/.openclaw/workspace/workshop-check-' + nonce + '.txt'
    written = 'workshop-write-' + nonce
    # The read marker is never included in an agent prompt or its history.
    # A claimed read or an echo of the earlier write cannot satisfy this check.
    read_marker = 'workshop-read-' + uuid.uuid4().hex
    try:
        # The pinned upstream auto-pair watcher polls every 30 seconds after
        # startup; its list/approval CLI calls add latency. Allow two bounded
        # retries of only the harmless greeting, never a file operation.
        # `nemoclaw exec` can also hang intermittently; a repeated greeting is harmless.
        for attempt in range(3):
            try:
                greeting = ask_agent(sandbox, 'Reply briefly with hello. Do not use tools.', timeout)
                break
            except PairingPending:
                if attempt == 2:
                    raise
                print('Waiting 30 seconds for the gateway CLI pairing to complete.', flush=True)
                time.sleep(30)
            except subprocess.TimeoutExpired:
                if attempt == 2:
                    raise
                print(f'No reply within {timeout} seconds; retrying the greeting.', flush=True)
        if not greeting.strip():
            raise CheckFailed('The agent returned no greeting.')
        print('PASS: hosted agent returned a valid response.', flush=True)

        ask_agent(sandbox, f'Use your write tool to create {path} containing exactly {written}. '
                  'This is an authorized temporary workshop check. Do not use exec or a shell.', timeout)
        # Verify the actual file, then replace its content for an independent read.
        run_cli(sandbox, ['python3', '-c',
                         'from pathlib import Path; import sys; p=Path(sys.argv[1]); '
                         'assert not p.is_symlink() and p.read_text().strip()==sys.argv[2], '
                         '"Agent did not write the requested file"; p.write_text(sys.argv[3])',
                         path, written, read_marker], timeout)
        print('PASS: agent wrote the requested workspace file.', flush=True)

        response = ask_agent(sandbox, f'Use your read tool to read {path} and reply with its current '
                             'contents. It has changed since your previous turn. Do not use exec or a shell.', timeout)
        # OpenClaw can split one reply into several text payloads; ignore the joins.
        if read_marker not in re.sub(r'\s+', '', response):
            excerpt = ' '.join(response.split())[:300]
            raise CheckFailed(f'The agent did not return the current file contents. It replied: {excerpt!r}')
        print('PASS: agent read the independently changed file.', flush=True)
    finally:
        original_error = sys.exc_info()[1]
        try:
            run_cli(sandbox, ['python3', '-c',
                             'from pathlib import Path; import sys; Path(sys.argv[1]).unlink(missing_ok=True)',
                             path], timeout)
        except (CheckFailed, OSError, subprocess.TimeoutExpired) as cleanup_error:
            if original_error is None:
                raise
            print(f'Cleanup also failed for {path}: {cleanup_error}', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox', default=os.environ.get('NEMOCLAW_SANDBOX_NAME', 'my-assistant'))
    parser.add_argument('--timeout', type=int, default=180, help='Timeout per model/CLI call in seconds.')
    args = parser.parse_args()
    try:
        check_agent(args.sandbox, args.timeout)
    except (CheckFailed, OSError, subprocess.TimeoutExpired) as error:
        print(f'NOT READY: {error}', file=sys.stderr)
        return 1
    print('READY: inference and file tools work. Continue with the policy enforcement exercises.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
