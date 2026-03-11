# Blocky Bits Integration Notes

There's a React hook (`src/hooks/useBlockyBits.ts`) that hits `GET /blocks/workspace` through a Vite proxy (we proxy `/blocks/*` → `localhost:1234`). It parses your response and maps block names to our internal IDs.

Here are the current mappings — **these will need updating once you finalize your block names**:

```typescript
// Model blocks → which LLM to use
'NVIDIA'  → 'nemotron'   // nvidia/nemotron-3-super-120b-a12b
'Meta'    → 'llama'      // meta/llama-3.3-70b-instruct
'Claude'  → 'claude'     // fallback to llama for now
'Google'  → 'deepseek'   // deepseek-ai/deepseek-r1-0528

// Skill blocks → which tools to give the agent
'Google'  → 'websearch'  // Tavily web search
'weather' → 'websearch'  // also maps to web search
```

Our tool IDs that you can map to:
- `websearch` — internet search
- `fileio` — read/write/edit files
- `execute` — run shell commands
- `superpowers` — TDD methodology (skill, not a tool)
- `cudf` — NVIDIA RAPIDS cuDF knowledge (skill, not a tool)

If you name your blocks to match these IDs directly (like a block called "websearch"), the mapping becomes trivial. Otherwise just let me know what names you're using and I'll update the map.

## Running it

1. Start your blocky-bits on port 1234:
   ```
   cd blocky-bits
   uv run blocky-bits start --port 1234
   ```

2. Start our backend on port 8000:
   ```
   cd DeepAgentsDemo/backend
   source .venv/bin/activate
   uvicorn server:app --host 127.0.0.1 --port 8000 --reload
   ```

3. Start our frontend on port 5173:
   ```
   cd DeepAgentsDemo
   npm run dev
   ```

4. Go to `http://localhost:5173` and click the **🧊 Visual** toggle in the top right

5. Use your debug UI at `http://localhost:1234/debug` to simulate placing blocks

When a model block appears, our soul picker auto-selects and moves to the builder. When skill blocks appear, they auto-add to the agent.

## Files i changed

- `src/hooks/useBlockyBits.ts` — the polling hook (this is the main thing)
- `src/App.tsx` — wired the hook in, added the mode toggle
- `src/App.css` — styled the toggle and connection indicator
- `vite.config.ts` — added proxy `/blocks` → `localhost:1234`

Nothing else changed. The backend, agent builder, chat, and all existing functionality still works the same in Website Mode.
