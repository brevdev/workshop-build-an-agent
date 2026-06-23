<div class="dx-hero" data-eyebrow="MODULE 03 / 03 - DATASETS" data-title="Creating Evaluation Datasets" data-meta="DURATION::2-3 hrs|MODEL::Nemotron 3 Super (LLM-judge)|GPU::Hosted API endpoint"></div>

<img src="_static/robots/operator.png" alt="Dataset Design" style="float:right;max-width:300px;margin:25px;" />

You've learned about the metrics you'll use to evaluate your agents. But how do you measure those metrics in practice? 

To produce high-quality, meaningful evaluation metrics, you need a well-designed evaluation dataset. In this lesson, you'll learn how to create evaluation datasets for the two agents you built earlier in this course:

- **IT Help Desk RAG Agent** (Module 2)
- **Report Generation Agent** (Module 1)

We'll start with the RAG agent since it has a simpler evaluation structure, then move to the more open-ended Report Generation agent.

<!-- fold:break -->

## Dataset Design for Your Agents

<div class="dx-island dx-reveal">
  <p class="dx-island-title">WHAT MAKES A GOOD EVALUATION DATASET</p>
  <ul>
    <li><span class="dx-chip">COVER DIVERSE SCENARIOS</span> common cases, edge cases, and failure modes.</li>
    <li><span class="dx-chip">INCLUDE GROUND TRUTH</span> provide correct answers for comparison where possible.</li>
    <li><span class="dx-chip">REPRESENT REAL USAGE</span> base test cases on actual user interactions.</li>
    <li><span class="dx-chip">START SMALL</span> begin with a few high-quality examples and expand over time.</li>
    <li><span class="dx-chip">VERSION CONTROL</span> track datasets alongside your code.</li>
  </ul>
</div>

In addition to these general principles, you'll need to make sure your data is tailored to your particular evaluation use case. Different agent tasks require different types of evaluation data.

To understand dataset design, let's look at what you'll need to evaluate the agents you've built. Let's explore how to craft different test datasets depending on the agent and task we want to evaluate. 

<!-- fold:break -->

We'll create one dataset per agent - and their shapes differ because the agents differ:

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>IT HELP DESK RAG AGENT &middot; MODULE 2</h4>Each test case pairs a <b>Question</b> with a <b>Ground Truth Answer</b>, <b>Expected Context Keywords</b>, and a <b>Category</b> (password_management, vpn_access...). Answers are brief and objectively correct, so we include ground truth for direct comparison.<br><button onclick="openOrCreateFileInJupyterLab('data/evaluation/rag_agent_test_cases.json');"><i class="fa-brands fa-python"></i> RAG Agent Evaluation Dataset</button></div>
  <div class="dx-cell is-wide"><h4>REPORT GENERATION AGENT &middot; MODULE 1</h4>Each test case carries a <b>Topic</b>, <b>Expected Sections</b>, and <b>Quality Criteria</b>. Reports are long and variable, so there is no single ground-truth answer - we score structure and content instead (see <a href="running_evaluations.md">Running Evaluations</a>).<br><button onclick="openOrCreateFileInJupyterLab('data/evaluation/report_agent_test_cases.json');"><i class="fa-brands fa-python"></i> Report Agent Evaluation Dataset</button></div>
</div>

<!-- fold:break -->

## How to Create Your Evaluation Datasets

<img src="_static/robots/study.png" alt="Building Datasets" style="float:right;max-width:300px;margin:25px;" />

Now that you understand what evaluation datasets look like for each agent, let's explore strategies for creating them.

<!-- fold:break -->

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>REAL-WORLD DATA</h4>The realism gold standard - authentic user needs. But manual collection is slow, raises privacy concerns, and may not exist for niche use cases. <i>Use when you already have user logs or deployed usage.</i></div>
  <div class="dx-cell"><h4>SYNTHETIC (SDG)</h4>Fast and versatile - generate large, controllable datasets on demand. But it needs human validation and may miss real edge cases. <i>Use when you lack real data or need broad coverage fast.</i></div>
  <div class="dx-cell"><h4>HYBRID</h4>Ground in real data, then augment coverage with synthetic examples - the strengths of both. <i>Use when you have some real data but need more.</i></div>
</div>

<!-- fold:break -->

## Generate Evaluation Data for Your Agents

Now it's time to create evaluation datasets for the agents you built!

For this workshop, we'll use **Synthetic Data Generation** with **NVIDIA NeMo Data Designer**, an open source tool for generating high-quality synthetic data. This approach is ideal for getting started with agent evaluation and learning the fundamentals.

<div class="dx-island dx-reveal">
  <p class="dx-island-title">GENERATE YOUR DATASETS</p>
  <p>Follow the first notebook to generate data for your RAG agent from Module 2 and get familiar with SDG concepts:</p>
  <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/generate_rag_eval_dataset.ipynb');"><i class="fa-solid fa-flask"></i> RAG Evaluation Data Notebook</button>
  <p>Next, generate data for your Report Generation agent from Module 1:</p>
  <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/generate_report_eval_dataset.ipynb');"><i class="fa-solid fa-flask"></i> Report Generation Evaluation Data Notebook</button>
</div>

<details>
<summary>💡 NEED SOME HELP?</summary>

We recommend generating your own datasets using the notebooks above to get hands-on experience with the synthetic data generation process. However, if you're running into issues or want to move ahead quickly, we've provided starter datasets you can use:

- <button onclick="openOrCreateFileInJupyterLab('data/evaluation/rag_agent_test_cases.json');"><i class="fa-brands fa-python"></i> RAG Agent Test Cases</button> - 12 IT help desk questions across common categories
- <button onclick="openOrCreateFileInJupyterLab('data/evaluation/report_agent_test_cases.json');"><i class="fa-brands fa-python"></i> Report Agent Test Cases</button> - 6 report topics with quality criteria

These pre-made datasets can also serve as reference examples when you create your own.

</details>

<!-- fold:break -->

<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">You use an LLM to synthetically generate 500 evaluation test cases in minutes. What matters most before trusting evaluations built on them?</p>
  <button class="dx-quiz-opt" data-right data-fb="Right. The page's key caution: synthetic data requires careful human validation and may not capture real distributions or edge cases. Speed is its strength; unverified realism is its risk.">Have a human validate a sample - synthetic data can miss real edge cases and inherit the generator's biases</button>
  <button class="dx-quiz-opt" data-fb="This is the trap. Synthetic data is fast and controllable, but using it unverified means your eval may not reflect real user behavior or edge cases.">Nothing - data from a strong LLM is ready to use as-is</button>
  <button class="dx-quiz-opt" data-fb="Too far. Real-world data is the realism gold standard, but it is slow, privacy-constrained, and may not exist for your use case. The hybrid approach combines both on purpose.">Discard it - only real-world data is ever trustworthy</button>
  <button class="dx-quiz-opt" data-fb="More volume does not fix unverified quality. A larger unvalidated set just scales the same blind spots.">Generate 500 more to increase coverage</button>
</div>

<!-- fold:break -->

## What's Next

<img src="_static/robots/typewriter.png" alt="Next Steps" style="float:right;max-width:250px;margin:25px;" />

Once you have your evaluation datasets ready, you're prepared to run comprehensive evaluations! 

In the next lesson, [Running Evaluations](running_evaluations.md), you'll:
- Load your evaluation datasets
- Run your agents on test cases
- Use LLM-as-a-Judge to score responses
- Analyze results and identify improvement areas

