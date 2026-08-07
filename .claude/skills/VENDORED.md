# Vendored skills

`nvwb/` and `nvwb-project/` are **vendored** (real copies, not symlinks) from the
upstream nvwb-skills repo so they ship with this workshop and load automatically
when an agent runs Claude Code inside a clone — no separate install. The workshop
runs entirely on NVIDIA AI Workbench, so these are the CLI/project companions to
the `setup-workshop` skill.

| Skill | Purpose |
|---|---|
| `nvwb/` | AI Workbench CLI control-plane: contexts, clone, build, apps, mounts, env vars. |
| `nvwb-project/` | In-container project awareness for dirs with `.project/spec.yaml` (this repo). Includes opt-in agent-sandbox `hooks/` (not auto-activated). |
| `setup-workshop/` | Local bootstrap that spins up DevX-Lab (authored for this workshop). |

## Provenance
- Upstream: https://github.com/nv-twhitehouse/nvwb-skills
- Vendored at commit: `8f6b85b` ("Add common-context, agent sandbox hooks, and env var protection")
- Vendored on: 2026-06-25

## Why copies, not committed symlinks
A symlink committed to git stores its absolute target path, which exists only on
the machine that created it — every other clone would get a **dangling** link and
the skill would silently fail to load. Real copies travel with the repo.

## Re-syncing with upstream (pinned snapshot — does not auto-update)
```bash
UP=~/.claude/skills-repos/nvwb-skills        # or a fresh clone of the upstream
git -C "$UP" pull
rm -rf .claude/skills/nvwb .claude/skills/nvwb-project
cp -a "$UP/nvwb" "$UP/nvwb-project" .claude/skills/
```

## Not vendored
`cursor-rules/` (Cursor IDE rules) and `spec.schema.json` from upstream are
omitted. Only the optional Cursor agent-bridge in
`nvwb-project/references/agent-bridge.md` references `cursor-rules/`; copy it from
upstream into `.claude/skills/cursor-rules/` if that feature is used.

## Machine-local global access (NOT shipped)
On this machine, `~/.claude/skills/nvwb` and `~/.claude/skills/nvwb-project` are
symlinked to these vendored copies so they're also available outside the repo.
That convenience is per-machine only and is not part of what ships.
Revert to the standalone source any time:
```bash
ln -sfn ~/.claude/skills-repos/nvwb-skills/nvwb         ~/.claude/skills/nvwb
ln -sfn ~/.claude/skills-repos/nvwb-skills/nvwb-project ~/.claude/skills/nvwb-project
```
