"""
RAG evaluation module for Exo using DeepEval.

Provides evaluation metrics for RAG pipelines:
- Answer Relevancy: Is the answer relevant to the question?
- Faithfulness: Is the answer faithful to the context?
- Contextual Relevancy: Is the retrieved context relevant?

Gracefully degrades when DeepEval is not installed.

Usage:
    from exo.llmops.evaluate import run_rag_evaluation

    result = run_rag_evaluation(
        query="What is the capital of France?",
        answer="The capital of France is Paris.",
        context=["France is a country in Europe. Paris is its capital."],
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Try to import DeepEval
try:
    from deepeval import evaluate as deepeval_evaluate
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        FaithfulnessMetric,
        ContextualRelevancyMetric,
    )
    from deepeval.test_case import LLMTestCase
    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False
    deepeval_evaluate = None  # type: ignore
    AnswerRelevancyMetric = None  # type: ignore
    FaithfulnessMetric = None  # type: ignore
    ContextualRelevancyMetric = None  # type: ignore
    LLMTestCase = None  # type: ignore


@dataclass
class EvaluationResult:
    """Result from a RAG evaluation."""
    
    metric_name: str
    score: float
    passed: bool
    reason: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "score": self.score,
            "passed": self.passed,
            "reason": self.reason,
        }


@dataclass
class RAGEvaluationResult:
    """Aggregate result from RAG evaluation."""
    
    answer_relevancy: EvaluationResult | None = None
    faithfulness: EvaluationResult | None = None
    contextual_relevancy: EvaluationResult | None = None
    skipped: bool = False
    skip_reason: str | None = None
    
    @property
    def all_passed(self) -> bool:
        """Check if all evaluations passed."""
        if self.skipped:
            return True  # Treat skipped as passed
        
        results = [
            self.answer_relevancy,
            self.faithfulness,
            self.contextual_relevancy,
        ]
        return all(r.passed for r in results if r is not None)
    
    @property
    def average_score(self) -> float:
        """Calculate average score across all metrics."""
        if self.skipped:
            return 0.0
        
        results = [
            self.answer_relevancy,
            self.faithfulness,
            self.contextual_relevancy,
        ]
        scores = [r.score for r in results if r is not None]
        return sum(scores) / len(scores) if scores else 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "skipped": self.skipped,
            "all_passed": self.all_passed,
            "average_score": self.average_score,
        }
        
        if self.skip_reason:
            result["skip_reason"] = self.skip_reason
        
        if self.answer_relevancy:
            result["answer_relevancy"] = self.answer_relevancy.to_dict()
        if self.faithfulness:
            result["faithfulness"] = self.faithfulness.to_dict()
        if self.contextual_relevancy:
            result["contextual_relevancy"] = self.contextual_relevancy.to_dict()
        
        return result


def evaluate_answer_relevancy(
    query: str,
    answer: str,
    threshold: float = 0.7,
) -> EvaluationResult:
    """
    Evaluate if the answer is relevant to the query.
    
    Args:
        query: The user's question
        answer: The generated answer
        threshold: Minimum score to pass (0.0 - 1.0)
    
    Returns:
        EvaluationResult with score and pass/fail status
    """
    if not DEEPEVAL_AVAILABLE:
        return EvaluationResult(
            metric_name="answer_relevancy",
            score=0.0,
            passed=True,  # Pass when skipped
            reason="DeepEval not installed - skipped",
        )
    
    try:
        test_case = LLMTestCase(
            input=query,
            actual_output=answer,
        )
        
        metric = AnswerRelevancyMetric(threshold=threshold)
        metric.measure(test_case)
        
        return EvaluationResult(
            metric_name="answer_relevancy",
            score=metric.score or 0.0,
            passed=metric.is_successful(),
            reason=metric.reason,
        )
    except Exception as e:
        return EvaluationResult(
            metric_name="answer_relevancy",
            score=0.0,
            passed=False,
            reason=f"Evaluation error: {e}",
        )


def evaluate_faithfulness(
    query: str,
    answer: str,
    context: list[str],
    threshold: float = 0.7,
) -> EvaluationResult:
    """
    Evaluate if the answer is faithful to the provided context.
    
    The answer should only contain information present in the context.
    
    Args:
        query: The user's question
        answer: The generated answer
        context: List of context strings used to generate the answer
        threshold: Minimum score to pass (0.0 - 1.0)
    
    Returns:
        EvaluationResult with score and pass/fail status
    """
    if not DEEPEVAL_AVAILABLE:
        return EvaluationResult(
            metric_name="faithfulness",
            score=0.0,
            passed=True,  # Pass when skipped
            reason="DeepEval not installed - skipped",
        )
    
    try:
        test_case = LLMTestCase(
            input=query,
            actual_output=answer,
            retrieval_context=context,
        )
        
        metric = FaithfulnessMetric(threshold=threshold)
        metric.measure(test_case)
        
        return EvaluationResult(
            metric_name="faithfulness",
            score=metric.score or 0.0,
            passed=metric.is_successful(),
            reason=metric.reason,
        )
    except Exception as e:
        return EvaluationResult(
            metric_name="faithfulness",
            score=0.0,
            passed=False,
            reason=f"Evaluation error: {e}",
        )


def evaluate_contextual_relevancy(
    query: str,
    context: list[str],
    threshold: float = 0.7,
) -> EvaluationResult:
    """
    Evaluate if the retrieved context is relevant to the query.
    
    Args:
        query: The user's question
        context: List of retrieved context strings
        threshold: Minimum score to pass (0.0 - 1.0)
    
    Returns:
        EvaluationResult with score and pass/fail status
    """
    if not DEEPEVAL_AVAILABLE:
        return EvaluationResult(
            metric_name="contextual_relevancy",
            score=0.0,
            passed=True,  # Pass when skipped
            reason="DeepEval not installed - skipped",
        )
    
    try:
        # Contextual relevancy needs an answer for the test case
        test_case = LLMTestCase(
            input=query,
            actual_output="",  # Not used for this metric
            retrieval_context=context,
        )
        
        metric = ContextualRelevancyMetric(threshold=threshold)
        metric.measure(test_case)
        
        return EvaluationResult(
            metric_name="contextual_relevancy",
            score=metric.score or 0.0,
            passed=metric.is_successful(),
            reason=metric.reason,
        )
    except Exception as e:
        return EvaluationResult(
            metric_name="contextual_relevancy",
            score=0.0,
            passed=False,
            reason=f"Evaluation error: {e}",
        )


def run_rag_evaluation(
    query: str,
    answer: str,
    context: list[str],
    threshold: float = 0.7,
) -> RAGEvaluationResult:
    """
    Run all RAG evaluation metrics.
    
    This is a convenience function that runs all three standard metrics:
    - Answer Relevancy
    - Faithfulness
    - Contextual Relevancy
    
    Args:
        query: The user's question
        answer: The generated answer
        context: List of context strings used to generate the answer
        threshold: Minimum score to pass all metrics (0.0 - 1.0)
    
    Returns:
        RAGEvaluationResult with all metric results
    
    Example:
        result = run_rag_evaluation(
            query="What is the capital of France?",
            answer="Paris is the capital of France.",
            context=["France is a country. Paris is its capital city."],
        )
        
        if result.all_passed:
            print("All evaluations passed!")
        print(f"Average score: {result.average_score:.2f}")
    """
    if not DEEPEVAL_AVAILABLE:
        return RAGEvaluationResult(
            skipped=True,
            skip_reason="DeepEval not installed",
        )
    
    return RAGEvaluationResult(
        answer_relevancy=evaluate_answer_relevancy(query, answer, threshold),
        faithfulness=evaluate_faithfulness(query, answer, context, threshold),
        contextual_relevancy=evaluate_contextual_relevancy(query, context, threshold),
    )


def load_golden_dataset(path: str) -> list[dict[str, Any]]:
    """
    Load a golden dataset from a JSON file.
    
    The file should contain an array of test cases with:
    - query: The user's question
    - expected_answer: The expected answer (optional)
    - context: List of context strings (optional)
    
    Args:
        path: Path to the JSON file
    
    Returns:
        List of test case dictionaries
    """
    import json
    
    with open(path) as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "test_cases" in data:
        return data["test_cases"]
    
    if isinstance(data, list):
        return data
    
    raise ValueError(f"Invalid golden dataset format in {path}")


def evaluate_golden_dataset(
    path: str,
    answer_generator: Any,  # Callable that takes query and returns answer
    context_retriever: Any,  # Callable that takes query and returns context list
    threshold: float = 0.7,
) -> list[RAGEvaluationResult]:
    """
    Evaluate a RAG pipeline against a golden dataset.
    
    Args:
        path: Path to the golden dataset JSON file
        answer_generator: Function that generates answers (query -> answer)
        context_retriever: Function that retrieves context (query -> list[str])
        threshold: Minimum score to pass
    
    Returns:
        List of RAGEvaluationResult for each test case
    """
    if not DEEPEVAL_AVAILABLE:
        return []
    
    dataset = load_golden_dataset(path)
    results = []
    
    for case in dataset:
        query = case["query"]
        context = case.get("context") or context_retriever(query)
        answer = answer_generator(query)
        
        result = run_rag_evaluation(query, answer, context, threshold)
        results.append(result)
    
    return results
