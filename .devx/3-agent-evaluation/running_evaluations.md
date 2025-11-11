# Running Evaluations

<img src="_static/robots/blueprint.png" alt="Running Evaluations" style="float:left;max-width:300px;margin:25px;" />

Now it's time to put everything together and run comprehensive evaluations on your agents! In this hands-on lesson, you'll build evaluation pipelines for both the RAG agent from Module 2 and the report generation agent from Module 1.

<!-- fold:break -->

## Evaluation Architecture

A robust evaluation pipeline consists of several key components:

1. **Agent Under Test**: The agent you're evaluating
2. **Test Dataset**: Collection of test cases with inputs and expected outputs
3. **Evaluation Prompts and Metrics**: Instructions as to how to score agent outputs
4. **Analysis of Results**: Interpret results for areas of improvement

Let's take a look at these in greater detail in our hands-on example as we build out our evaluation pipeline.

<!-- fold:break -->

## Creating Evaluation Datasets

Good evaluation metrics always require good test data. When creating evaluation datasets, here are some key considerations to keep in mind:

1. **Cover Diverse Scenarios**: Include common cases, edge cases, and failure modes
2. **Include Ground Truth**: Where possible, provide correct answers for comparison
3. **Represent Real Usage**: Base test cases on actual user interactions
4. **Start Small**: Begin with 20-30 high-quality examples, expand over time
5. **Version Control**: Track your datasets alongside your code

<!-- fold:break -->

<img src="_static/robots/operator.png" alt="Dataset Design" style="float:right;max-width:300px;margin:25px;" />

For the IT Help Desk RAG agent from Module 2, each of our evaluation test cases should include:
- Question
- Ground truth answer (if available)
- Expected retrieved contexts (if available)
- Success criteria

Check out the <button onclick="openOrCreateFileInJupyterLab('data/evaluation/rag_agent_test_cases.json');"><i class="fa-brands fa-python"></i> RAG Agent Evaluation Dataset</button> to take a look at some examples we will use in our evaluation pipeline. 

<!-- fold:break -->

For the Report Generation task agent from Module 1, each of our evaluation test cases should include:
- Task description
- Expected tools to be used
- Success criteria
- Example of good output

Check out the <button onclick="openOrCreateFileInJupyterLab('data/evaluation/report_agent_test_cases.json');"><i class="fa-brands fa-python"></i> Report Agent Evaluation Dataset</button> to take a look at some examples we will use in our evaluation pipeline. 

<!-- fold:break -->

## Designing Evaluation Prompts

The quality of an agent evaluation pipeline also depends heavily on your evaluation prompts. Here are some key design principles when crafting evaluation prompts:

<img src="_static/robots/typewriter.png" alt="Crafting Prompts" style="float:right;max-width:300px;margin:25px;" />

### 1. Be Specific About Criteria

**Bad**: "Is this a good answer?"

**Good**: "Evaluate this answer on the following criteria:
1. Relevance: Does it directly address the question?
2. Accuracy: Are all factual claims correct?
3. Completeness: Does it cover all aspects of the question?
4. Clarity: Is it easy to understand?"

<!-- fold:break -->

### 2. Provide Context

Include all relevant information the judge needs:
- The original question or task
- The agent's output
- Retrieved context (for RAG systems)
- Ground truth answer (if available)

<!-- fold:break -->

### 3. Request Structured Output

Ask for scores and explanations:

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

<!-- fold:break -->

### 4. Include Examples

Few-shot examples can help help the judge understand your standards:

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

Let's take a look at some example <button onclick="goToLineAndSelect('code/evaluation_framework.py', '# Evaluation Prompt Templates');"><i class="fas fa-code"></i> evaluation prompt templates </button> just to get a better idea of these principles in action in our evaluation pipeline.

<!-- fold:break -->

## Setting Up the Evaluation Environment

Before we start evaluating, let's set up our environment. Open the <button onclick="openOrCreateFileInJupyterLab('code/evaluation_framework.py');"><i class="fa-brands fa-python"></i> code/evaluation_framework.py</button> file.

This file contains the evaluation framework we'll use. Let's walk through the key components:

### Import Dependencies

The evaluation framework uses several libraries:
- **RAGAS**: For RAG-specific metrics
- **LangChain**: For agent interaction and evaluation chains
- **NVIDIA AI Endpoints**: For models used in evaluation
- **LangSmith** (optional): For tracking and analyzing results

### Configure Models

We'll use NVIDIA models for evaluation:
- **Judge Model**: Nemotron for LLM-as-a-judge evaluation
- **Embedding Model**: For semantic similarity metrics
- **RAGAS Models**: For computing RAGAS metrics

<!-- fold:break -->

## Evaluating the RAG Agent

<img src="_static/robots/datacenter.png" alt="RAG Evaluation" style="float:right;max-width:300px;margin:25px;" />

Let's start by evaluating the IT Help Desk agent from Module 2. Open the <button onclick="openOrCreateFileInJupyterLab('code/evaluate_rag_agent.ipynb');"><i class="fa-solid fa-flask"></i> RAG Agent Evaluation</button> notebook.

### Load the Test Dataset

We've prepared a test dataset with common IT help desk questions. Each test case includes:
- **Question**: The user's query
- **Ground Truth Answer**: The expected response
- **Expected Contexts**: Documents that should be retrieved

Load the dataset at <button onclick="goToLineAndSelect('code/evaluate_rag_agent.ipynb', 'test_dataset =');"><i class="fas fa-code"></i> test_dataset</button>.

<!-- fold:break -->

### Run the Agent on Test Cases

For each test case, we'll:
1. Send the question to the agent
2. Capture the response
3. Record which contexts were retrieved
4. Store the results for evaluation

Execute the cell at <button onclick="goToLineAndSelect('code/evaluate_rag_agent.ipynb', '# Run agent on test cases');"><i class="fas fa-code"></i> Run agent on test cases</button>.

This may take a few minutes as the agent processes each question.

<!-- fold:break -->

### Compute RAGAS Metrics

Now let's evaluate the agent's performance using RAGAS metrics. We'll compute:

- **Context Precision**: Are retrieved documents relevant?
- **Context Recall**: Did we retrieve all necessary information?
- **Faithfulness**: Is the answer grounded in the context?
- **Answer Relevancy**: Does the answer address the question?

Run the evaluation at <button onclick="goToLineAndSelect('code/evaluate_rag_agent.ipynb', '# Compute RAGAS metrics');"><i class="fas fa-code"></i> Compute RAGAS metrics</button>.

<details>
<summary>🆘 Need some help?</summary>

```python
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

# Prepare data for RAGAS
ragas_dataset = {
    "question": [case["question"] for case in results],
    "answer": [case["agent_response"] for case in results],
    "contexts": [case["retrieved_contexts"] for case in results],
    "ground_truth": [case["ground_truth"] for case in results],
}

# Run evaluation
ragas_results = evaluate(
    dataset=ragas_dataset,
    metrics=[
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    ],
    llm=judge_llm,
    embeddings=embeddings,
)

print(ragas_results)
```

</details>

<!-- fold:break -->

### Analyze Results

<img src="_static/robots/debug.png" alt="Analyzing Results" style="float:right;max-width:300px;margin:25px;" />

The evaluation results show aggregate scores across all test cases. Let's dig deeper:

**Overall Metrics**: Look at the mean scores for each metric. Generally:
- **Above 0.8**: Excellent
- **0.6 - 0.8**: Good
- **0.4 - 0.6**: Needs improvement
- **Below 0.4**: Significant issues

**Per-Question Analysis**: Identify which questions performed poorly:

```python
# Find low-scoring questions
for i, case in enumerate(results):
    if case["faithfulness_score"] < 0.6:
        print(f"Low faithfulness: {case['question']}")
        print(f"Answer: {case['agent_response']}")
        print(f"Score: {case['faithfulness_score']}")
        print("---")
```

**Common Failure Patterns**: Look for patterns in failures:
- Are certain topics consistently problematic?
- Does the agent struggle with specific question types?
- Are retrieval or generation issues more common?

<!-- fold:break -->

### Custom Evaluation Criteria

Beyond RAGAS metrics, let's add custom evaluation for IT help desk specific qualities. Add a custom evaluator at <button onclick="goToLineAndSelect('code/evaluate_rag_agent.ipynb', '# Custom evaluation');"><i class="fas fa-code"></i> Custom evaluation</button>.

We'll evaluate:
- **Citation Quality**: Does the agent properly cite sources?
- **Actionability**: Does the response include clear next steps?
- **Tone**: Is the response professional and helpful?

<details>
<summary>🆘 Need some help?</summary>

```python
from langchain_core.prompts import ChatPromptTemplate

custom_eval_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are evaluating IT help desk responses."),
    ("user", """
Evaluate this response on a scale of 1-5:

Question: {question}
Response: {response}

Criteria:
1. Citation Quality: Does it cite sources with [KB]?
2. Actionability: Are next steps clear?
3. Tone: Is it professional and helpful?

Provide scores and brief explanations as JSON.
""")
])

custom_eval_chain = custom_eval_prompt | judge_llm

# Run custom evaluation
for case in results:
    custom_score = custom_eval_chain.invoke({
        "question": case["question"],
        "response": case["agent_response"]
    })
    case["custom_evaluation"] = custom_score.content
```

</details>

<!-- fold:break -->

## Evaluating the Report Generation Agent

<img src="_static/robots/typewriter.png" alt="Report Evaluation" style="float:left;max-width:300px;margin:25px;" />

Now let's evaluate the Report Generation Agent from Module 1. Open the <button onclick="openOrCreateFileInJupyterLab('code/evaluate_report_agent.ipynb');"><i class="fa-solid fa-flask"></i> Report Agent Evaluation</button> notebook.

### Define Test Cases

For the report agent, test cases are different:
- **Topic**: The report subject
- **Expected Sections**: Sections that should appear
- **Quality Criteria**: What makes a good report on this topic

Load the test cases at <button onclick="goToLineAndSelect('code/evaluate_report_agent.ipynb', 'report_test_cases =');"><i class="fas fa-code"></i> report_test_cases</button>.

<!-- fold:break -->

### Generate Reports

Run the agent on each test topic:

```python
from docgen_agent import agent

results = []
for test_case in report_test_cases:
    # Generate report
    result = agent.graph.invoke({
        "topic": test_case["topic"],
        "report_structure": "standard",
        "messages": []
    })
    
    results.append({
        "topic": test_case["topic"],
        "report": result["report"],
        "expected_sections": test_case["expected_sections"]
    })
```

This will take several minutes per report.

<!-- fold:break -->

### Evaluate Report Quality

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

Implement the evaluation at <button onclick="goToLineAndSelect('code/evaluate_report_agent.ipynb', '# Evaluate reports');"><i class="fas fa-code"></i> Evaluate reports</button>.

<details>
<summary>🆘 Need some help?</summary>

```python
report_eval_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert at evaluating research reports."),
    ("user", """
Evaluate this report on the topic: {topic}

Report:
{report}

Expected sections: {expected_sections}

Evaluate on these criteria (1-5 scale):
1. Structure: Are all expected sections present and well-organized?
2. Content Quality: Is the information substantive and relevant?
3. Accuracy: Are claims well-supported?
4. Writing Quality: Is it clear and professional?

Provide scores and explanations as JSON:
{{
  "structure": {{"score": X, "explanation": "..."}},
  "content": {{"score": X, "explanation": "..."}},
  "accuracy": {{"score": X, "explanation": "..."}},
  "writing": {{"score": X, "explanation": "..."}}
}}
""")
])

report_eval_chain = report_eval_prompt | judge_llm

for result in results:
    evaluation = report_eval_chain.invoke({
        "topic": result["topic"],
        "report": result["report"],
        "expected_sections": ", ".join(result["expected_sections"])
    })
    result["evaluation"] = evaluation.content
```

</details>

<!-- fold:break -->

### Tool Usage Analysis

<img src="_static/robots/wrench.png" alt="Tool Analysis" style="float:right;max-width:300px;margin:25px;" />

For the report agent, we should also analyze tool usage patterns:

```python
# Analyze search patterns
for result in results:
    # Extract tool calls from trace
    trace = result.get("trace", {})
    searches = [call for call in trace if call["tool"] == "search_tavily"]
    
    print(f"Topic: {result['topic']}")
    print(f"Number of searches: {len(searches)}")
    print(f"Search queries: {[s['query'] for s in searches]}")
    print("---")
```

Good tool usage patterns:
- Appropriate number of searches (not too few or too many)
- Relevant search queries
- Searches at logical points in the workflow

<!-- fold:break -->

## Interpreting Results and Taking Action

<img src="_static/robots/supervisor.png" alt="Taking Action" style="float:right;max-width:300px;margin:25px;" />

Evaluation results should drive improvements. Here's how to act on common findings:

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

### Poor Tool Usage

**Problem**: Inefficient or incorrect tool calls

**Solutions**:
- Improve tool descriptions
- Add tool usage examples
- Implement tool selection validation
- Adjust model parameters

<!-- fold:break -->

## What's Next

Now that you have a basic understanding of how to evaluate your agents, let's dive deeper by seeing how we can take this to production using NVIDIA open source tooling, like NeMo Evaluator. In the next lesson, [Path to Production (Optional)](production.md), we'll explore: 

- NeMo Evaluator as an open source platform for agent evaluation
- Robust, reproducible, and scalable evaluation of agents and models
- Production monitoring best practices
- Building a culture of quality around AI agents

