"""
Evaluation script for the Report Generation agent using NVIDIA models.

This script demonstrates how to:
1. Load test cases for report generation
2. Generate reports on test topics
3. Evaluate report quality using LLM-as-a-judge
4. Analyze tool usage patterns
5. Generate improvement recommendations
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv

from evaluation_framework import (
    create_judge_llm,
    evaluate_report_quality,
)

# Load environment variables
load_dotenv("../variables.env")
load_dotenv("../secrets.env")

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


def load_test_cases(dataset_path: Path) -> List[Dict]:
    """Load report generation test cases from JSON file."""
    with open(dataset_path, 'r') as f:
        return json.load(f)


def generate_reports(test_cases: List[Dict], agent) -> List[Dict]:
    """
    Generate reports for all test topics.
    
    Args:
        test_cases: List of test cases with topics and expected sections
        agent: The report generation agent
        
    Returns:
        List of results with generated reports
    """
    results = []
    
    for i, test_case in enumerate(test_cases):
        _LOGGER.info(f"Generating report {i+1}/{len(test_cases)}: {test_case['topic']}")
        
        try:
            # Generate report
            result = agent.graph.invoke({
                "topic": test_case["topic"],
                "report_structure": "standard",
                "messages": []
            })
            
            results.append({
                "topic": test_case["topic"],
                "report": result.get("report", ""),
                "expected_sections": test_case["expected_sections"],
                "quality_criteria": test_case.get("quality_criteria", {})
            })
            
            _LOGGER.info(f"Report generated ({len(result.get('report', ''))} characters)")
            
        except Exception as e:
            _LOGGER.error(f"Error generating report: {e}")
            results.append({
                "topic": test_case["topic"],
                "report": f"ERROR: {str(e)}",
                "expected_sections": test_case["expected_sections"],
                "quality_criteria": test_case.get("quality_criteria", {})
            })
    
    return results


def evaluate_reports(results: List[Dict], judge_llm) -> List[Dict]:
    """
    Evaluate all generated reports using LLM-as-a-judge.
    
    Args:
        results: List of generated reports to evaluate
        judge_llm: The judge model
        
    Returns:
        Updated results with evaluation scores
    """
    for i, result in enumerate(results):
        _LOGGER.info(f"Evaluating report {i+1}/{len(results)}...")
        
        try:
            # Run report quality evaluation
            eval_results = evaluate_report_quality(
                topic=result["topic"],
                report=result["report"],
                expected_sections=result["expected_sections"],
                judge_llm=judge_llm
            )
            
            # Store evaluation results
            result["structure_score"] = eval_results["structure"].score
            result["structure_explanation"] = eval_results["structure"].explanation
            result["content_score"] = eval_results["content"].score
            result["content_explanation"] = eval_results["content"].explanation
            result["accuracy_score"] = eval_results["accuracy"].score
            result["accuracy_explanation"] = eval_results["accuracy"].explanation
            result["writing_score"] = eval_results["writing"].score
            result["writing_explanation"] = eval_results["writing"].explanation
            
            # Calculate aggregate score
            result["aggregate_score"] = sum([
                eval_results["structure"].score,
                eval_results["content"].score,
                eval_results["accuracy"].score,
                eval_results["writing"].score
            ]) / 4.0 / 5.0  # Normalize to 0-1
            
            _LOGGER.info(
                f"Scores - Structure: {result['structure_score']}, "
                f"Content: {result['content_score']}, "
                f"Accuracy: {result['accuracy_score']}, "
                f"Writing: {result['writing_score']}"
            )
            
        except Exception as e:
            _LOGGER.error(f"Error evaluating report: {e}")
            result["structure_score"] = 0.0
            result["content_score"] = 0.0
            result["accuracy_score"] = 0.0
            result["writing_score"] = 0.0
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
    print(f"  Structure:  {df['structure_score'].mean():.2f}")
    print(f"  Content:    {df['content_score'].mean():.2f}")
    print(f"  Accuracy:   {df['accuracy_score'].mean():.2f}")
    print(f"  Writing:    {df['writing_score'].mean():.2f}")
    print(f"\nAggregate Score (0-1 scale): {df['aggregate_score'].mean():.3f}")
    
    # Identify problem areas
    threshold = 3.0
    print("\n" + "=" * 60)
    print("LOW-SCORING REPORTS (Score < 3.0)")
    print("=" * 60)
    
    low_scores = df[
        (df['structure_score'] < threshold) |
        (df['content_score'] < threshold) |
        (df['accuracy_score'] < threshold) |
        (df['writing_score'] < threshold)
    ]
    
    if len(low_scores) > 0:
        print(f"\n⚠️  Found {len(low_scores)} low-scoring reports:")
        for _, row in low_scores.iterrows():
            print(f"\nTopic: {row['topic']}")
            print(f"Structure: {row['structure_score']} - {row['structure_explanation']}")
            print(f"Content: {row['content_score']} - {row['content_explanation']}")
            print(f"Accuracy: {row['accuracy_score']} - {row['accuracy_explanation']}")
            print(f"Writing: {row['writing_score']} - {row['writing_explanation']}")
            print("-" * 60)
    else:
        print("\n✅ All reports scored above threshold!")
    
    # Report length analysis
    df['report_length'] = df['report'].apply(len)
    print("\n" + "=" * 60)
    print("REPORT LENGTH ANALYSIS")
    print("=" * 60)
    print(f"\nMean length: {df['report_length'].mean():.0f} characters")
    print(f"Min length: {df['report_length'].min():.0f} characters")
    print(f"Max length: {df['report_length'].max():.0f} characters")
    
    # Check for placeholder content
    df['has_placeholder'] = df['report'].apply(
        lambda x: "will be drafted" in x.lower() or "to be written" in x.lower()
    )
    placeholder_count = df['has_placeholder'].sum()
    
    if placeholder_count > 0:
        print(f"\n⚠️  Warning: {placeholder_count} reports contain placeholder content")
    
    return {
        "mean_structure": float(df['structure_score'].mean()),
        "mean_content": float(df['content_score'].mean()),
        "mean_accuracy": float(df['accuracy_score'].mean()),
        "mean_writing": float(df['writing_score'].mean()),
        "aggregate_score": float(df['aggregate_score'].mean()),
        "mean_length": float(df['report_length'].mean()),
        "total_test_cases": len(df),
        "low_scoring_count": len(low_scores),
        "placeholder_count": int(placeholder_count)
    }


def generate_recommendations(summary: Dict) -> List[str]:
    """Generate improvement recommendations based on evaluation results."""
    recommendations = []
    
    if summary["mean_structure"] < 4.0:
        recommendations.append(
            "📋 Structure: Improve report planning to ensure all expected sections are included and well-organized."
        )
    
    if summary["mean_content"] < 4.0:
        recommendations.append(
            "📝 Content: Enhance research depth to provide more substantive and relevant information."
        )
    
    if summary["mean_accuracy"] < 4.0:
        recommendations.append(
            "✅ Accuracy: Strengthen fact-checking and ensure claims are well-supported by research."
        )
    
    if summary["mean_writing"] < 4.0:
        recommendations.append(
            "✍️  Writing: Improve writing quality through better prompts or post-processing."
        )
    
    if summary["placeholder_count"] > 0:
        recommendations.append(
            "⚠️  Placeholders: Investigate why some sections contain placeholder content instead of actual writing."
        )
    
    if summary["mean_length"] < 2000:
        recommendations.append(
            "📏 Length: Reports may be too short. Consider adjusting section writing prompts for more depth."
        )
    
    return recommendations


def main():
    """Main evaluation workflow."""
    _LOGGER.info("Starting report agent evaluation...")
    
    # Load test cases
    test_cases_path = Path(__file__).parent.parent / "data" / "evaluation" / "report_agent_test_cases.json"
    test_cases = load_test_cases(test_cases_path)
    _LOGGER.info(f"Loaded {len(test_cases)} test cases")
    
    # Initialize the report generation agent
    try:
        from docgen_agent import agent
        _LOGGER.info("Report generation agent loaded successfully")
    except ImportError as e:
        _LOGGER.error(f"Failed to import report agent: {e}")
        _LOGGER.info("Make sure docgen_agent is properly configured")
        return
    
    # Generate reports
    _LOGGER.info("Generating reports (this may take several minutes)...")
    results = generate_reports(test_cases, agent)
    
    # Initialize judge model
    _LOGGER.info("Initializing judge model...")
    judge_llm = create_judge_llm()
    
    # Evaluate reports
    _LOGGER.info("Evaluating reports...")
    results = evaluate_reports(results, judge_llm)
    
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
        print("\n🎉 Excellent! Report agent is performing well across all metrics.")
        print("Consider testing on more diverse or challenging topics.")
    else:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")
    
    # Save results
    output_dir = Path(__file__).parent.parent / "data" / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_path = output_dir / "report_agent_results.csv"
    df.to_csv(results_path, index=False)
    _LOGGER.info(f"Results saved to {results_path}")
    
    summary_path = output_dir / "report_agent_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    _LOGGER.info(f"Summary saved to {summary_path}")
    
    print("\n" + "=" * 60)
    print("✅ Evaluation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

