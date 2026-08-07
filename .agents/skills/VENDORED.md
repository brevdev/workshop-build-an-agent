# Codex skill tree (`.agents/skills/`)

This directory is the **Codex** copy of the workshop's Agent Skills. Codex auto-discovers
project skills from `<repo>/.agents/skills/` (verified with `codex debug prompt-input`),
the exact parallel to how Claude Code auto-discovers `<repo>/.claude/skills/`. Shipping the
skills in-repo means they load automatically in any clone — no separate install.

## Generated from `.claude/skills/` — do not hand-edit synced files

The canonical source of truth is **`.claude/skills/`**. This tree is regenerated from it by:

```bash
bash .agents/sync-codex-skills.sh          # regenerate
bash .agents/sync-codex-skills.sh --check  # verify in sync (non-zero exit on drift)
```

The sync applies a small set of **surgical, survey-safe** substitutions so the Codex copy
reads naturally for a Codex user (invocation phrases like "run claude" → "run codex", the
path `.claude/skills/` → `.agents/skills/`, "inner Claude" → "inner agent"). It deliberately
does **not** touch the
educational content in Module 7 / the glossary that *names* "Claude Code" and "Codex" as
objects of study, nor the `claude`→llama model-alias references in Module 5.

**Workflow:** edit `.claude/skills/…`, then re-run the sync. Editing files here directly will
be overwritten on the next sync — except the hand-authored files below.

## Hand-authored Codex files (preserved by the sync script)

These are genuine Codex rewrites, not mechanical substitutions; the sync script lists them in
`HAND_AUTHORED` and never overwrites them:

| File | Why it's hand-authored |
|---|---|
| `nvwb/references/codex-in-container.md` | Codex rewrite of the Claude `claude-in-container.md` (Codex install, `codex login`, `~/.codex/` auth persistence). |
| `nvwb-project/references/agent-bridge.md` | Adds a Codex hooks-wiring section alongside the Claude/Cursor ones. |
| `VENDORED.md` | This file. |

The cross-harness hook scripts under `nvwb-project/hooks/` (`inner-agent-*.sh`,
`outer-agent-*.sh`) emit the `hookSpecificOutput`/`PreToolUse`/`permissionDecision` wire
format that **both** Claude Code and Codex consume, so they are shared (synced), not
duplicated. The `cursor-*.sh` variants cover Cursor's different schema. See
`nvwb-project/references/agent-bridge.md` for how to register them in each harness.

## Provenance of the vendored `nvwb/` and `nvwb-project/` skills

These two originate from the upstream nvwb-skills repo (not authored for this workshop):

- Upstream: https://github.com/nv-twhitehouse/nvwb-skills
- Vendored at commit: `8f6b85b` ("Add common-context, agent sandbox hooks, and env var protection")
- Vendored into `.claude/skills/` on: 2026-06-25, then synced here.

To re-sync with upstream: update `.claude/skills/nvwb` and `.claude/skills/nvwb-project` from
upstream (see `.claude/skills/VENDORED.md`), then run `bash .agents/sync-codex-skills.sh`.
