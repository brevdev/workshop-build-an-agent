# Module 3: Quick Start Guide

## Prerequisites

Before starting this module, ensure you have:

- ✅ Completed Module 1 (Build an Agent) or Module 2 (Agentic RAG)
- ✅ NVIDIA NGC API Key configured
- ✅ LangSmith API Key configured (recommended)
- ✅ Python environment with all dependencies installed

## Quick Setup

1. **Navigate to the module**:
   ```bash
   cd .devx/3-agent-evaluation
   ```

2. **Open the introduction**:
   - Start with `intro.md` to understand evaluation concepts

3. **Configure secrets** (if not already done):
   - Use the Secrets Manager to set up your NGC API Key
   - Optionally configure LangSmith for tracking

## Recommended Learning Path

### Path A: Evaluate RAG Agent (Faster, ~1.5 hours)

If you completed Module 2, start here:

1. Read [Introduction to Evaluation](intro.md) - 15 min
2. Read [Understanding Evaluation Metrics](evaluation_metrics.md) - 20 min
3. Read [LLM-as-a-Judge](llm_as_judge.md) - 25 min
4. Run RAG agent evaluation:
   ```bash
   cd code
   python evaluate_rag_agent.py
   ```
   This takes 10-20 minutes depending on test set size.

5. Analyze results and read [Continuous Improvement](continuous_improvement.md) - 20 min

### Path B: Evaluate Report Agent (Slower, ~2.5 hours)

If you completed Module 1, start here:

1. Read [Introduction to Evaluation](intro.md) - 15 min
2. Read [Understanding Evaluation Metrics](evaluation_metrics.md) - 20 min
3. Read [LLM-as-a-Judge](llm_as_judge.md) - 25 min
4. Run Report agent evaluation:
   ```bash
   cd code
   python evaluate_report_agent.py
   ```
   This takes 30-60 minutes as reports are generated.

5. Analyze results and read [Continuous Improvement](continuous_improvement.md) - 20 min

### Path C: Complete Experience (~3 hours)

For the full module experience:

1. Follow all reading materials in order
2. Run both evaluation scripts
3. Compare results between agent types
4. Experiment with custom evaluation criteria
5. Try improving one agent based on evaluation results

## Key Files

### Documentation
- `intro.md` - Why evaluation matters
- `evaluation_metrics.md` - Understanding metrics
- `llm_as_judge.md` - Using NVIDIA models as judges
- `running_evaluations.md` - Hands-on exercises
- `continuous_improvement.md` - Improvement strategies

### Code
- `code/evaluation_framework.py` - Reusable evaluation utilities
- `code/evaluate_rag_agent.py` - RAG agent evaluation script
- `code/evaluate_report_agent.py` - Report agent evaluation script

### Data
- `data/evaluation/rag_agent_test_cases.json` - Test cases for RAG agent
- `data/evaluation/report_agent_test_cases.json` - Test cases for Report agent

## Running Evaluations

### RAG Agent Evaluation

```bash
cd code
python evaluate_rag_agent.py
```

**What it does**:
- Loads 12 IT help desk test questions
- Runs the RAG agent on each question
- Evaluates responses using NVIDIA models as judges
- Computes faithfulness, relevancy, and helpfulness scores
- Generates recommendations for improvement

**Expected output**:
- Console output with scores and analysis
- `data/evaluation/rag_agent_results.csv` - Detailed results
- `data/evaluation/rag_agent_summary.json` - Summary statistics

### Report Agent Evaluation

```bash
cd code
python evaluate_report_agent.py
```

**What it does**:
- Loads 6 report topics
- Generates a full report for each topic
- Evaluates report quality (structure, content, accuracy, writing)
- Analyzes report characteristics
- Generates recommendations for improvement

**Expected output**:
- Console output with scores and analysis
- `data/evaluation/report_agent_results.csv` - Detailed results
- `data/evaluation/report_agent_summary.json` - Summary statistics

**Note**: This takes longer as it generates complete reports!

## Understanding Results

### Score Interpretation (1-5 scale)

- **5**: Excellent - Exceeds expectations
- **4**: Good - Meets expectations with minor issues
- **3**: Acceptable - Meets basic requirements
- **2**: Poor - Significant issues present
- **1**: Unacceptable - Fails to meet requirements

### What to Look For

1. **Overall Scores**: Are they above 3.0 (acceptable)?
2. **Category Patterns**: Do certain types of questions perform worse?
3. **Low-Scoring Examples**: What went wrong in failed cases?
4. **Explanations**: What do the judge models say about issues?

## Common Issues

### "Import Error: No module named 'rag_agent'"

**Solution**: Make sure you're in the `code` directory and that `rag_agent.py` exists and is properly configured.

### "API Key Error"

**Solution**: Verify your NGC API Key is set in `secrets.env`:
```bash
NVIDIA_API_KEY=your_key_here
```

### "Evaluation is too slow"

**Solution**: 
- Start with a smaller test set (edit the JSON files)
- Use the faster Nemotron Nano model (already default)
- Run during off-peak hours

### "Scores seem wrong"

**Solution**:
- Check the explanations - they provide context
- Validate a few examples manually
- Remember: evaluation is subjective, scores are guides not absolutes

## Next Steps

After completing this module:

1. **Experiment**: Try improving an agent based on evaluation results
2. **Customize**: Add your own test cases to the datasets
3. **Extend**: Implement custom evaluation criteria for your use case
4. **Deploy**: Use these techniques to monitor production agents
5. **Share**: Apply what you learned to your own AI projects

## Getting Help

- Review the documentation in each lesson
- Check `INSTRUCTOR_NOTES.md` for additional context
- Examine the evaluation framework code for implementation details
- Refer to RAGAS and LangSmith documentation for advanced features

## Key Takeaways

By the end of this module, you should be able to:

✅ Explain why systematic evaluation is important  
✅ Choose appropriate metrics for different agent types  
✅ Use NVIDIA models as evaluation judges  
✅ Run automated evaluation pipelines  
✅ Interpret results and identify improvement areas  
✅ Apply continuous improvement strategies  

Happy evaluating! 🚀

