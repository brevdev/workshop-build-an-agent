# The Agent-Bridge Pattern

The agent-bridge is a file-based communication channel between an AI agent running **inside the container** (inner agent) and an AI agent or human running on the **local machine** (outer agent). It exists because the inner agent cannot run `nvwb` commands — those only work on the local machine.

## Setup

Create the bridge directory in the project root:

```bash
mkdir -p /project/agent-bridge/common-context/
```

Add to `.gitignore` — bridge messages are transient and should not be committed:

```
agent-bridge/
```

The directory appears as `/project/agent-bridge/` inside the container and as `<project-path>/agent-bridge/` on the local machine (or via SSH for remote contexts).

The resulting structure:

```
agent-bridge/
├── inner.md                  ← inner agent writes requests here
├── outer.md                  ← outer agent writes responses here
├── common-context/
│   ├── context.md            ← shared task state (both agents read/write)
│   ├── .sensitive-vars       ← sensitive env var names (optional)
│   └── [nvwb references]     ← pre-populated by the user
└── hooks/                    ← sandbox hook scripts (optional)
```

---

## How It Works

**Inner agent** writes a request to `/project/agent-bridge/inner.md` whenever it needs a host-side action.

**Outer agent** (Claude on the local machine, or the user) reads the request, takes action, and writes results to `/project/agent-bridge/outer.md`.

**Inner agent** reads the response and continues.

---

## Common Context

The `common-context/` subdirectory holds shared state that both agents can read. This avoids repeating task context in every `inner.md` / `outer.md` exchange.

### `context.md` — Shared task state

A living scratchpad for the current task. Both agents read it before acting; either agent can update it.

Contents:
- What is currently being worked on
- Progress so far
- Blockers or open questions
- Key decisions already made

#### Template

```markdown
## Current Task

[What's being worked on and the goal]

## Progress

- [Step completed]
- [Step completed]
- [Step in progress...]

## Blockers

- [Anything blocking progress]

## Decisions

- [Key decisions made during this task]
```

### nvwb skill references

The user pre-populates `common-context/` with nvwb skill reference files (CLI reference, spec reference, workflows, etc.) so the outer agent has working knowledge of Workbench without needing a separate skills installation on the local machine.

---

## Rules

Both inner and outer agents must follow these rules:

1. **Do not copy files into or out of `agent-bridge/`.** The bridge is a communication channel, not a file staging area. Do not place project files, scripts, or other artifacts in this directory.
2. **The content of `inner.md` and `outer.md` is unrestricted.** Include whatever text is useful — logs, command output, code snippets, diagnostics. The restriction is on the directory, not the messages.
3. **Read `common-context/` before acting.** Check `context.md` for current task state and consult the nvwb references when needed.

---

## Sandboxing with Hooks (Optional)

The rules above are documentation — agents follow them but nothing enforces them. Claude Code **hooks** can enforce these constraints at the tool level, blocking disallowed actions before they execute.

The skills repo ships hook scripts at `nvwb-project/hooks/`. Copy them into your project's `agent-bridge/hooks/` directory:

```bash
cp -r ~/.claude/skills/nvwb-project/hooks/ <project-path>/agent-bridge/hooks/
```

### What the hooks enforce

**Inner agent** (in the container):
- Blocks `nvwb` commands with a message redirecting to the bridge
- Blocks environment variable dumps (`env`, `printenv`, `set`, `export -p`)
- Scrubs sensitive variables from all shell commands (wraps with `env -u`)
- Blocks reads of sensitive files (`.env`, `~/.claude.json`, credential files)
- Restricts bridge writes to `inner.md` and `common-context/context.md`

**Outer agent** (on the local machine):
- Only allows `nvwb`, `ssh`, read-only commands (`ls`, `cat`, `git status`, etc.)
- Blocks environment variable dumps
- Scrubs sensitive variables from allowed commands
- Restricts file writes to `outer.md` and `common-context/context.md`

### Sensitive variable protection

Hooks scrub sensitive environment variables from Claude's shell commands (wrapping them with `env -u`). Variable names are collected from three sources, in priority order:

1. **`execution.secrets` in `.project/spec.yaml`** — the authoritative source. Any variable declared as a secret is automatically scrubbed.
2. **`agent-bridge/common-context/.sensitive-vars`** — additional project-specific overrides (one name per line, `#` comments). Use this for variables not declared in spec.yaml.
3. **Pattern matching** — variable names in the current environment matching `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL`, `AUTH`, `PRIVATE` are caught automatically.

Example `.sensitive-vars` (only needed for variables not already in spec.yaml secrets):

```
# Additional sensitive variables
DATABASE_URL
CUSTOM_AUTH_HEADER
```

### Wiring up the hooks

#### Claude Code

Add to `.claude/settings.json` (or `.claude/settings.local.json` to keep it out of Git).

**Inner agent** (Claude Code in the container):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "/project/agent-bridge/hooks/inner-agent-bash.sh"}]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "/project/agent-bridge/hooks/inner-agent-files.sh"}]
      },
      {
        "matcher": "Read",
        "hooks": [{"type": "command", "command": "/project/agent-bridge/hooks/inner-agent-read.sh"}]
      }
    ]
  }
}
```

**Outer agent** (Claude Code on the local machine):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/agent-bridge/hooks/outer-agent-bash.sh"}]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/agent-bridge/hooks/outer-agent-files.sh"}]
      }
    ]
  }
}
```

#### Cursor

Add to `.cursor/hooks.json` in the project root.

**Inner agent** (Cursor in the container):

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "matcher": "Shell",
        "command": ".cursor/../agent-bridge/hooks/cursor-inner-shell.sh"
      },
      {
        "matcher": "Write",
        "command": ".cursor/../agent-bridge/hooks/cursor-inner-files.sh"
      }
    ],
    "beforeReadFile": [
      {
        "command": ".cursor/../agent-bridge/hooks/cursor-inner-read.sh"
      }
    ]
  }
}
```

> **Note**: Cursor's `beforeReadFile` is fail-closed — if the hook script fails (e.g. missing `jq`), the read is blocked. Ensure `jq` is installed in the container.

### Testing

Run the included test suite from inside the hooks directory:

```bash
cd <project-path>/agent-bridge/hooks/
./test-hooks.sh
```

Requires `jq` and `bash`. Tests cover both Claude Code and Cursor hook scripts.

---

## Bootstrapping the Outer Agent

The outer agent (on the local machine) needs to know the bridge exists. Add a `CLAUDE.md` file in the project root that points it at `agent-bridge/`:

```markdown
## Agent Bridge

This project uses an agent-bridge for communication between the inner agent
(in the container) and the outer agent (on this machine).

- Check `agent-bridge/inner.md` for requests from the inner agent
- Write responses to `agent-bridge/outer.md`
- Read `agent-bridge/common-context/context.md` for current task state
- Read reference files in `agent-bridge/common-context/` for Workbench CLI knowledge
- Do NOT copy files into or out of `agent-bridge/` — it is a communication channel, not a file staging area

## Sandbox

You are sandboxed. Hooks enforce the following constraints:
- You may only run `nvwb`, `ssh`, and read-only commands (`ls`, `cat`, `git status`, etc.)
- You may only write to `agent-bridge/outer.md` and `agent-bridge/common-context/context.md`
- Sensitive environment variables are scrubbed from your shell commands
- You cannot read or modify hook configuration or settings files
- Do not attempt to circumvent these restrictions
```

---

## What to Put in `inner.md`

Write in plain prose. Include:

1. **What you changed** — file paths, what was modified and why
2. **What you need done** — the specific `nvwb` command, compose restart, rebuild, etc.
3. **What to report back** — logs, curl output, exit codes, specific lines to look for

The more context you give, the better outer Claude can act without needing to ask follow-up questions.

### Template

```markdown
## Request

I've made the following changes:
- [file] — [what changed and why]
- [file] — [what changed and why]

Please run:
```
[command or commands]
```

Report back:
- The full output / any errors
- [specific thing to check, e.g. `curl http://api:8080/health`]
- Whether [expected outcome] is true
```

### Example

```markdown
## Request

I've updated `/project/code/server.py` to add a `/health` endpoint that
returns `{"status": "ok", "version": "1.2.0"}`.

Please run:
```
nvwb compose down && nvwb compose up
```

Report back:
- Full compose startup logs
- Output of `curl -s http://api:8080/health`
- Whether the service came up cleanly (no restart loops)
```

---

## What to Put in `outer.md`

Write in plain prose. Include:

1. **What you ran** — confirm the commands executed
2. **Output** — paste relevant logs, command output, errors
3. **Status** — did it succeed? Any warnings?
4. **Results of any tests** — curl output, health check results

### Template

```markdown
## Response

Ran: `[command]`

Output:
```
[paste output]
```

[Additional results, e.g. curl output]

Status: [succeeded / failed / partial — explain]
```

### Example

```markdown
## Response

Ran: `nvwb compose down && nvwb compose up`

Compose came up cleanly. No errors or restart loops in the logs.

curl output:
```
{"status": "ok", "version": "1.2.0"}
```

Status: succeeded.
```

---

## Claude Code vs Cursor

### Claude Code (inner agent)

The `nvwb-project` skill activates automatically when `.project/spec.yaml` is detected. Claude knows about the bridge natively and will write to `inner.md` autonomously whenever it needs a host-side action. No additional setup required.

### Cursor (inner agent)

Cursor has no built-in awareness of the bridge. It relies on `.cursor/rules/` in the project repo for context.

**Workbench handles this automatically.** When Cursor is added as a project app, Workbench creates `.cursor/rules/ai-workbench/` directly in the project repo (workspace root is `/project/`). The `agent-bridge.mdc` rule in that set instructs Cursor to write to the bridge for any host-side action. Without it, Cursor will attempt to run `nvwb` commands directly (which will fail) or tell the user it cannot act.

If the rules are missing from a project, copy them from the skills repo:

```bash
cp -r ~/.claude/skills/cursor-rules/ai-workbench /project/.cursor/rules/
```

---

## Outer Agent Access

### Local context

Bridge files are directly accessible on the local filesystem at `<project-path>/agent-bridge/`. Outer Claude can read and write them natively.

### Remote context

When the project is running in a remote context, the bridge files live on the remote machine. The context name (from `nvwb list contexts`) is the SSH alias — Workbench adds a matching entry to `~/.ssh/config`:

```bash
# Read a request
ssh <context-name> cat /path/to/project/agent-bridge/inner.md

# Write a response
ssh <context-name> "cat > /path/to/project/agent-bridge/outer.md" << 'EOF'
## Response
...
EOF
```
