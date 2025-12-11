# Creating Evaluation Datasets

<img src="_static/robots/operator.png" alt="Dataset Design" style="float:right;max-width:300px;margin:25px;" />

You've learned about the metrics you'll use to evaluate your agents. But how do you measure those metrics in practice? 

To produce high-quality, meaningful evaluation metrics, you need a well-designed evaluation dataset. In this lesson, you'll learn how to create evaluation datasets for the two agents you've built:

- **IT Help Desk RAG Agent** (Module 2)
- **Report Generation Agent** (Module 1)

<!-- fold:break -->

## Dataset Design for Your Agents

Evaluation datasets work best when they align with the following principles: 

1. **Cover Diverse Scenarios**: Include common cases, edge cases, and failure modes
2. **Include Ground Truth**: Where possible, provide correct answers for comparison
3. **Represent Real Usage**: Base test cases on actual user interactions
4. **Start Small**: Begin with 20-30 high-quality examples and expand over time
5. **Version Control**: Track your datasets alongside your code

In addition to these general principles, you'll need to make sure your data is tailored to your particular evaluation use-case. Different agent tasks, and different metrics, require different types of evaluation data.

To understand dataset design, let's look at what you'll need to evaluate the agents you've built.

<!-- fold:break -->

### Dataset for the IT Help Desk RAG Agent (Module 2)

For the IT Help Desk RAG agent from Module 2, each evaluation test case should include:

- **Question**: The user's query (common IT help desk questions)
- **Ground Truth Answer**: The expected response
- **Expected Context Keywords**: Keywords that should appear in retrieved documents
- **Category**: The type of question (password_management, vpn_access, network_issues, etc.)

In your evaluation pipeline, you'll query the agent with your user question. The agent's generated response can then be compared to the test data, to evaluate multiple dimensions of your agent's performance.

<todo>

We've provided a starter dataset with examples for you. Check out the <button onclick="openOrCreateFileInJupyterLab('data/evaluation/rag_agent_test_cases.json');"><i class="fa-brands fa-python"></i> RAG Agent Evaluation Dataset</button> to see the structure.

### Dataset for the Report Generation Agent (Module 1)

For the Report Generation agent from Module 1, each evaluation test case should include:
- **Topic**: The report subject
- **Expected Sections**: Sections that should appear in the report
- **Quality Criteria**: Custom metrics that define what makes a "good" report on this topic

Like for the IT Help Desk agent, in your evaluation pipeline, you'll query the Report Generation agent with a topic. However, note that the Report Generation dataset does not contain a complete ground truth answer. The length and variability of reports makes this form of evaluation impractical. 

Instead, the test cases include expected section names and quality criteria, which we'll use to evaluate each report's structure and content. You'll dive into using these quality criteria in the next lesson, [Running Evaluations](running_evaluations.md).

Check out the starter <button onclick="openOrCreateFileInJupyterLab('data/evaluation/report_agent_test_cases.json');"><i class="fa-brands fa-python"></i> Report Agent Evaluation Dataset</button> to see the structure.

<!-- fold:break -->

## How to Create Your Evaluation Datasets

Now that you understand what evaluation datasets look like for each agent, let's explore strategies for creating them.

### Dataset Creation Strategies

### Strategy 1: Real-World Data Collection

The first strategy is to use existing, real-world data. This approach is often considered the "gold standard" for realism because it captures authentic user experiences and needs. You can either collect this data yourself or leverage existing datasets from online repositories like HuggingFace. 

However, real-world data comes with trade-offs. Manual collection requires substantial human labor and time. Privacy concerns may limit what data you can use, and quality issues, like biased or inappropriate content, can compromise your evaluation. Further, real-world data may simply not exist for your specific use case, particularly for complex or niche applications.

**Use When**: <todo>

### Strategy 2: Synthetic Data Generation

The second strategy is to generate synthetic data using an LLM. This type of data is highly versatile: it enables developers to rapidly create large datasets, control diversity and coverage, and support use cases where real-world data is difficult or impossible to obtain.

However, synthetic data has its weaknesses as well. It typically requires careful human validation before use, and it may fail to accurately capture real-world behaviors, edge cases, or distributions, which can reduce the reliability of any evaluations that rely on it.

**Use When**: <todo>

### Strategy 3: Hybrid Approach

A hybrid approach combines real-world and synthetic data to leverage the strengths of both while mitigating their weaknesses. It allows developers to ground systems in realistic data, then augment coverage with synthetic examples.

<!-- fold:break -->

## Generate Evaluation Data for Your Agents

Now it's time to create evaluation datasets for the agents you built! We'll use **Synthetic Data Generation (SDG)** with **NVIDIA NeMo Data Designer**, an open source tool for generating high-quality synthetic data, to quickly create test cases.

Start with generating data for your RAG agent from Module 2 to get familiar with SDG concepts:
<button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/generate_rag_eval_dataset.ipynb');"><i class="fa-solid fa-flask"></i> RAG Evaluation Data Notebook</button>

Next, generate data for your Report Generation agent from Module 1: 
<button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/generate_report_eval_dataset.ipynb');"><i class="fa-solid fa-flask"></i> Report Generation Evaluation Data Notebook</button>

<!-- fold:break -->

## Using Pre-Made Datasets

If you prefer to start with pre-made datasets, we've provided starter sets for both agents:

- <button onclick="openOrCreateFileInJupyterLab('data/evaluation/rag_agent_test_cases.json');"><i class="fa-brands fa-python"></i> RAG Agent Test Cases</button> - 12 IT help desk questions across common categories
- <button onclick="openOrCreateFileInJupyterLab('data/evaluation/report_agent_test_cases.json');"><i class="fa-brands fa-python"></i> Report Agent Test Cases</button> - 6 report topics with quality criteria

<!-- fold:break -->

## What's Next

Once you have your evaluation datasets ready, you're prepared to run comprehensive evaluations! 

In the next lesson, [Running Evaluations](running_evaluations.md), you'll:
- Load your evaluation datasets
- Run your agents on test cases
- Use LLM-as-a-Judge to score responses
- Analyze results and identify improvement areas

