# Introduction to Agents

<img src="_static/robots/blueprint.png" alt="VSS Robot Character" style="float:left; max-width:300px;margin:25px;" />

Welcome to the world of AI agents! In this exercise, we'll explore how agents apply Large Language Models to solve complex tasks.

<!-- fold:break -->

## What is an Agent?

Large Language Models (LLMs) have an impressive ability to generate text and recall information. On their own, however, they are limited by their training data.

Design patterns like Retrieval Augmented Generation (RAG) become popular as they are simple workflows that make LLMs more capable. Workflows are systems that use LLMs to navigate hardcoded paths. 

LLMs and Workflows are both very useful tools, but agents take things a step further.

Agents are intelligent programs that use large language models (LLMs) to decide how to accomplish tasks. They can use tools to interact with their environment and can adapt to changes.

<!-- fold:break -->

## Anatomy of an Agent

<img src="_static/robots/assembly.png" alt="Agent Blueprint" style="float:right; max-width:320px; margin:20px 0 20px 30px; border-radius:12px; box-shadow:0 2px 8px £ccc;" />

Agentic patterns can be very complex, with many important components.

However, there are four key components that are fundamental to all agents:

<ul style="margin-left:1em;">
  <li><b>MODEL:</b> An LLM that decides which tools to use and how to respond</li>
  <li><b>TOOLS:</b> Functions that let the LLM perform actions like math, database queries, or API calls</li>
  <li><b>MEMORY and STATE:</b> Information available to the LLM during and between conversations</li>
  <li><b>ROUTING:</b> The LLM will make decisions about what to do next, we need to route messages accordingly</li>
</ul>

<!-- fold:break -->

## Do It Yourself

Want to see how these components work together? 
Check out the 
<button onclick="openOrCreateFileInJupyterLab('code/intro_to_agents.ipynb');"><i class="fa-solid fa-flask"></i> Introduction to Agents</button>
notebook where you can build your first agent the hard way - from scratch!



