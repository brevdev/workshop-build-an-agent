<div class="dx-hero" data-eyebrow="MODULE 02 / AGENTIC RAG" data-title="Agentic RAG Workshop" data-meta="DURATION::2-3 hrs|MODEL::Nemotron 3 Super + NeMo Retriever|GPU::Hosted API; local NIM optional"></div>

The Agentic RAG Workshop teaches you how to build intelligent Retrieval Augmented Generation (RAG) systems using NVIDIA technology and LangGraph. You'll create an **IT Help Desk Agent** - an intelligent system that can dynamically decide when and how to search knowledge bases to answer user queries. Unlike traditional RAG systems that always perform the same retrieval steps, agentic RAG gives the model control over when and how to use retrieval as a tool.

This workshop will help you understand the evolution from basic LLMs to traditional RAG to intelligent agentic RAG. Here's what you're in for:

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide is-tall"><h4>YOU WILL BUILD</h4>An <b>IT Help Desk Agent</b> that decides when and how to search a knowledge base, the web, and loadable skills to answer queries - agentic RAG, not fixed retrieval.</div>
  <div class="dx-cell"><h4>DURATION</h4><span class="dx-big">2-3 h</span>self-paced</div>
  <div class="dx-cell"><h4>BUILT WITH</h4>LangGraph + NVIDIA NeMo Retriever + FAISS</div>
  <div class="dx-cell is-wide"><h4>YOU'LL TAKE HOME</h4>A working ReAct RAG agent, a FAISS vector database, hands-on with NVIDIA embedding/reranking/chat models, plus MCP and Skills integration.</div>
</div>

## Learning Objectives

<img src="_static/robots/surfwithshorts.png" alt="Workshop Robot Character" style="float:right;max-width:300px;margin:25px;" />

By the end of this workshop, you'll know how to:
- Build vector databases with document chunking and embeddings
- Implement retrieval chains with NVIDIA NeMo Retriever
- Create ReAct agents that can decide when and how to use those chains
- Use LangGraph to orchestrate NVIDIA NIM services

<div class="dx-island dx-tutor">
  <p class="dx-island-title">WORK ALONGSIDE AN AI TUTOR</p>

This workshop ships its own tutor as **Agent Skills**. It explains this module's concepts in the workshop's own framing, gives graduated hints **without ever completing your exercises**, and helps you troubleshoot when something breaks. Open one and leave it running beside these pages:

<button onclick="launch('Claude Code', 'Workshop Assistants');"><i class="fa-solid fa-robot"></i> Claude Code</button> <button onclick="launch('Codex CLI', 'Workshop Assistants');"><i class="fa-solid fa-robot"></i> Codex CLI</button>

Ask for this module by name — `/module-2` in Claude Code, `$module-2` in Codex — or just describe what you're stuck on and the right skill loads on its own.

```text
/module-2 I'm stuck on the reranker exercise - give me a hint, not the answer
```

</div>

> Head over to [Setting up Secrets](secrets) to get started!

