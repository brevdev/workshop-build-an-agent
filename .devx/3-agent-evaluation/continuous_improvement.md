# Continuous Improvement

<img src="_static/robots/hiking.png" alt="Continuous Journey" style="float:right;max-width:300px;margin:25px;" />

Evaluation is not the end goal—it's a tool for continuous improvement. In this final lesson, we'll explore how to use evaluation results to systematically improve your agents and close the loop on everything you've learned in this module.

<!-- fold:break -->

## The Improvement Cycle

Effective agent improvement follows a continuous cycle:

1. **Measure**: Run comprehensive evaluations
2. **Analyze**: Identify patterns in failures and weaknesses
3. **Hypothesize**: Form theories about what changes will help
4. **Implement**: Make targeted improvements
5. **Validate**: Re-evaluate to confirm improvements
6. **Repeat**: Continue the cycle

This systematic approach ensures that improvements are data-driven and measurable rather than based on guesswork.

<!-- fold:break -->

## Common Improvement Strategies

### Strategy 1: Prompt Engineering

Often the fastest way to improve agent performance is refining prompts.

**When to use**: Low scores on answer quality, relevancy, or tone

**Techniques**:
- Add specific instructions for problem areas
- Include few-shot examples of desired behavior
- Clarify success criteria in the system prompt
- Adjust tone and style guidance

**Example**:
```python
# Before
system_prompt = "You are a helpful assistant."

# After - more specific
system_prompt = """You are an IT help desk assistant.
- Always cite sources with [KB]
- Provide step-by-step instructions
- If information is missing, clearly state what you need
- Keep responses concise and actionable"""
```

**Validation**: Re-run evaluation focusing on metrics that were low.

<!-- fold:break -->

### Strategy 2: Retrieval Optimization

For RAG agents, improving retrieval quality often has the biggest impact.

**When to use**: Low context precision, context recall, or faithfulness scores

**Techniques**:

**Adjust Retrieval Parameters**:
```python
# Experiment with different values
retriever = vectordb.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 6,  # Try different values: 3, 6, 10
        "score_threshold": 0.7  # Filter low-quality matches
    }
)
```

**Improve Chunking**:
```python
# Experiment with chunk size and overlap
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,  # Try: 500, 800, 1200
    chunk_overlap=120  # Try: 50, 120, 200
)
```

**Enhance Metadata**:
```python
# Add metadata for filtering
for doc in docs:
    doc.metadata["category"] = categorize(doc)
    doc.metadata["priority"] = assess_priority(doc)

# Use in retrieval
retriever = vectordb.as_retriever(
    search_kwargs={
        "filter": {"category": "password_reset"}
    }
)
```

**Validation**: Focus on context precision and recall metrics.

<!-- fold:break -->

### Strategy 3: Model Selection

Different models have different strengths. Choose the right model for each task.

**When to use**: Persistent quality issues despite prompt and retrieval improvements

**Considerations**:

**For Main LLM**:
- **Nano models**: Fast and cost-effective, good for straightforward tasks
- **Larger models**: Better reasoning for complex tasks
- **Specialized models**: Some models excel at specific domains

**For Embeddings**:
- **General purpose**: Good for most use cases
- **Domain-specific**: Better for specialized content
- **Multilingual**: If you need multiple languages

**Example**:
```python
# Try different models
llm_options = [
    "nvidia/nvidia-nemotron-nano-9b-v2",  # Fast, efficient
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",  # More capable
]

for model_name in llm_options:
    llm = ChatNVIDIA(model=model_name)
    results = evaluate_agent(llm)
    print(f"{model_name}: {results}")
```

**Validation**: Compare evaluation scores across models.

<!-- fold:break -->

### Strategy 4: Architecture Changes

Sometimes you need to modify the agent's structure.

**When to use**: Fundamental limitations in the current architecture

**Techniques**:

**Add Validation Steps**:
```python
# Add a validation node to your graph
def validate_response(state):
    if not has_citation(state.response):
        return {"needs_revision": True}
    return {"needs_revision": False}

workflow.add_node("validate", validate_response)
workflow.add_conditional_edges(
    "generate",
    lambda x: "revise" if x["needs_revision"] else "end"
)
```

**Implement Multi-Step Reasoning**:
```python
# Break complex tasks into steps
workflow.add_node("understand_question", understand_question)
workflow.add_node("gather_information", gather_information)
workflow.add_node("synthesize_answer", synthesize_answer)
```

**Add Self-Correction**:
```python
# Let agent review and improve its own output
def self_review(state):
    review_prompt = f"Review this answer for accuracy: {state.answer}"
    feedback = llm.invoke(review_prompt)
    if needs_improvement(feedback):
        return {"revise": True}
    return {"revise": False}
```

**Validation**: Run comprehensive evaluation on the new architecture.

<!-- fold:break -->

### Strategy 5: Training Data Enhancement

Improve the knowledge base or training data.

**When to use**: Agent consistently lacks information or has outdated knowledge

**For RAG Systems**:
- Add missing documents to knowledge base
- Update outdated information
- Improve document quality and structure
- Add metadata and tags

**Validation**: Context recall should improve if information gaps were the issue.

<!-- fold:break -->

## Real-World Example: Complete Improvement Cycle

<img src="_static/robots/hero.png" alt="Success Story" style="float:right;max-width:300px;margin:25px;" />

Let's walk through a complete example of using the evaluation life cycle to improve an agent.

### Starting Point

Your IT Help Desk agent has these evaluation results:

```
Mean Scores:
  Faithfulness:  0.65 (Needs improvement)
  Relevancy:     0.78 (Good)
  Helpfulness:   0.72 (Good)
  Citation Rate: 45%

Problem areas identified:
- Low faithfulness on password-related questions
- Inconsistent citation usage
- Some responses include general knowledge beyond KB
```

### Step 1: Investigate Root Causes

Examine low-scoring examples:

```python
# Find faithfulness issues
low_faith = df[df['faithfulness_score'] < 0.6]
print(low_faith[['question', 'agent_response', 'faithfulness_explanation']])

# Example finding:
# Question: "How do I reset my password?"
# Response: "Reset your password at the portal. Passwords should be 
#            at least 12 characters with uppercase, lowercase, and symbols."
# Issue: The complexity requirements weren't in the retrieved context!
```

**Root cause**: Agent is adding password policy knowledge from training data.

<!-- fold:break -->

### Step 2: Implement Fix

Update the system prompt:

```python
# Before
SYSTEM_PROMPT = """
You are an IT help desk support agent.
Use the knowledge base to answer questions.
"""

# After
SYSTEM_PROMPT = """
You are an IT help desk support agent.

CRITICAL RULES:
1. ONLY use information from retrieved context
2. DO NOT add information from your general knowledge
3. If context doesn't cover something, say "I don't have that information in our knowledge base"
4. Cite EVERY fact with [KB]
5. Better to say "I don't know" than to guess

When answering:
- Check: Is this fact in my retrieved context?
- If yes: Include it with [KB] citation
- If no: Don't include it
"""
```

<!-- fold:break -->

### Step 3: Re-evaluate

Run evaluation again:

```python
# Re-run evaluation with updated agent
updated_results = evaluate_agent(updated_agent, test_cases)

print("Improvement Analysis:")
print(f"Faithfulness: {original_results['faithfulness']:.2f} → {updated_results['faithfulness']:.2f}")
print(f"Citation Rate: {original_results['citation_rate']:.1%} → {updated_results['citation_rate']:.1%}")
```

**Results**:
```
Faithfulness: 0.65 → 0.85 (+0.20 ✅)
Citation Rate: 45% → 82% (+37% ✅)
Relevancy: 0.78 → 0.76 (-0.02, acceptable)
```

### Step 4: Address Remaining Issues

Citation rate still below 90%. Add enforcement:

```python
def validate_response(response: str, contexts: str) -> dict:
    """Validate response quality before returning."""
    issues = []
    
    # Check for citations
    if "[KB]" not in response:
        issues.append("Missing knowledge base citation")
    
    # Check faithfulness
    if len(response) > 100 and response.count("[KB]") < 2:
        issues.append("Insufficient citations for response length")
    
    if issues:
        # Regenerate with stricter prompt
        return regenerate_with_emphasis(response, contexts, issues)
    
    return {"response": response, "validated": True}
```

<!-- fold:break -->

### Step 5: Offline Evaluation Results

After 3 iterations of offline evaluation:

```
OFFLINE EVALUATION SCORES:
  Faithfulness:  0.88 (Excellent) ✅
  Relevancy:     0.79 (Good) ✅
  Helpfulness:   0.85 (Excellent) ✅
  Citation Rate: 94% ✅

Improvement Summary:
  +35% Faithfulness
  +23pp Citation Rate
  +18% Helpfulness
  0 Regression issues

Time invested: 4 hours
```

Your offline metrics look great! But how do you know these improvements translate to real-world performance? Time for the final validation step.

<!-- fold:break -->

### Step 6: Validate with A/B Testing

Before rolling out the improved agent to all users, deploy an A/B test to validate real-world impact:

```
7-Day A/B TEST RESULTS (10% traffic to improved agent):

                          Control (v1)    Treatment (v2)    Change
Task Completion Rate:        72%              84%           +12% ✅
User Satisfaction:           3.2/5            4.1/5         +0.9 ✅
Escalation Rate:             18%              11%           -7%  ✅
Avg Session Length:          4.2 min          3.1 min       -26% ✅

Statistical Significance: p < 0.01 for all metrics
```

The A/B test confirms that offline improvements translate to real-world gains. Ship it!

<!-- fold:break -->

## Module Wrap-Up

<img src="_static/robots/finish.png" alt="Finish Line" style="float:right;max-width:300px;margin:25px;" />

You've completed the Agent Evaluation module! Let's recap what you've accomplished:

### What You Learned

**In the Introduction**, you discovered why systematic evaluation matters—moving beyond "vibe checks" to rigorous, data-driven quality assessment. You learned about the unique challenges of agent evaluation.

**In Understanding Evaluation Metrics**, you dove deep into RAGAS metrics for RAG agents (Context Precision, Context Recall, Faithfulness, Answer Relevancy) and learned how to evaluate task agents on completion rate, tool usage, and output quality.

**In Creating Evaluation Datasets**, you learned strategies for building high-quality test datasets. You designed evaluation datasets tailored to both the IT Help Desk RAG agent and the Report Generation agent.

**In Running Evaluations**, you got hands-on with evaluation pipelines, using judge models to evaluate both the IT Help Desk agent and the Report Generation agent. You learned to create test datasets, design evaluation prompts, and analyze results.

**In this lesson**, you learned how to close the loop—using evaluation results to systematically improve your agents through targeted strategies and iterative refinement.

<!-- fold:break -->

### Skills You're Taking Away

<img src="_static/robots/party.png" alt="Celebration" style="float:left;max-width:300px;margin:25px;" />

✅ Understanding of evaluation metrics and when to use them  
✅ Experience with RAGAS for RAG evaluation  
✅ Skills in LLM-as-a-judge techniques with NVIDIA models  
✅ Practical evaluation pipelines for your agents  
✅ Strategies for continuous improvement  
✅ Systematic debugging techniques  

You've transformed from relying on intuition to having a rigorous, data-driven approach to agent quality.

<!-- fold:break -->

### Alternative Evaluation Frameworks

While this module focused on RAGAS and custom LLM-as-a-judge pipelines, the evaluation ecosystem is rich with other tools worth exploring as you scale your agent development:

- **[LangSmith](https://smith.langchain.com/)**: LangChain's platform for debugging, testing, and monitoring LLM applications. Offers tracing, dataset management, and evaluation features tightly integrated with LangChain agents.

- **[Weights & Biases (W&B)](https://wandb.ai/)**: A popular MLOps platform that supports experiment tracking, model versioning, and evaluation dashboards. Great for comparing agent versions over time.

- **[Arize Phoenix](https://phoenix.arize.com/)**: An open-source observability tool for LLM applications with built-in support for tracing, evaluation, and debugging retrieval and generation quality.

- **[DeepEval](https://docs.confident-ai.com/)**: An open-source evaluation framework with pre-built metrics for hallucination, relevancy, toxicity, and more. Integrates well with CI/CD pipelines.

Each tool has different strengths—some excel at real-time monitoring, others at offline batch evaluation, and some offer better integration with specific agent frameworks. As your evaluation needs grow, consider how these tools might complement the techniques and concepts you've learned here.

<!-- fold:break -->

## Final Thoughts

<img src="_static/robots/study.png" alt="Keep Learning" style="float:right;max-width:300px;margin:25px;" />

Remember: evaluation is not about achieving perfect scores—it's about understanding your agent's behavior, identifying areas for improvement, and building confidence in your system. The goal is continuous progress, not perfection.

The best agents aren't built in a single sprint. They're refined over time through careful measurement, analysis, and iteration. You now have the tools to make that journey a systematic one.

Happy evaluating! 🚀
