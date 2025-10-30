# LLM-as-a-Judge

<img src="_static/robots/magician.png" alt="LLM Judge" style="float:right;max-width:300px;margin:25px;" />

One of the most powerful techniques for evaluating AI agents is using another LLM to judge the quality of outputs. This approach, called "LLM-as-a-judge," allows us to evaluate subjective qualities like helpfulness, coherence, and relevance at scale. In this lesson, we'll explore how to use NVIDIA models as judges for agent evaluation.

<!-- fold:break -->

## Why LLM-as-a-Judge?

<img src="_static/robots/study.png" alt="Understanding Judgment" style="float:left;max-width:300px;margin:25px;" />

Traditional metrics like exact string matching or BLEU scores don't work well for evaluating natural language outputs. Human evaluation is accurate but expensive and slow. LLM-as-a-judge provides a middle ground:

**Advantages**:
- **Scalable**: Evaluate thousands of outputs quickly
- **Consistent**: More consistent than human reviewers
- **Flexible**: Can assess any criteria you define
- **Nuanced**: Understands semantic meaning and context
- **Cost-Effective**: Cheaper than human evaluation at scale

**Limitations**:
- **Not Perfect**: Judge models can make mistakes
- **Biased**: May favor outputs similar to their own style
- **Costly**: More expensive than simple metrics
- **Requires Validation**: Should be spot-checked against human judgment

<!-- fold:break -->

## NVIDIA Models for Evaluation

NVIDIA provides several models that work well as evaluation judges:

### Nemotron Models

The [NVIDIA Nemotron family](https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2) offers excellent reasoning capabilities:

- **Nemotron Nano 9B**: Fast and efficient, good for high-volume evaluation
- **Nemotron 70B**: More capable, better for complex evaluation tasks
- **Optimized for Reasoning**: Designed for analytical tasks like evaluation

### Why Use NVIDIA Models?

1. **Performance**: Strong reasoning capabilities for nuanced evaluation
2. **Availability**: Accessible through NVIDIA NIM endpoints
3. **Consistency**: Reproducible results for reliable evaluation
4. **Cost-Effective**: Competitive pricing for evaluation workloads
5. **Integration**: Works seamlessly with LangChain and LangSmith

<!-- fold:break -->

## Designing Evaluation Prompts

<img src="_static/robots/typewriter.png" alt="Crafting Prompts" style="float:right;max-width:300px;margin:25px;" />

The quality of LLM-as-a-judge evaluation depends heavily on your evaluation prompts. Here are key principles:

### 1. Be Specific About Criteria

**Bad**: "Is this a good answer?"

**Good**: "Evaluate this answer on the following criteria:
1. Relevance: Does it directly address the question?
2. Accuracy: Are all factual claims correct?
3. Completeness: Does it cover all aspects of the question?
4. Clarity: Is it easy to understand?"

### 2. Provide Context

Include all relevant information the judge needs:
- The original question or task
- The agent's output
- Retrieved context (for RAG systems)
- Ground truth answer (if available)

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

### 4. Include Examples

Few-shot examples help the judge understand your standards:

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

## Evaluation Patterns

### Pattern 1: Single-Aspect Evaluation

Evaluate one specific aspect at a time.

**Use case**: When you need detailed assessment of a particular quality

**Example**: Evaluating faithfulness in RAG responses

```python
evaluation_prompt = """
You are evaluating whether an AI assistant's answer is faithful to the provided context.

Context: {context}
Question: {question}
Answer: {answer}

Is every claim in the answer supported by the context?
- Score 1: Multiple unsupported claims
- Score 3: Some claims lack support
- Score 5: All claims are supported

Provide your score and explanation.
"""
```

<!-- fold:break -->

### Pattern 2: Multi-Aspect Evaluation

Evaluate multiple criteria in a single pass.

**Use case**: When you need a holistic view of quality

**Example**: Overall response quality

```python
evaluation_prompt = """
Evaluate this AI assistant response on multiple criteria:

Question: {question}
Answer: {answer}

Criteria:
1. Relevance (1-5): Does it answer the question?
2. Helpfulness (1-5): Would this help the user?
3. Clarity (1-5): Is it easy to understand?
4. Professionalism (1-5): Is the tone appropriate?

Provide scores and brief explanations for each criterion.
"""
```

<!-- fold:break -->

### Pattern 3: Comparative Evaluation

Compare two outputs to determine which is better.

**Use case**: A/B testing different models or prompts

**Example**: Comparing two agent responses

```python
evaluation_prompt = """
Compare these two responses to the same question:

Question: {question}

Response A: {response_a}
Response B: {response_b}

Which response is better? Consider:
- Accuracy
- Completeness
- Clarity

Choose: A, B, or Tie
Provide your reasoning.
"""
```

<!-- fold:break -->

### Pattern 4: Chain-of-Thought Evaluation

Ask the judge to reason step-by-step before scoring.

**Use case**: Complex evaluations requiring careful analysis

**Example**: Evaluating multi-step reasoning

```python
evaluation_prompt = """
Evaluate this agent's reasoning process:

Task: {task}
Agent's Steps: {steps}
Final Output: {output}

First, analyze:
1. Did the agent identify the right approach?
2. Were the intermediate steps logical?
3. Is the final output correct?

Then, provide an overall score (1-5) and explanation.
"""
```

<!-- fold:break -->

## Implementing LLM-as-a-Judge with NVIDIA

<img src="_static/robots/plumber.png" alt="Implementation" style="float:left;max-width:300px;margin:25px;" />

Let's look at a practical implementation using NVIDIA models:

```python
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate

# Initialize NVIDIA model as judge
judge_llm = ChatNVIDIA(
    model="nvidia/nvidia-nemotron-nano-9b-v2",
    temperature=0.0  # Use 0 for consistent evaluation
)

# Define evaluation prompt
eval_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert evaluator of AI assistant responses."),
    ("user", """
Evaluate this response:

Question: {question}
Answer: {answer}
Context: {context}

Rate the faithfulness (1-5): Are all claims supported by the context?
Provide your score and a brief explanation.
""")
])

# Create evaluation chain
eval_chain = eval_prompt | judge_llm

# Run evaluation
result = eval_chain.invoke({
    "question": "How do I reset my password?",
    "answer": "Visit the self-service portal at portal.company.com/reset",
    "context": "Password resets can be done through the self-service portal..."
})

print(result.content)
```

<!-- fold:break -->

## Handling Judge Output

LLM judges can return outputs in various formats. Here are strategies for parsing them:

### Strategy 1: JSON Mode

Request structured JSON output:

```python
judge_llm = ChatNVIDIA(
    model="nvidia/nvidia-nemotron-nano-9b-v2",
    temperature=0.0
)

eval_prompt = """
Evaluate and return JSON:
{
  "score": <1-5>,
  "explanation": "<brief explanation>"
}

Question: {question}
Answer: {answer}
"""

# Parse JSON response
import json
result = judge_llm.invoke(eval_prompt)
scores = json.loads(result.content)
```

### Strategy 2: Regex Parsing

Extract scores from natural language:

```python
import re

result = judge_llm.invoke(eval_prompt)
score_match = re.search(r'Score:\s*(\d+)', result.content)
if score_match:
    score = int(score_match.group(1))
```

### Strategy 3: Structured Output

Use Pydantic models for type safety:

```python
from pydantic import BaseModel

class EvaluationResult(BaseModel):
    score: int
    explanation: str
    
# Use with structured output
result = eval_chain.with_structured_output(EvaluationResult).invoke(...)
```

<!-- fold:break -->

## Best Practices

<img src="_static/robots/controls.png" alt="Best Practices" style="float:right;max-width:300px;margin:25px;" />

### 1. Validate Your Judge

Before relying on automated evaluation:
- Manually evaluate a sample of outputs
- Compare judge scores with human scores
- Calculate inter-rater reliability
- Adjust prompts if judge is too lenient or harsh

### 2. Use Temperature 0

For consistent evaluation results:
```python
judge_llm = ChatNVIDIA(model="...", temperature=0.0)
```

### 3. Provide Clear Rubrics

Define what each score means:
```
Score 5: Perfect - All criteria fully met
Score 4: Good - Minor issues only
Score 3: Acceptable - Some significant issues
Score 2: Poor - Major problems
Score 1: Unacceptable - Fails basic requirements
```

### 4. Consider Multiple Judges

For critical evaluations, use multiple models and aggregate:
```python
judges = [
    ChatNVIDIA(model="nvidia/nvidia-nemotron-nano-9b-v2"),
    ChatNVIDIA(model="nvidia/llama-3.1-nemotron-70b-instruct"),
]

scores = [judge.invoke(eval_prompt) for judge in judges]
final_score = sum(scores) / len(scores)
```

### 5. Monitor Judge Performance

Track metrics about your judge:
- Agreement with human evaluators
- Consistency across similar examples
- Bias patterns (e.g., favoring longer responses)

<!-- fold:break -->

## Cost Optimization

LLM-as-a-judge can be expensive at scale. Optimize costs by:

### 1. Tiered Evaluation

Use cheaper judges for most evaluations, expensive judges for edge cases:

```python
# Quick screening with smaller model
quick_score = nano_judge.invoke(eval_prompt)

# Detailed evaluation only if quick score is borderline
if 2 <= quick_score <= 4:
    detailed_score = large_judge.invoke(detailed_eval_prompt)
```

### 2. Batch Processing

Evaluate multiple examples in one API call:

```python
batch_prompt = """
Evaluate each of these responses:

1. Question: {q1}
   Answer: {a1}
   
2. Question: {q2}
   Answer: {a2}

Provide scores for each.
"""
```

### 3. Caching

Cache evaluation results to avoid re-evaluating:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def evaluate_response(question, answer):
    return judge_llm.invoke(eval_prompt)
```

<!-- fold:break -->

## Combining with Other Metrics

LLM-as-a-judge works best when combined with other evaluation approaches:

```python
def comprehensive_evaluation(question, answer, context):
    # Fast, cheap metrics first
    length_ok = 50 <= len(answer) <= 500
    has_citation = "[KB]" in answer
    
    # LLM-based evaluation for quality
    judge_score = judge_llm.invoke(eval_prompt)
    
    # Combine into overall assessment
    return {
        "length_check": length_ok,
        "citation_check": has_citation,
        "quality_score": judge_score,
        "overall_pass": length_ok and has_citation and judge_score >= 3
    }
```

<!-- fold:break -->

## Ready for Hands-On Practice

Now that you understand LLM-as-a-judge techniques, let's put them into practice! Continue to [Running Evaluations](running_evaluations.md) where you'll:

- Build evaluation pipelines for both RAG and task agents
- Implement RAGAS metrics with NVIDIA models
- Create custom evaluation criteria
- Run comprehensive evaluations on your agents from Modules 1 and 2

