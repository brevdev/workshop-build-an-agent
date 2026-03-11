"""
Evaluation framework for AI agents using RAGAS and LLM-as-a-judge techniques.

This module provides utilities for evaluating both RAG agents and task-based agents
using NVIDIA models and industry-standard metrics.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from pydantic import BaseModel

_LOGGER = logging.getLogger(__name__)

# Model Configuration
JUDGE_MODEL = "nvidia/nemotron-3-super-120b-a12b"
EMBEDDING_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"


class EvaluationResult(BaseModel):
    """Structured evaluation result."""
    score: float
    explanation: str
    metric_name: str


class RAGEvaluationResult(BaseModel):
    """Complete RAG evaluation results."""
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    custom_scores: Dict[str, float] = {}


def create_judge_llm(temperature: float = 0.0) -> ChatNVIDIA:
    """
    Create an LLM instance for use as a judge.
    
    Args:
        temperature: Temperature for the model (0.0 for consistent evaluation)
        
    Returns:
        ChatNVIDIA instance configured for evaluation
    """
    return ChatNVIDIA(
        model=JUDGE_MODEL,
        temperature=temperature,
        max_tokens=4096,
    )


def create_embeddings() -> NVIDIAEmbeddings:
    """
    Create embeddings model for semantic similarity.
    
    Returns:
        NVIDIAEmbeddings instance
    """
    return NVIDIAEmbeddings(
        model=EMBEDDING_MODEL,
        truncate="END"
    )


# Evaluation Prompt Templates

FAITHFULNESS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert evaluator assessing whether AI responses are faithful to provided context."),
    ("user", """
Evaluate the faithfulness of this response to the given context.

Context:
{context}

Question: {question}

Response: {response}

Faithfulness means every claim in the response is supported by the context.

TODO: ...

Provide your evaluation as JSON:
{{
  "score": <1-5>,
  "explanation": "<brief explanation of your rating>"
}}
""")
])


RELEVANCY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert evaluator assessing whether AI responses are relevant to questions."),
    ("user", """
Evaluate how relevant this response is to the question.

Question: {question}

Response: {response}

Relevancy means the response directly addresses what was asked.

Rate relevancy on a scale of 1-5:
- 5: Directly and completely answers the question
- 4: Mostly answers the question, minor tangents
- 3: Partially answers the question
- 2: Barely addresses the question
- 1: Does not answer the question

Provide your evaluation as JSON:
{{
  "score": <1-5>,
  "explanation": "<brief explanation of your rating>"
}}
""")
])


HELPFULNESS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert evaluator assessing whether AI responses are helpful to users."),
    ("user", """
Evaluate how helpful this response would be to a user.

Question: {question}

Response: {response}

Consider:
- Does it provide actionable information?
- Is it clear and easy to understand?
- Does it anticipate follow-up needs?

Rate helpfulness on a scale of 1-5:
- 5: Extremely helpful, clear, actionable
- 4: Very helpful with minor room for improvement
- 3: Moderately helpful
- 2: Somewhat helpful but lacking
- 1: Not helpful

Provide your evaluation as JSON:
{{
  "score": <1-5>,
  "explanation": "<brief explanation of your rating>"
}}
""")
])


REPORT_QUALITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert evaluator assessing the quality of research reports."),
    ("user", """
Evaluate this research report on the topic: {topic}

Report:
{report}

Expected sections: {expected_sections}
{quality_criteria_text}
Evaluate on these criteria (1-5 scale each):

Rate Structure on a scale of 1-5: Are all expected sections present and well-organized?
- 5: All sections present and well-organized
- 4: Most sections present and generally organized
- 3: Some sections present and organization is lacking
- 2: Few sections present and not well organized
- 1: No sections present and not well organized

Rate Content Quality on a scale of 1-5: Is the information substantive and relevant?
- 5: All information is both relevant and substantive
- 4: Most information is both relevant and substantive
- 3: Some information is both relevant and substantive
- 2: Most information irrelevant or of little substance
- 1: None of the information is relevant or substantive

Rate Content Coverage on a scale of 1-5: Are relevant topics covered and irrelevant ones avoided?
- 5: All "should include" points are present and all "should avoid" are not present
- 4: Most "should include" points are present and most "should avoid" are not present
- 3: Some "should include" points are present or some "should avoid" are not present
- 2: Few "should include" points are present or few "should avoid" are not present
- 1: No "should include" points are present or all "should avoid" are present

Rate Accuracy on a scale of 1-5: Are claims well-supported and factual?
- 5: All sections factual and well-supported
- 4: Most sections factual and well-supported
- 3: Some sections factual and well-supported
- 2: Few sections factual and well-supported
- 1: No sections factual and well-supported

Rate Writing Quality on a scale of 1-5: Is it clear, professional, and well-written?
- 5: All sections clear, professional, and well-written
- 4: Most sections clear, professional, and well-written
- 3: Some sections clear, professional, and well-written
- 2: Few sections clear, professional, and well-written
- 1: No sections clear, professional, and well-written

Provide your evaluation as JSON:
{{
  "structure": {{"score": <1-5>, "explanation": "..."}},
  "content": {{"score": <1-5>, "explanation": "..."}},
  "coverage": {{"score": <1-5>, "explanation": "..."}},
  "accuracy": {{"score": <1-5>, "explanation": "..."}},
  "writing": {{"score": <1-5>, "explanation": "..."}}
}}
""")
])


def evaluate_faithfulness(
    question: str,
    response: str,
    context: str,
    judge_llm: Optional[ChatNVIDIA] = None
) -> EvaluationResult:
    """
    Evaluate faithfulness of a response to context using LLM-as-a-judge.

    Args:
        question: The user's question
        response: The agent's response
        context: The context provided to the agent
        judge_llm: Optional judge model (creates one if not provided)

    Returns:
        EvaluationResult with score and explanation
    """
    if judge_llm is None:
        judge_llm = create_judge_llm()

    chain = FAITHFULNESS_PROMPT | judge_llm

    try:
        result = chain.invoke({
            "question": question,
            "response": response,
            "context": context
        })
    except Exception as e:
        _LOGGER.error(f"LLM invocation failed: {type(e).__name__}: {e}")
        return EvaluationResult(
            score=0.0,
            explanation=f"LLM call failed: {type(e).__name__}",
            metric_name="faithfulness"
        )

    try:
        parsed = json.loads(result.content)
        return EvaluationResult(
            score=float(parsed["score"]),
            explanation=parsed["explanation"],
            metric_name="faithfulness"
        )
    except json.JSONDecodeError:
        _LOGGER.warning(f"Judge returned invalid JSON for faithfulness evaluation")
        _LOGGER.debug(f"Raw output: {result.content[:200]}")
        # Fallback: try to extract score from text
        import re
        score_match = re.search(r'"?score"?\s*:\s*(\d+)', result.content)
        if score_match:
            _LOGGER.info(f"Extracted score from text: {score_match.group(1)}")
            return EvaluationResult(
                score=float(score_match.group(1)),
                explanation="Extracted from malformed JSON",
                metric_name="faithfulness"
            )
        return EvaluationResult(
            score=0.0,
            explanation="Failed to parse evaluation - invalid JSON format",
            metric_name="faithfulness"
        )
    except KeyError as e:
        _LOGGER.warning(f"Missing expected field in faithfulness evaluation: {e}")
        _LOGGER.debug(f"Parsed content: {parsed}")
        return EvaluationResult(
            score=0.0,
            explanation=f"Missing required field: {e}",
            metric_name="faithfulness"
        )


def evaluate_relevancy(
    question: str,
    response: str,
    judge_llm: Optional[ChatNVIDIA] = None
) -> EvaluationResult:
    """
    Evaluate relevancy of a response to the question using LLM-as-a-judge.

    Args:
        question: The user's question
        response: The agent's response
        judge_llm: Optional judge model (creates one if not provided)

    Returns:
        EvaluationResult with score and explanation
    """
    if judge_llm is None:
        judge_llm = create_judge_llm()

    chain = RELEVANCY_PROMPT | judge_llm

    try:
        result = chain.invoke({
            "question": question,
            "response": response
        })
    except Exception as e:
        _LOGGER.error(f"LLM invocation failed: {type(e).__name__}: {e}")
        return EvaluationResult(
            score=0.0,
            explanation=f"LLM call failed: {type(e).__name__}",
            metric_name="relevancy"
        )

    try:
        parsed = json.loads(result.content)
        return EvaluationResult(
            score=float(parsed["score"]),
            explanation=parsed["explanation"],
            metric_name="relevancy"
        )
    except json.JSONDecodeError:
        _LOGGER.warning(f"Judge returned invalid JSON for relevancy evaluation")
        import re
        score_match = re.search(r'"?score"?\s*:\s*(\d+)', result.content)
        if score_match:
            return EvaluationResult(
                score=float(score_match.group(1)),
                explanation="Extracted from malformed JSON",
                metric_name="relevancy"
            )
        return EvaluationResult(
            score=0.0,
            explanation="Failed to parse evaluation - invalid JSON format",
            metric_name="relevancy"
        )
    except KeyError as e:
        _LOGGER.warning(f"Missing expected field in relevancy evaluation: {e}")
        return EvaluationResult(
            score=0.0,
            explanation=f"Missing required field: {e}",
            metric_name="relevancy"
        )


def evaluate_helpfulness(
    question: str,
    response: str,
    judge_llm: Optional[ChatNVIDIA] = None
) -> EvaluationResult:
    """
    Evaluate helpfulness of a response using LLM-as-a-judge.

    Args:
        question: The user's question
        response: The agent's response
        judge_llm: Optional judge model (creates one if not provided)

    Returns:
        EvaluationResult with score and explanation
    """
    if judge_llm is None:
        judge_llm = create_judge_llm()

    chain = HELPFULNESS_PROMPT | judge_llm

    try:
        result = chain.invoke({
            "question": question,
            "response": response
        })
    except Exception as e:
        _LOGGER.error(f"LLM invocation failed: {type(e).__name__}: {e}")
        return EvaluationResult(
            score=0.0,
            explanation=f"LLM call failed: {type(e).__name__}",
            metric_name="helpfulness"
        )

    try:
        parsed = json.loads(result.content)
        return EvaluationResult(
            score=float(parsed["score"]),
            explanation=parsed["explanation"],
            metric_name="helpfulness"
        )
    except json.JSONDecodeError:
        _LOGGER.warning(f"Judge returned invalid JSON for helpfulness evaluation")
        import re
        score_match = re.search(r'"?score"?\s*:\s*(\d+)', result.content)
        if score_match:
            return EvaluationResult(
                score=float(score_match.group(1)),
                explanation="Extracted from malformed JSON",
                metric_name="helpfulness"
            )
        return EvaluationResult(
            score=0.0,
            explanation="Failed to parse evaluation - invalid JSON format",
            metric_name="helpfulness"
        )
    except KeyError as e:
        _LOGGER.warning(f"Missing expected field in helpfulness evaluation: {e}")
        return EvaluationResult(
            score=0.0,
            explanation=f"Missing required field: {e}",
            metric_name="helpfulness"
        )


def evaluate_report_quality(
    topic: str,
    report: str,
    expected_sections: List[str],
    quality_criteria: Optional[Dict[str, Any]] = None,
    judge_llm: Optional[ChatNVIDIA] = None
) -> Dict[str, EvaluationResult]:
    """
    Evaluate the quality of a generated report using LLM-as-a-judge.

    Args:
        topic: The report topic
        report: The generated report content
        expected_sections: List of sections that should be present
        quality_criteria: Optional dict with 'should_include' and 'should_avoid' lists
        judge_llm: Optional judge model (creates one if not provided)

    Returns:
        Dictionary mapping criteria to EvaluationResults
    """
    if judge_llm is None:
        judge_llm = create_judge_llm()

    # Format quality criteria into text for the prompt
    quality_criteria_text = ""
    if quality_criteria:
        parts = []
        if quality_criteria.get("should_include"):
            parts.append("The report SHOULD include: " + ", ".join(quality_criteria["should_include"]))
        if quality_criteria.get("should_avoid"):
            parts.append("The report SHOULD avoid: " + ", ".join(quality_criteria["should_avoid"]))
        if parts:
            quality_criteria_text = "\nQuality criteria:\n" + "\n".join(f"- {p}" for p in parts)

    chain = REPORT_QUALITY_PROMPT | judge_llm

    result = chain.invoke({
        "topic": topic,
        "report": report,
        "expected_sections": ", ".join(expected_sections),
        "quality_criteria_text": quality_criteria_text
    })
    
    try:
        parsed = json.loads(result.content)
        return {
            criterion: EvaluationResult(
                score=float(data["score"]),
                explanation=data["explanation"],
                metric_name=criterion
            )
            for criterion, data in parsed.items()
        }
    except (json.JSONDecodeError, KeyError) as e:
        _LOGGER.warning(f"Failed to parse report evaluation: {e}")
        return {
            "structure": EvaluationResult(score=0.0, explanation="Parse failed", metric_name="structure"),
            "content": EvaluationResult(score=0.0, explanation="Parse failed", metric_name="content"),
            "accuracy": EvaluationResult(score=0.0, explanation="Parse failed", metric_name="accuracy"),
            "writing": EvaluationResult(score=0.0, explanation="Parse failed", metric_name="writing"),
        }


def evaluate_rag_response(
    question: str,
    response: str,
    context: str,
    judge_llm: Optional[ChatNVIDIA] = None
) -> Dict[str, EvaluationResult]:
    """
    Comprehensive evaluation of a RAG agent response.
    
    Args:
        question: The user's question
        response: The agent's response
        context: The context provided to the agent
        judge_llm: Optional judge model (creates one if not provided)
        
    Returns:
        Dictionary mapping metric names to EvaluationResults
    """
    if judge_llm is None:
        judge_llm = create_judge_llm()
    
    return {
        "faithfulness": evaluate_faithfulness(question, response, context, judge_llm),
        "relevancy": evaluate_relevancy(question, response, judge_llm),
        "helpfulness": evaluate_helpfulness(question, response, judge_llm),
    }


def calculate_aggregate_score(results: Dict[str, EvaluationResult]) -> float:
    """
    Calculate aggregate score from multiple evaluation results.
    
    Args:
        results: Dictionary of evaluation results
        
    Returns:
        Average score normalized to 0-1 range
    """
    if not results:
        return 0.0
    
    scores = [r.score for r in results.values()]
    return sum(scores) / len(scores) / 5.0  # Normalize from 1-5 scale to 0-1

