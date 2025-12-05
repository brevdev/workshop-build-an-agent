# NeMo Evaluator (Optional)

<img src="_static/robots/magician.png" alt="LLM Judge" style="float:right;max-width:300px;margin:25px;" />

In the previous lessons, you manually ran evaluations using Python scripts to test your agents. This works great for development and experimentation. But what if you need to evaluate not just a few, but <i>thousands</i> of responses? 

Once you’re scoring large volumes of outputs, comparing multiple agent versions, or running evaluations on a schedule in production, you need a more robust, reproducible, and scalable workflow.

That's where **NVIDIA NeMo Evaluator**, an open source framework for evaluation at scale, comes in. NeMo Evaluator supports automated agent evaluation using academic benchmarks, custom metrics, and LLM-as-a-judge workflows, so you can measure and monitor agent performance in real-world environments.

<!-- fold:break -->

## Should You Do This Module?

This module is **optional**.

- **Do if**: You want to deploy agents to production and need automated evaluation
- **Do if**: You're curious about enterprise evaluation infrastructure
- **Skip if**: You're focused on learning core concepts and will add production tooling later

Keep reading to learn how NeMo Evaluator works.

<!-- fold:break -->

## What is NeMo Evaluator?

By now, you've designed evaluation datasets and scoring rubrics and have seen how LLMs can judge agent outputs with nuance and speed. 

NeMo Evaluator brings structure and automation to this process. It runs as an independent microservice, keeping evaluation isolated from your agent code and enabling consistent, repeatable testing at any scale.

You submit evaluation jobs to NeMo Evaluator, and it provides:

- **Scalability & Automation**: Run thousands of evaluations efficiently without manual triggering
- **Isolation & Consistency**: Microservice architecture ensures repeatable, decoupled testing
- **Error Handling**: Built-in retries, rate limiting, and monitoring for reliability
- **Result Tracking**: Store and compare evaluation results across iterations

<!-- fold:break -->

## What You'll Learn

Recall that a robust evaluation pipeline requires an agent under test, a judging mechanism, a test dataset, evaluation prompts and metrics, and analysis of results.

In this hands-on tutorial, you'll learn how to implement these components using NeMo Evaluator. You'll use the **HelpSteer2** dataset, a collection of prompts and sample agent responses, to set up an example LLM-as-a-Judge workflow.

1. **Set Up the Infrastructure** - Deploy NeMo Evaluator as a Docker microservice
2. **Prepare the Test Dataset** - Load HelpSteer2 prompt-response pairs
3. **Configure Your Judge** - Define custom metrics (helpfulness, correctness, coherence)
4. **Submit Evaluation Jobs** - Send jobs to NeMo Evaluator and monitor progress
5. **Analyze Results** - Retrieve scores and identify patterns
6. **Batch Process Efficiently** - Run evaluations on larger datasets

<!-- fold:break -->

## Get Started

<img src="_static/robots/datacenter.png" alt="Production Infrastructure" style="float:left;max-width:300px;margin:25px;" />

Ready to automate your evaluation workflows?

Open the <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/evaluator.ipynb');"><i class="fa-solid fa-flask"></i> NeMo Evaluator Tutorial</button> notebook to begin!

<!-- fold:break -->

## What's Next

You now have a comprehensive evaluation framework for your agents! In the next lesson, [Continuous Improvement](continuous_improvement.md), we'll explore:

- Systematic approaches to improving agent performance
- Advanced evaluation techniques
- Production monitoring best practices
- Building a culture of quality around AI agents
