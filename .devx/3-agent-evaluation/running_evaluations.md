# Running Evaluations

<img src="_static/robots/blueprint.png" alt="Running Evaluations" style="float:right;max-width:300px;margin:25px;" />

It's time to put everything together and run comprehensive evaluations on your agents! In this hands-on lesson, you'll build evaluation pipelines for both the RAG agent from Module 2 and the report generation agent from Module 1.

<!-- fold:break -->

## Prerequisites

Before starting, ensure you have:

**Evaluation datasets ready** - You should have created or reviewed test datasets from the previous lesson ([Creating Evaluation Datasets](evaluation_data.md)). You can use:
- Your own generated datasets from the `generate_rag_eval_dataset.ipynb` and `generate_report_eval_dataset.ipynb` notebooks
- The pre-made datasets: `rag_agent_test_cases.json` and `report_agent_test_cases.json`

**Agents built** - Your RAG agent from Module 2 and Report Generation agent from Module 1 should be built and functional. 
- If you have not yet completed those modules, paste the contents of the ``code/2-agentic-rag/rag_agent.answers.py`` answer key into ``code/2-agentic-rag/rag_agent.py``. 

**Metrics selected** - You've learned about evaluation metrics and LLM-as-a-Judge techniques in the previous sections of this module. 

Now let's evaluate!

<!-- fold:break -->

## Evaluation Architecture

A robust evaluation pipeline consists of several key components:

1. **Agent Under Test**: The agent you're evaluating
2. **Judging Mechanism**: The LLM, human, or other mechanism that will judge the agent
3. **Test Dataset**: Collection of test cases with inputs and optional ground truth
4. **Evaluation Prompts and Metrics**: Instructions on how to score agent outputs
5. **Analysis of Results**: Interpret results for areas of improvement

Let's start by crafting effective evaluation prompts!

<!-- fold:break -->

<img src="_static/robots/typewriter.png" alt="Crafting Prompts" style="float:right;max-width:300px;margin:25px;" />

## Designing Evaluation Prompts

The quality of an agent evaluation pipeline depends not only on your test data, but also on your evaluation prompts. Consider the following key design principles when crafting evaluation prompts:

<details>
<summary>1. Be Specific About Criteria - Expand me!</summary>

Clear and specific prompts result in precise and objective responses from LLMs. When possible, ask for empirical and quantifiable scores. 

Additionally, consider requesting the model to explain its justification for each score to get more detailed evaluation information.

**Ineffective example:**
```
Is this a good answer?
```

**Effective example:**
```
Evaluate this answer on the following criteria:
1. Relevance: Does it directly address the question?
2. Accuracy: Are all factual claims correct?
3. Completeness: Does it cover all aspects of the question?
4. Clarity: Is it easy to understand?
```

</details>

<details>
<summary>2. Provide Context - Expand me!</summary>

Include all relevant information the judge needs:
- The original question or task
- The agent's output
- Retrieved context (for RAG systems)
- Ground truth answer (if available)

</details>

<details>
<summary>3. Request Structured Output - Expand me!</summary>

LLMs tend to provide better, more actionable output when prompted to generate responses in a structured format like JSON.

```
For each criterion, provide:
- Score (1-5)
- Explanation (1-2 sentences)

Format your response as JSON:
{
  "relevance": {"score": 4, "explanation": "..."},
  "accuracy": {"score": 5, "explanation": "..."}
}
```

</details>

<details>
<summary>4. Include Examples - Expand me!</summary>

Few-shot examples can help the judge understand your standards:

```
Example of a score 5 for relevance:
Question: "How do I reset my password?"
Answer: "To reset your password, visit portal.company.com/reset..."
Explanation: Directly answers the question with specific steps.

Example of a score 2 for relevance:
Question: "How do I reset my password?"
Answer: "Passwords are important for security..."
Explanation: Discusses passwords but doesn't answer the question.
```

</details>

<!-- fold:break -->

Let’s take a look at some example evaluation prompt templates in <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/evaluation_framework.py');"><i class="fa-brands fa-python"></i> evaluation_framework.py </button> so you can see these principles in action in our evaluation pipeline.

### Exercise

**The faithfulness metric prompt in this file is currently incomplete!** Under the <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluation_framework.py', 'TODO: ...');"><i class="fas fa-code"></i> FAITHFULNESS_PROMPT </button>, complete the FAITHFULNESS_PROMPT.

Your task is to complete the prompt by briefly defining each “faithfulness” score level, giving the judge model clearer guidance on when to assign each score. 

Once you're finished, save the file and compare your answer to the solution in the dropdown below.

<details>
<summary>🆘 Need some help?</summary>

```
Rate faithfulness on a scale of 1-5:
- 5: All claims fully supported by context
- 4: Most claims supported, minor unsupported details
- 3: Some claims supported, some unsupported
- 2: Few claims supported
- 1: Most claims unsupported or contradicted
```

</details>

<!-- fold:break -->

Now that we have made our evaluation prompts robust, we can leverage these in addition to the evaluation datasets we created in the last section to evaluate agents! 

> Before proceeding, ensure ``code/2-agentic-rag/rag_agent.py`` has been completed. Need help? Check out the <button onclick="openOrCreateFileInJupyterLab('code/2-agentic-rag/rag_agent.answers.py');"><i class="fa-solid fa-flask"></i> RAG Agent Answer Key</button>. 

## Evaluating the RAG Agent

<img src="_static/robots/datacenter.png" alt="RAG Evaluation" style="float:right;max-width:300px;margin:25px;" />

Let's start by evaluating the IT Help Desk agent from Module 2. Open the <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/evaluate_rag_agent.ipynb');"><i class="fa-solid fa-flask"></i> RAG Agent Evaluation</button> notebook.

### Load the Test Dataset

Load your evaluation dataset - either the one you generated in the previous lesson or the pre-made dataset provided. 

The dataset should be located at `data/evaluation/rag_agent_test_cases.json` (or use your custom-generated file).

Load the dataset under the <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', 'test_dataset =');"><i class="fas fa-code"></i> Load Test Dataset</button> section.

<!-- fold:break -->

### Run the Agent on Test Cases

Let's run the IT Help Desk agent on our test dataset's questions.

For each test case, we'll:
1. Send the question to the agent
2. Capture the response
3. Record which contexts were retrieved
4. Store the results for evaluation

Execute the cell under <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '## Run Agent on Test Cases');"><i class="fas fa-code"></i> Run Agent on Test Cases</button>.

This may take a few minutes as the agent processes each question.

<!-- fold:break -->

Once this completes, we can use the results to evaluate the agent's responses in comparison to the expected retrieved contexts and ground truth answers in our test dataset.

Run <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '## Evaluate with LLM-as-a-Judge');"><i class="fas fa-code"></i> Evaluate with LLM-as-a-Judge</button> to evaluate each response.

Let's get used to what it means to use an LLM as a judge for agent evaluation. For this first pass, we'll evaluate these qualities: 
1. **Faithfulness**: Whether responses are grounded in the retrieved context
2. **Relevancy**: Whether responses address the user's question
3. **Helpfulness**: Whether responses contain actionable and useful advice

This may take a few minutes as the judge processes each response.

<!-- fold:break -->

### Compute RAGAS Metrics

Custom metrics let you evaluate criteria specific to your use case. But are there industry-standard frameworks?

**RAGAS** is a popular open-source framework for evaluating RAG applications, providing built-in metrics for agentic pipelines and RAG systems.

Let's explore and evaluate the agent's performance using RAGAS metrics. We'll use the ``ragas`` python library to compute:

- **Context Precision**: Are retrieved documents relevant?
- **Context Recall**: Did we retrieve all necessary information?
- **Faithfulness**: Is the answer grounded in the context?
- **Answer Relevancy**: Does the answer address the question?

Run the evaluation at <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '## Compute RAGAS Metrics');"><i class="fas fa-code"></i> Compute RAGAS Metrics</button>.

<!-- fold:break -->

### Judge Calibration Check

Before fully trusting our LLM judge scores, let's perform a quick calibration check. We'll review a small sample of responses side-by-side with the judge's scores to verify alignment with human judgment.

This is a critical step! If the judge mechanism we use systematically disagrees with human intuition, our entire evaluation pipeline can become unreliable. 

Run the cell under at <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '## Judge Calibration Check');"><i class="fas fa-code"></i> Judge Calibration Check</button>. Take a moment to review these and consider: Do you agree with the judge's scores?

<!-- fold:break -->

### Analyze Results

<img src="_static/robots/debug.png" alt="Analyzing Results" style="float:right;max-width:300px;margin:25px;" />

Let's dig into the evaluation results to understand how well your RAG agent is performing.

First, let's review the mean scores across all test cases. Run <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '## Analyze Results');"><i class="fas fa-code"></i> Analyze Results </button> to view a nicely formatted overview of the evaluation results.

Check the overall results. These scores range from 0-1, where 1 represents "perfect" performance. A score of 0.8+ is generally considered "good". How well did your agent perform in each category?

Next, check the statistical distribution to understand:
- How consistent is the agent's performance?
- Are there outliers (very high or very low scores)?
- What's the variance across test cases?

Finally, run <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '## Performance by Category');"><i class="fas fa-code"></i> Performance by Category </button> to break down scores by question type.

View the results. Which categories does the agent handle well? Which categories need improvement?

**Common Failure Patterns**: Look for patterns in low-scoring responses:
- Are certain topics consistently problematic?
- Does the agent struggle with specific question types (e.g., troubleshooting vs. how-to)?
- Review the explanations from the judge to understand *why* scores are low
- Check if failures are due to retrieval issues (wrong context) or generation issues (poor use of correct context)

<!-- fold:break -->

### Custom Evaluation Criteria

By now, you have a pretty good set of metrics to use to understand your IT Help Desk agent's performance in retrieval and generation. 

However, the metrics we discussed so far alone may miss key performance indicators specific to your use case. 

For example, you may need your agent to properly cite knowledge base sources with `[KB]` tags, so users can verify crucial information. This specific requirement won't be captured by general RAG system metrics.

To address these use-case-specific needs, let's explore one final custom evaluation.

<!-- fold:break -->

First, we'll evaluate the agent on citation quality. Run <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '## Custom Evaluation: Citation Quality');"><i class="fas fa-code"></i> Citation Quality </button> to see the results. 

Your results should contain the percent of responses that include citations. Is your agent regularly citing its sources?

Next, evaluate the agent on actionability. Run <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '## Custom Evaluation: Actionability');"><i class="fas fa-code"></i> Actionability </button> to see the results. 

Your results should score the responses on a raw scale of 1-5. Do your agent's responses contain clear, actionable steps?

<!-- fold:break -->

## Evaluating the Report Generation Agent

<img src="_static/robots/typewriter.png" alt="Report Evaluation" style="float:left;max-width:300px;margin:25px;" />

Now that you've thoroughly evaluated your IT Help Desk agent using both standard and custom metrics, you're familiar with the process of running an evaluation! Next, let's put that hard-earned knowledge into practice by evaluating the Report Generation Agent you built in Module 1.

Open the <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/evaluate_report_agent.ipynb');"><i class="fa-solid fa-flask"></i> Report Agent Evaluation</button> notebook.

### Load Test Cases

Load your report generation test dataset - either one you created or the pre-made dataset at `data/evaluation/report_agent_test_cases.json`.

Run <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', 'report_test_cases =');"><i class="fas fa-code"></i> Load Test Cases </button> to load and view the test cases.

<!-- fold:break -->

### Generate Reports

Let's gather some agent responses to evaluate. Run the agent on each test topic by executing the <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', '## Generate Reports');"><i class="fas fa-code"></i> Generate Reports</button> cell.

This may take a few minutes as the agent processes each task.

<!-- fold:break -->

### Evaluate Report Quality

Now that we have our agent responses and our evaluation dataset, we're ready to evaluate!
For report evaluation, we'll use LLM-as-a-judge with specific criteria:

**Structure Evaluation**:
- Does the report have all expected sections?
- Is the organization logical?
- Are sections well-connected?

**Content Evaluation**:
- Is the information accurate and relevant?
- Is each section substantive (not just placeholders)?
- Are claims supported by the research?

**Writing Evaluation**:
- Is the writing clear and professional?
- Is the tone appropriate for the topic?
- Are there grammatical or formatting issues?

Once you're ready, run the cell <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', '## Evaluate Report Quality');"><i class="fas fa-code"></i> Evaluate Report Quality </button> to evaluate your report generation agent's performance.

<!-- fold:break -->

### Judge Calibration Check

Once again, let's perform a quick calibration check. We'll review a small sample of responses side-by-side with the judge's scores to verify alignment with human judgment.

Run the cell under at <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', '## Judge Calibration Check');"><i class="fas fa-code"></i> Judge Calibration Check</button>. Take a moment to review these and consider: Do you agree with the judge's scores?

<!-- fold:break -->

### Analyze Results

<img src="_static/robots/wrench.png" alt="Tool Analysis" style="float:right;max-width:300px;margin:25px;" />

Run <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', '## Analyze Results');"><i class="fas fa-code"></i> Analyze Results</button> to create a readable overview of your evaluation results. 

Check the overall results. Like in the previous example, the final scores should range from 0-1. How did your agent perform in each category?

Examine the statistical breakdown to identify:
- Consistency across different report topics
- Which dimensions show the most variance
- Whether certain types of topics are harder for the agent

Next, let's review any low-scoring responses. Run the cell <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', '## Identify Problem Areas');"><i class="fas fa-code"></i> Identify Problem Areas</button>.

Consider:
- Are there missing sections?
- Do reports contain placeholder content, like "will be drafted"?
- Are there overly vague or unsupported claims?

Finally, let's check the length of the generated reports. Run the cell <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', '## Report Length Analysis');"><i class="fas fa-code"></i> Report Length Analysis</button>.

Consider:
- Reports under 2,000 characters may be too superficial.
- Does length vary across topics?
- Does length correlate with quality scores?

<!-- fold:break -->

## Interpreting Results and Taking Action

<img src="_static/robots/supervisor.png" alt="Taking Action" style="float:right;max-width:300px;margin:25px;" />

Evaluation results should drive improvements. Here are some ideas on how to act on common findings from the two notebooks you just completed:

### Low Context Precision

**Problem**: Retrieving too many irrelevant documents

**Solutions**:
- Adjust retrieval parameters (reduce `k`)
- Improve embedding model
- Enhance document chunking strategy
- Add metadata filtering

### Low Context Recall

**Problem**: Missing relevant information

**Solutions**:
- Increase number of retrieved documents
- Improve query formulation
- Expand knowledge base coverage
- Use query expansion techniques

### Low Faithfulness

**Problem**: Agent making unsupported claims

**Solutions**:
- Strengthen system prompt to emphasize grounding
- Add explicit citation requirements
- Reduce model temperature
- Implement fact-checking step

### Low Answer Relevancy

**Problem**: Responses don't address the question

**Solutions**:
- Improve system prompt clarity
- Add question understanding step
- Use few-shot examples
- Implement response validation

<!-- fold:break -->

### Incomplete Structure

**Problem**: Incomplete or unexpected output structure

**Solutions**:
- Strengthen section-by-section outline in the system prompt
- Provide examples of well-structured outputs
- Enforce required headings via templates

### Inaccurate Content

**Problem**: Unsupported or inaccurate claims

**Solutions**:
- Require source citations for factual claims
- Add a fact-checking or verification step in the prompt
- Lower temperature to reduce hallucinations

### Poor Writing Quality

**Problem**: Output is unclear, incorrect tone, or contains improper grammar

**Solutions**:
- Add explicit style and tone guidelines
- Include a revision pass for clarity and grammar
- Provide strong exemplars for desired writing quality
- Use a formatting checklist for final output

<!-- fold:break -->

## What's Next

Congrats! You now have a comprehensive evaluation framework for your agents! In the next lesson, [Continuous Improvement](continuous_improvement.md), we'll explore:

- Systematic approaches to improving agent performance
- Building a culture of quality around AI agents
- Wrapping up the learnings and best practices from this module

