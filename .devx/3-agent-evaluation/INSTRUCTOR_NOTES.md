# Module 3: Agent Evaluation - Instructor Notes

## Overview

Module 3 completes the Build an Agent Workshop by teaching students how to evaluate and improve the agents they built in Modules 1 and 2. This module emphasizes practical, hands-on evaluation techniques using NVIDIA models and industry-standard frameworks.

## Learning Progression

This module naturally follows Modules 1 and 2:
- **Module 1**: Students built a Report Generation Agent
- **Module 2**: Students built an IT Help Desk RAG Agent
- **Module 3**: Students learn to evaluate both agents systematically

## Module Structure

### 1. Introduction to Evaluation (intro.md)
**Duration**: 15-20 minutes reading

**Key concepts**:
- Why evaluation is critical for production agents
- Types of evaluation metrics
- RAGAS framework overview
- NVIDIA's evaluation ecosystem

**Teaching tips**:
- Emphasize that evaluation is not a one-time activity
- Connect to real-world scenarios where agents fail
- Preview the hands-on exercises to build excitement

### 2. Understanding Evaluation Metrics (evaluation_metrics.md)
**Duration**: 20-25 minutes reading

**Key concepts**:
- RAGAS metrics deep dive (faithfulness, relevancy, context precision/recall)
- Metrics for task-based agents
- Choosing appropriate metrics
- Creating evaluation datasets

**Teaching tips**:
- Use concrete examples from the IT Help Desk agent
- Discuss trade-offs between different metrics
- Emphasize the importance of representative test data

### 3. LLM-as-a-Judge (llm_as_judge.md)
**Duration**: 25-30 minutes reading + exercises

**Key concepts**:
- Using NVIDIA models as evaluation judges
- Designing effective evaluation prompts
- Evaluation patterns (single-aspect, multi-aspect, comparative, chain-of-thought)
- Best practices and cost optimization

**Teaching tips**:
- Live demo of creating an evaluation prompt
- Show examples of good vs. bad evaluation prompts
- Discuss validation of judge models against human judgment

### 4. Running Evaluations (running_evaluations.md)
**Duration**: 45-60 minutes hands-on

**Key activities**:
- Run evaluation on RAG agent using provided test cases
- Run evaluation on Report Generation agent
- Analyze results and identify improvement areas
- Generate recommendations

**Teaching tips**:
- Students should run `code/3-agent-evaluation/evaluate_rag_agent.py` first (faster)
- Then run `code/3-agent-evaluation/evaluate_report_agent.py` (slower, good for discussion)
- Use wait time to discuss results from early finishers
- Encourage students to examine low-scoring examples

### 5. Continuous Improvement (continuous_improvement.md)
**Duration**: 20-25 minutes reading

**Key concepts**:
- The improvement cycle (measure, analyze, hypothesize, implement, validate)
- Common improvement strategies
- A/B testing
- Production monitoring
- Building a quality culture

**Teaching tips**:
- Share real-world examples of agent improvements
- Discuss organizational challenges in maintaining quality
- Emphasize that perfect scores aren't the goal—understanding behavior is

## Prerequisites

Students should have completed:
- Module 1 (Build an Agent) - for Report Generation Agent
- Module 2 (Agentic RAG) - for IT Help Desk Agent

Students should be familiar with:
- Python programming
- Basic LLM concepts
- LangChain/LangGraph basics

## Technical Requirements

### API Keys Required
- NVIDIA NGC API Key (required)
- LangSmith API Key (recommended for tracking)
- OpenRouter API Key (if evaluating Module 1 agent)
- Tavily API Key (if evaluating Module 1 agent)

### Compute Requirements
- Evaluation can run entirely on NVIDIA-hosted endpoints
- No local GPU required
- Evaluation scripts can take 10-30 minutes depending on test set size

### Dependencies
New dependencies added in Module 3:
- `ragas~=0.2.0` - RAGAS evaluation framework
- `langsmith~=0.3.0` - LangSmith integration
- `pandas~=2.2.0` - Data analysis

## Common Student Questions

### "Why do we need evaluation? Can't we just test manually?"

**Answer**: Manual testing doesn't scale and introduces bias. Systematic evaluation provides:
- Quantitative metrics for comparison
- Reproducible results
- Coverage of edge cases
- Continuous monitoring capability

### "The evaluation scores seem arbitrary. How do I know they're accurate?"

**Answer**: Great question! This is why we:
- Validate judge models against human judgment
- Use multiple metrics (not just one)
- Examine explanations, not just scores
- Spot-check low-scoring examples manually

### "My agent got low scores. Is it broken?"

**Answer**: Not necessarily! Low scores help you understand where to improve:
- Low faithfulness → strengthen grounding in context
- Low relevancy → improve question understanding
- Low context precision → tune retrieval parameters

### "Can I use these techniques for my own agents?"

**Answer**: Absolutely! The evaluation framework is designed to be:
- Modular and reusable
- Adaptable to different agent types
- Production-ready with minor modifications

## Troubleshooting

### Evaluation takes too long
- Reduce test dataset size for initial runs
- Use faster judge model (Nemotron Nano)
- Run evaluations in parallel if possible

### Judge model returns inconsistent scores
- Ensure temperature is set to 0.0
- Validate evaluation prompts with examples
- Consider using multiple judges and averaging

### Students can't import agents from Modules 1/2
- Check that agents are properly configured
- Verify environment variables are set
- May need to adjust import paths

## Extension Activities

For advanced students or extra time:

1. **Custom Metrics**: Implement domain-specific evaluation criteria
2. **RAGAS Integration**: Add full RAGAS evaluation (requires more setup)
3. **Comparative Evaluation**: Compare different prompt versions
4. **Production Pipeline**: Set up automated evaluation in CI/CD
5. **Adversarial Testing**: Create tests designed to break the agent

## Assessment Ideas

- Have students identify and fix a low-scoring test case
- Ask students to design evaluation criteria for a new agent type
- Challenge students to improve an agent's score by 10%
- Request a written analysis of evaluation results

## Time Management

**Minimum viable module** (1.5 hours):
- Intro + Metrics overview: 30 min
- Run one evaluation script: 45 min
- Discuss results: 15 min

**Recommended full module** (3 hours):
- All reading content: 90 min
- Both evaluation scripts: 60 min
- Discussion and Q&A: 30 min

**Extended workshop** (4+ hours):
- Include extension activities
- Deep dive into improvement strategies
- Hands-on agent improvement exercise

## Key Takeaways

Students should leave Module 3 understanding:

1. **Evaluation is essential** for production AI agents
2. **Multiple metrics** provide comprehensive assessment
3. **LLM-as-a-judge** enables scalable, nuanced evaluation
4. **NVIDIA models** are excellent evaluation judges
5. **Continuous improvement** requires systematic evaluation
6. **Production monitoring** is evaluation in real-time

## Resources for Further Learning

- [RAGAS Documentation](https://docs.ragas.io/)
- [LangSmith Evaluation Guide](https://docs.smith.langchain.com/evaluation)
- [NVIDIA NIM Documentation](https://docs.nvidia.com/nim/)
- [LangChain Evaluation Docs](https://python.langchain.com/docs/guides/evaluation/)

## Feedback and Iteration

This module is designed to evolve based on student feedback. Key areas to monitor:

- Are evaluation concepts clear and actionable?
- Do students successfully run evaluations?
- Are the test datasets representative and challenging?
- Do students understand how to improve based on results?

Please collect feedback and share with the workshop development team!

