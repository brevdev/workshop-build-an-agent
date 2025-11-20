"""
Evaluation script for the RAG agent using NVIDIA models and evaluation framework.

This script demonstrates how to:
1. Load test cases
2. Run the RAG agent on test questions
3. Evaluate responses using LLM-as-a-judge
4. Analyze and report results
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv

from evaluation_framework import (
    create_judge_llm,
    evaluate_rag_response,
    calculate_aggregate_score
)

# Load environment variables
load_dotenv("../../variables.env")
load_dotenv("../../secrets.env")

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


def load_test_dataset(dataset_path: Path) -> List[Dict]:
    """Load test cases from JSON file."""
    with open(dataset_path, 'r') as f:
        return json.load(f)


def run_agent_on_test_cases(test_dataset: List[Dict], agent) -> List[Dict]:
    """
    Run the agent on all test cases and collect results.
    
    Args:
        test_dataset: List of test cases
        agent: The RAG agent to evaluate
        
    Returns:
        List of results with agent responses
    """
    results = []
    
    for i, test_case in enumerate(test_dataset):
        _LOGGER.info(f"Processing test case {i+1}/{len(test_dataset)}: {test_case['question'][:50]}...")
        
        try:
            # Run the agent
            response = agent.invoke({
                "messages": [{"role": "user", "content": test_case["question"]}]
            })
            
            # Extract the response
            agent_response = response["messages"][-1].content
            
            # In a production system, you would capture retrieved contexts
            # from the agent's execution trace
            retrieved_contexts = "Context from agent execution"
            
            results.append({
                "question": test_case["question"],
                "agent_response": agent_response,
                "ground_truth": test_case["ground_truth"],
                "retrieved_contexts": retrieved_contexts,
                "category": test_case["category"]
            })
            
            _LOGGER.info(f"Response: {agent_response[:100]}...")
            
        except Exception as e:
            _LOGGER.error(f"Error processing test case: {e}")
            results.append({
                "question": test_case["question"],
                "agent_response": f"ERROR: {str(e)}",
                "ground_truth": test_case["ground_truth"],
                "retrieved_contexts": "",
                "category": test_case["category"]
            })
    
    return results


def evaluate_responses(results: List[Dict], judge_llm) -> List[Dict]:
    """
    Evaluate all agent responses using LLM-as-a-judge.
    
    Args:
        results: List of agent responses to evaluate
        judge_llm: The judge model
        
    Returns:
        Updated results with evaluation scores
    """
    for i, result in enumerate(results):
        _LOGGER.info(f"Evaluating response {i+1}/{len(results)}...")
        
        try:
            # Run comprehensive evaluation
            eval_results = evaluate_rag_response(
                question=result["question"],
                response=result["agent_response"],
                context=result["retrieved_contexts"],
                judge_llm=judge_llm
            )
            
            # Store evaluation results
            result["faithfulness_score"] = eval_results["faithfulness"].score
            result["faithfulness_explanation"] = eval_results["faithfulness"].explanation
            result["relevancy_score"] = eval_results["relevancy"].score
            result["relevancy_explanation"] = eval_results["relevancy"].explanation
            result["helpfulness_score"] = eval_results["helpfulness"].score
            result["helpfulness_explanation"] = eval_results["helpfulness"].explanation
            
            # Calculate aggregate score
            result["aggregate_score"] = calculate_aggregate_score(eval_results)
            
            _LOGGER.info(
                f"Scores - Faithfulness: {result['faithfulness_score']}, "
                f"Relevancy: {result['relevancy_score']}, "
                f"Helpfulness: {result['helpfulness_score']}"
            )
            
        except Exception as e:
            _LOGGER.error(f"Error evaluating response: {e}")
            result["faithfulness_score"] = 0.0
            result["relevancy_score"] = 0.0
            result["helpfulness_score"] = 0.0
            result["aggregate_score"] = 0.0
    
    return results


def analyze_results(df: pd.DataFrame) -> Dict:
    """
    Analyze evaluation results and generate insights.
    
    Args:
        df: DataFrame with evaluation results
        
    Returns:
        Dictionary with analysis summary
    """
    print("=" * 60)
    print("OVERALL EVALUATION RESULTS")
    print("=" * 60)
    print(f"\nMean Scores (1-5 scale):")
    print(f"  Faithfulness:  {df['faithfulness_score'].mean():.2f}")
    print(f"  Relevancy:     {df['relevancy_score'].mean():.2f}")
    print(f"  Helpfulness:   {df['helpfulness_score'].mean():.2f}")
    print(f"\nAggregate Score (0-1 scale): {df['aggregate_score'].mean():.3f}")
    
    # Performance by category
    print("\n" + "=" * 60)
    print("PERFORMANCE BY CATEGORY")
    print("=" * 60)
    category_stats = df.groupby('category')[
        ['faithfulness_score', 'relevancy_score', 'helpfulness_score']
    ].mean()
    print(category_stats.round(2))
    
    # Identify problem areas
    threshold = 3.0
    print("\n" + "=" * 60)
    print("LOW-SCORING RESPONSES (Score < 3.0)")
    print("=" * 60)
    
    low_scores = df[
        (df['faithfulness_score'] < threshold) |
        (df['relevancy_score'] < threshold) |
        (df['helpfulness_score'] < threshold)
    ]
    
    if len(low_scores) > 0:
        print(f"\n⚠️  Found {len(low_scores)} low-scoring responses:")
        for _, row in low_scores.iterrows():
            print(f"\nQuestion: {row['question']}")
            print(f"Faithfulness: {row['faithfulness_score']} - {row['faithfulness_explanation']}")
            print(f"Relevancy: {row['relevancy_score']} - {row['relevancy_explanation']}")
            print(f"Helpfulness: {row['helpfulness_score']} - {row['helpfulness_explanation']}")
            print("-" * 60)
    else:
        print("\n✅ All responses scored above threshold!")
    
    # Citation analysis
    df['has_citation'] = df['agent_response'].apply(lambda x: "[KB]" in x)
    citation_rate = df['has_citation'].mean()
    
    print("\n" + "=" * 60)
    print("CITATION QUALITY ANALYSIS")
    print("=" * 60)
    print(f"\nCitation Rate: {citation_rate:.1%}")
    print(f"Responses with citations: {df['has_citation'].sum()}/{len(df)}")
    
    if citation_rate < 0.8:
        print("\n⚠️  Warning: Citation rate is below 80%")
    
    return {
        "mean_faithfulness": float(df['faithfulness_score'].mean()),
        "mean_relevancy": float(df['relevancy_score'].mean()),
        "mean_helpfulness": float(df['helpfulness_score'].mean()),
        "aggregate_score": float(df['aggregate_score'].mean()),
        "citation_rate": float(citation_rate),
        "total_test_cases": len(df),
        "low_scoring_count": len(low_scores)
    }


def generate_recommendations(summary: Dict) -> List[str]:
    """Generate improvement recommendations based on evaluation results."""
    recommendations = []
    
    if summary["mean_faithfulness"] < 4.0:
        recommendations.append(
            "📝 Faithfulness: Update system prompt to emphasize grounding responses in retrieved context."
        )
    
    if summary["mean_relevancy"] < 4.0:
        recommendations.append(
            "🎯 Relevancy: Improve question understanding or add explicit relevance checking step."
        )
    
    if summary["mean_helpfulness"] < 4.0:
        recommendations.append(
            "💡 Helpfulness: Add more actionable steps and anticipate follow-up questions."
        )
    
    if summary["citation_rate"] < 0.8:
        recommendations.append(
            "📚 Citations: Strengthen citation requirements in system prompt."
        )
    
    return recommendations


def main():
    """Main evaluation workflow."""
    _LOGGER.info("Starting RAG agent evaluation...")
    
    # Load test dataset
    test_dataset_path = Path(__file__).parent.parent.parent / "data" / "evaluation" / "rag_agent_test_cases.json"
    test_dataset = load_test_dataset(test_dataset_path)
    _LOGGER.info(f"Loaded {len(test_dataset)} test cases")
    
    # Initialize the RAG agent
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "2-agentic-rag"))
        from rag_agent import AGENT
        _LOGGER.info("RAG agent loaded successfully")
    except ImportError as e:
        _LOGGER.error(f"Failed to import RAG agent: {e}")
        _LOGGER.info("Make sure rag_agent.py is properly configured")
        return
    
    # Run agent on test cases
    _LOGGER.info("Running agent on test cases...")
    results = run_agent_on_test_cases(test_dataset, AGENT)
    
    # Initialize judge model
    _LOGGER.info("Initializing judge model...")
    judge_llm = create_judge_llm()
    
    # Evaluate responses
    _LOGGER.info("Evaluating responses...")
    results = evaluate_responses(results, judge_llm)
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)
    
    # Analyze results
    summary = analyze_results(df)
    
    # Generate recommendations
    print("\n" + "=" * 60)
    print("IMPROVEMENT RECOMMENDATIONS")
    print("=" * 60)
    recommendations = generate_recommendations(summary)
    
    if len(recommendations) == 0:
        print("\n🎉 Excellent! Agent is performing well across all metrics.")
        print("Consider testing on more diverse or challenging cases.")
    else:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")
    
    # Save results
    output_dir = Path(__file__).parent.parent.parent / "data" / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_path = output_dir / "rag_agent_results.csv"
    df.to_csv(results_path, index=False)
    _LOGGER.info(f"Results saved to {results_path}")
    
    summary_path = output_dir / "rag_agent_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    _LOGGER.info(f"Summary saved to {summary_path}")
    
    print("\n" + "=" * 60)
    print("✅ Evaluation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

