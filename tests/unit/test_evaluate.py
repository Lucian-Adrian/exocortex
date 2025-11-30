"""
Unit tests for the evaluate module.
"""

import pytest

from exo.llmops.evaluate import (
    EvaluationResult,
    RAGEvaluationResult,
    evaluate_answer_relevancy,
    evaluate_faithfulness,
    evaluate_contextual_relevancy,
    run_rag_evaluation,
    DEEPEVAL_AVAILABLE,
)


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_to_dict(self) -> None:
        """Converts to dictionary correctly."""
        result = EvaluationResult(
            metric_name="test_metric",
            score=0.85,
            passed=True,
            reason="Good result",
        )
        
        d = result.to_dict()
        assert d["metric_name"] == "test_metric"
        assert d["score"] == 0.85
        assert d["passed"] is True
        assert d["reason"] == "Good result"

    def test_to_dict_without_reason(self) -> None:
        """Handles missing reason."""
        result = EvaluationResult(
            metric_name="test",
            score=0.5,
            passed=False,
        )
        
        d = result.to_dict()
        assert d["reason"] is None


class TestRAGEvaluationResult:
    """Tests for RAGEvaluationResult dataclass."""

    def test_all_passed_when_all_pass(self) -> None:
        """all_passed is True when all metrics pass."""
        result = RAGEvaluationResult(
            answer_relevancy=EvaluationResult("ar", 0.9, True),
            faithfulness=EvaluationResult("f", 0.85, True),
            contextual_relevancy=EvaluationResult("cr", 0.8, True),
        )
        
        assert result.all_passed is True

    def test_all_passed_when_one_fails(self) -> None:
        """all_passed is False when any metric fails."""
        result = RAGEvaluationResult(
            answer_relevancy=EvaluationResult("ar", 0.9, True),
            faithfulness=EvaluationResult("f", 0.5, False),
            contextual_relevancy=EvaluationResult("cr", 0.8, True),
        )
        
        assert result.all_passed is False

    def test_all_passed_when_skipped(self) -> None:
        """all_passed is True when evaluation is skipped."""
        result = RAGEvaluationResult(skipped=True, skip_reason="No deepeval")
        
        assert result.all_passed is True

    def test_average_score(self) -> None:
        """Calculates average score correctly."""
        result = RAGEvaluationResult(
            answer_relevancy=EvaluationResult("ar", 0.9, True),
            faithfulness=EvaluationResult("f", 0.8, True),
            contextual_relevancy=EvaluationResult("cr", 0.7, True),
        )
        
        assert result.average_score == pytest.approx(0.8, rel=0.01)

    def test_average_score_when_skipped(self) -> None:
        """Average score is 0 when skipped."""
        result = RAGEvaluationResult(skipped=True)
        assert result.average_score == 0.0

    def test_to_dict(self) -> None:
        """Converts to dictionary correctly."""
        result = RAGEvaluationResult(
            answer_relevancy=EvaluationResult("ar", 0.9, True),
        )
        
        d = result.to_dict()
        assert d["skipped"] is False
        assert d["all_passed"] is True
        assert "answer_relevancy" in d


class TestGracefulSkip:
    """Tests for graceful skip when DeepEval not installed."""

    def test_evaluate_answer_relevancy_graceful_skip(self) -> None:
        """Answer relevancy evaluation gracefully skips."""
        result = evaluate_answer_relevancy(
            query="What is the capital of France?",
            answer="Paris",
        )
        
        # Should return a result either way
        assert isinstance(result, EvaluationResult)
        assert result.metric_name == "answer_relevancy"
        
        if not DEEPEVAL_AVAILABLE:
            assert result.passed is True  # Passes when skipped
            assert "not installed" in (result.reason or "").lower() or "skipped" in (result.reason or "").lower()

    def test_evaluate_faithfulness_graceful_skip(self) -> None:
        """Faithfulness evaluation gracefully skips."""
        result = evaluate_faithfulness(
            query="What is the capital of France?",
            answer="Paris is the capital.",
            context=["Paris is the capital of France."],
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.metric_name == "faithfulness"
        
        if not DEEPEVAL_AVAILABLE:
            assert result.passed is True

    def test_evaluate_contextual_relevancy_graceful_skip(self) -> None:
        """Contextual relevancy evaluation gracefully skips."""
        result = evaluate_contextual_relevancy(
            query="What is the capital of France?",
            context=["Paris is the capital of France."],
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.metric_name == "contextual_relevancy"
        
        if not DEEPEVAL_AVAILABLE:
            assert result.passed is True

    def test_run_rag_evaluation_graceful_skip(self) -> None:
        """Full RAG evaluation gracefully skips."""
        result = run_rag_evaluation(
            query="What is the capital of France?",
            answer="Paris",
            context=["France is a country. Paris is its capital."],
        )
        
        assert isinstance(result, RAGEvaluationResult)
        
        if not DEEPEVAL_AVAILABLE:
            assert result.skipped is True
            assert result.skip_reason == "DeepEval not installed"
            assert result.all_passed is True  # Skipped counts as passed
