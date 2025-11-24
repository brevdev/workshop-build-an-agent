# Running Evaluations

<img src="_static/robots/blueprint.png" alt="Running Evaluations" style="float:left;max-width:300px;margin:25px;" />

Now it's time to put everything together and run comprehensive evaluations on your agents! In this hands-on lesson, you'll build evaluation pipelines for both the RAG agent from Module 2 and the report generation agent from Module 1.

<!-- fold:break -->

## Evaluation Architecture

A robust evaluation pipeline consists of several key components:

1. **Agent Under Test**: The agent you're evaluating
2. **Judging Mechanism**: The LLM (or human) that will judge the agent
3. **Test Dataset**: Collection of test cases with inputs and expected outputs
4. **Evaluation Prompts and Metrics**: Instructions as to how to score agent outputs
5. **Analysis of Results**: Interpret results for areas of improvement

Let's take a look at these in greater detail in our hands-on example as we build out our evaluation pipeline. We've already built our agents in the previous modules, and we have established our LLM-as-a-judge mechanism in the previous section. 

<!-- fold:break -->

## Creating Evaluation Datasets

Good evaluation metrics always require good test data. When creating evaluation datasets, here are some key considerations and best practices to keep in mind:

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
- Report Topic
- Expected Report Sections
- Output Quality Criteria

Check out the <button onclick="openOrCreateFileInJupyterLab('data/evaluation/report_agent_test_cases.json');"><i class="fa-brands fa-python"></i> Report Agent Evaluation Dataset</button> to take a look at some examples we will use in our evaluation pipeline. 

<!-- fold:break -->

## Designing Evaluation Prompts

The quality of an agent evaluation pipeline also depends heavily on your evaluation prompts. Here are some key design principles when crafting strong evaluation prompts:

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

Ask for empirical and quantifiable scores, as well as leverage reasoning judge models for justification:

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

<!-- fold:break -->

Let's take a look at some example evaluation prompt templates in <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/evaluation_framework.py');"><i class="fa-brands fa-python"></i> code/3-agent-evaluation/evaluation_framework.py</button> just to get a better idea of these principles in action in our evaluation pipeline.

Your task is to complete the prompts in this file according to the principles outlined above and improve our evaluation prompts to best support the evaluation pipeline we are building together.

**Exercise:** Under the <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluation_framework.py', 'TODO: ...');"><i class="fas fa-code"></i> FAITHFULNESS_PROMPT </button>, we need to do a better job at teaching the judge model what different scores in faithfulness mean. 

In your own words, briefly define what each score level should look like when it comes to evaluating faithfulness of a generated RAG response. Then save the file and check your answers below. 

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

## Evaluating the RAG Agent

<img src="_static/robots/datacenter.png" alt="RAG Evaluation" style="float:right;max-width:300px;margin:25px;" />

Let's start by evaluating the IT Help Desk agent from Module 2. Open the <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/evaluate_rag_agent.ipynb');"><i class="fa-solid fa-flask"></i> RAG Agent Evaluation</button> notebook.

### Load the Test Dataset

We've prepared a test dataset with common IT help desk questions. Each test case includes:
- **Question**: The user's query
- **Ground Truth Answer**: The expected response
- **Expected Contexts**: Documents that should be retrieved
- **Category**: The type of question (password_management, network_access, etc.)

Load the dataset under the <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', 'test_dataset =');"><i class="fas fa-code"></i> Load Test Dataset</button> section.

<!-- fold:break -->

> Before proceeding, ensure ``code/2-agentic-rag/rag_agent.py`` has been completed if not done so already in the previous module. Need help? Check out the <button onclick="openOrCreateFileInJupyterLab('code/2-agentic-rag/rag_agent.answers.py');"><i class="fa-solid fa-flask"></i> RAG Agent Answer Key</button>. 

### Run the Agent on Test Cases

For each test case, we'll:
1. Send the question to the agent
2. Capture the response
3. Record which contexts were retrieved
4. Store the results for evaluation

Execute the cell under <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '# Run agent on test cases');"><i class="fas fa-code"></i> Run Agent on Test Cases</button>.

This may take a few minutes as the agent processes each question.

<!-- fold:break -->

Ok, great! Looks like at this point, we have our generated responses from the IT Help Desk RAG agent. 

Let's evaluate these responses using our LLM judge and the above prompts and see what kind of results we get. We'll evaluate these qualities for now: 

1. Faithfulness - groundedness to the retrieved context
2. Relevancy - addresses the user's question
3. Helpfulness - actionable and useful advice

This may take a few minutes as the judge processes each response.

<!-- fold:break -->

### Compute RAGAS Metrics

We had to create our own metrics above, but what is a more industry-standard evaluation framework for RAG agents?

Next, let's explore and evaluate the agent's performance using RAGAS metrics. We'll compute:

- **Context Precision**: Are retrieved documents relevant?
- **Context Recall**: Did we retrieve all necessary information?
- **Faithfulness**: Is the answer grounded in the context?
- **Answer Relevancy**: Does the answer address the question?

Run the evaluation at <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '# Compute RAGAS metrics');"><i class="fas fa-code"></i> Compute RAGAS Metrics</button>.

<!-- fold:break -->

### Analyze Results

<img src="_static/robots/debug.png" alt="Analyzing Results" style="float:right;max-width:300px;margin:25px;" />

TODO

**Common Failure Patterns**: Look for patterns in failures:
- Are certain topics consistently problematic?
- Does the agent struggle with specific question types?
- Are retrieval or generation issues more common?

<!-- fold:break -->

### Custom Evaluation Criteria

Beyond RAGAS metrics, let's add custom evaluation for IT help desk specific qualities. Let's explore how to evaluate a custom metric under <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_rag_agent.ipynb', '# Custom evaluation');"><i class="fas fa-code"></i> Custom Evaluation </button>.

We'll evaluate:
- **Citation Quality**: Does the agent properly cite sources?
- **Actionability**: Does the response include clear next steps?

<!-- fold:break -->

## Evaluating the Report Generation Agent

<img src="_static/robots/typewriter.png" alt="Report Evaluation" style="float:left;max-width:300px;margin:25px;" />

Now let's evaluate the Report Generation Agent from Module 1. Open the <button onclick="openOrCreateFileInJupyterLab('code/3-agent-evaluation/evaluate_report_agent.ipynb');"><i class="fa-solid fa-flask"></i> Report Agent Evaluation</button> notebook.

### Define Test Cases

For the report generation agent, test cases are a bit different:
- **Topic**: The report subject
- **Expected Sections**: Sections that should appear
- **Quality Criteria**: What makes a good report on this topic

Load the evaluation test cases under <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', 'report_test_cases =');"><i class="fas fa-code"></i> Load Test Cases </button>.

<!-- fold:break -->

### Generate Reports

Run the agent on each test topic. Execute the cell under <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', '# Generate Reports');"><i class="fas fa-code"></i> Generate Reports</button>.

This may take a few minutes as the agent processes each task.

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

Let's run the evaluation under <button onclick="goToLineAndSelect('code/3-agent-evaluation/evaluate_report_agent.ipynb', '## Evaluate Report Quality');"><i class="fas fa-code"></i> Evaluate Report Quality </button>.

<!-- fold:break -->

### Analyze Results

<img src="_static/robots/wrench.png" alt="Tool Analysis" style="float:right;max-width:300px;margin:25px;" />

TODO

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

Now that you have a basic understanding of how to evaluate your agents, let's dive deeper by seeing how we can take this to production using NVIDIA open source tooling, like NeMo Evaluator. In the next lesson, [NeMo Evaluator (Optional)](nemo_evaluator.md), we'll explore: 

- NeMo Evaluator as an open source platform for agent evaluation
- Robust, reproducible, and scalable evaluation of agents and models
- Production monitoring best practices
- Building a culture of quality around AI agents

