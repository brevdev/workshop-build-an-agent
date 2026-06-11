"""Entry point: `python -m hermes`.

Answer key — solved version of hermes/__main__.py.

  python -m hermes                 # interactive REPL
  python -m hermes --once "hi"     # single message, print, exit (good for scripts/sandbox)
  python -m hermes --auto-approve  # skip the y/N gate (unattended runs)
"""
from __future__ import annotations

import argparse
import sys

from . import client
from .harness import Harness


def main() -> int:
    parser = argparse.ArgumentParser(prog="hermes", description="A glass-box agent harness.")
    parser.add_argument("--once", metavar="TEXT", help="send one message, print the reply, exit")
    parser.add_argument("--auto-approve", action="store_true", help="auto-approve gated tools")
    args = parser.parse_args()

    try:
        agent = Harness(auto_approve=args.auto_approve)
        if args.once is not None:
            print(agent.send(args.once))
        else:
            agent.repl()
    except (client.ModelConnectionError, client.ModelHTTPError) as e:
        sys.stderr.write("\n[hermes] could not talk to the model: {}\n".format(e))
        sys.stderr.write("[hermes] check NVIDIA_API_KEY (host) or HERMES_BASE_URL (sandbox).\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
