# Using Skills with MCP

<img src="_static/robots/magician.png" alt="Skills Magic Robot" style="float:right;max-width:300px;margin:25px;" />

Your agent now has **tools** (knowledge base + web search). Let's add **skills** — specialized expertise your agent can load on demand.

<!-- fold:break -->

## The Goal

Add two new tools:
- `list_available_skills` — See what skills exist
- `get_skill` — Load a skill for expertise

**Available Skills:**
- `code-review` — Systematic code review with checklist
- `technical-writing` — Guidelines for clear documentation

<!-- fold:break -->

## Your Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/rag_agent.py');"><i class="fa-brands fa-python"></i> code/rag_agent.py</button> and fill in these blanks in the **Skills section**:

### Exercise 6: Load a Skill

<button onclick="goToLineAndSelect('code/rag_agent.py', 'def get_skill');"><i class="fas fa-code"></i> get_skill return</button> — Return the loaded skill content.

<details>
<summary>🆘 Need some help?</summary>

```python
return load_skill(skill_name)
```

</details>

<!-- fold:break -->

### Exercise 7: List Available Skills

<button onclick="goToLineAndSelect('code/rag_agent.py', 'def list_available_skills');"><i class="fas fa-code"></i> list_available_skills return</button> — Return the list of skills.

<details>
<summary>🆘 Need some help?</summary>

```python
return list_skills()
```

</details>

<!-- fold:break -->

### Exercise 8: Initialize the LLM

<button onclick="goToLineAndSelect('code/rag_agent.py', 'llm = ');"><i class="fas fa-code"></i> llm</button> — Create the ChatNVIDIA model.

<details>
<summary>🆘 Need some help?</summary>

```python
llm = ChatNVIDIA(model=LLM_MODEL, temperature=0.6, max_tokens=4096)
```

</details>

<!-- fold:break -->

### Exercise 9: Create the Agent with ALL Tools

<button onclick="goToLineAndSelect('code/rag_agent.py', 'AGENT = ');"><i class="fas fa-code"></i> AGENT</button> — Wire up all four tools!

<details>
<summary>🆘 Need some help?</summary>

```python
AGENT = create_react_agent(
    model=llm,
    tools=[RETRIEVER_TOOL, web_search, get_skill, list_available_skills],
    prompt=SYSTEM_PROMPT,
)
```

</details>

<!-- fold:break -->

## Test Your Complete Agent

Restart your agent and try these prompts:

| Prompt | Expected Behavior |
|--------|-------------------|
| "How do I reset my password?" | Uses knowledge base [KB] |
| "What are the latest AI trends?" | Uses web search [Web] |
| "What skills do you have?" | Lists `code-review`, `technical-writing` |
| "Review this code: `def add(a,b): return a+b`" | Loads code-review skill, gives structured feedback |

<!-- fold:break -->

## Congratulations!

<img src="_static/robots/strong.png" alt="Strong Robot" style="float:right;max-width:250px;margin:25px;" />

Your agent now has:

- ✅ **RAG** — Knowledge base retrieval (Exercises 1-3)
- ✅ **MCP** — Web search (Exercises 4-5)
- ✅ **Skills** — Dynamic expertise (Exercises 6-9)

All in ONE agent! Check `rag_agent.answers.py` for the complete solution.
