"""
RAG evaluation tests using DeepEval.

These tests evaluate the quality of the RAG pipeline using standard metrics.
Requires DeepEval to be installed and OPENAI_API_KEY to be configured.

Skip Behavior:
- Tests are skipped if DeepEval is not installed
- Tests use pytest markers for easy filtering

Usage:
    # Run all RAG evaluation tests
    pytest tests/rag/ -v
    
    # Run only if DeepEval is available
    pytest tests/rag/ -v -m "not skip_without_deepeval"
"""

import json
import os
from pathlib import Path

import pytest

from exo.llmops.evaluate import (
    DEEPEVAL_AVAILABLE,
    evaluate_answer_relevancy,
    evaluate_faithfulness,
    evaluate_contextual_relevancy,
    run_rag_evaluation,
    load_golden_dataset,
)


# Skip all tests in this module if DeepEval is not available
pytestmark = pytest.mark.skipif(
    not DEEPEVAL_AVAILABLE,
    reason="DeepEval not installed"
)


# Path to golden dataset
GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"


class TestAnswerRelevancy:
    """Tests for answer relevancy metric."""

    def test_answer_relevancy_high_score(self) -> None:
        """Relevant answer should score high."""
        result = evaluate_answer_relevancy(
            query="What is the capital of France?",
            answer="The capital of France is Paris. It is located in the north-central part of the country.",
            threshold=0.7,
        )
        
        assert result.score >= 0.7
        assert result.passed is True

    def test_answer_relevancy_low_score(self) -> None:
        """Irrelevant answer should score low."""
        result = evaluate_answer_relevancy(
            query="What is the capital of France?",
            answer="I like pizza and ice cream. The weather is nice today.",
            threshold=0.7,
        )
        
        # Irrelevant answer should fail
        assert result.score < 0.7 or result.passed is False


class TestFaithfulness:
    """Tests for faithfulness metric."""

    def test_faithfulness_high_score(self) -> None:
        """Faithful answer should score high."""
        result = evaluate_faithfulness(
            query="What is the capital of France?",
            answer="Paris is the capital of France.",
            context=["France is a country in Western Europe. Paris is its capital city."],
            threshold=0.7,
        )
        
        assert result.score >= 0.7
        assert result.passed is True

    def test_faithfulness_hallucination(self) -> None:
        """Answer with hallucinations should score low."""
        result = evaluate_faithfulness(
            query="What is the capital of France?",
            answer="The capital of France is Lyon, which has a population of 10 million people.",
            context=["France is a country in Western Europe. Paris is its capital city."],
            threshold=0.7,
        )
        
        # Hallucinated answer should have lower score
        assert result.score < 1.0


class TestContextualRelevancy:
    """Tests for contextual relevancy metric."""

    def test_contextual_relevancy_high_score(self) -> None:
        """Relevant context should score high."""
        result = evaluate_contextual_relevancy(
            query="What is the capital of France?",
            context=[
                "France is a country in Western Europe.",
                "Paris is the capital and largest city of France.",
                "The Eiffel Tower is located in Paris.",
            ],
            threshold=0.7,
        )
        
        assert result.score >= 0.5  # Context relevancy can be strict
        assert result.passed is True

    def test_contextual_relevancy_irrelevant_context(self) -> None:
        """Irrelevant context should score low."""
        result = evaluate_contextual_relevancy(
            query="What is the capital of France?",
            context=[
                "Pizza is a popular Italian dish.",
                "The Great Wall of China is very long.",
                "Kangaroos live in Australia.",
            ],
            threshold=0.7,
        )
        
        # Completely irrelevant context should fail
        assert result.score < 0.7 or result.passed is False


class TestRunRagEvaluation:
    """Tests for full RAG evaluation pipeline."""

    def test_full_evaluation_passes(self) -> None:
        """Full RAG evaluation with good inputs should pass."""
        result = run_rag_evaluation(
            query="What is machine learning?",
            answer="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            context=[
                "Machine learning is a branch of artificial intelligence.",
                "It allows computers to learn patterns from data without explicit programming.",
            ],
            threshold=0.6,
        )
        
        assert not result.skipped
        assert result.answer_relevancy is not None
        assert result.faithfulness is not None
        assert result.contextual_relevancy is not None
        
        # With good inputs, average score should be reasonable
        assert result.average_score >= 0.5


class TestGoldenDataset:
    """Tests using the golden dataset."""

    def test_golden_dataset_exists(self) -> None:
        """Golden dataset file exists and is valid JSON."""
        assert GOLDEN_DATASET_PATH.exists(), "Golden dataset not found"
        
        with open(GOLDEN_DATASET_PATH) as f:
            data = json.load(f)
        
        assert "test_cases" in data
        assert len(data["test_cases"]) >= 5

    def test_golden_dataset_schema(self) -> None:
        """Golden dataset has correct schema."""
        dataset = load_golden_dataset(str(GOLDEN_DATASET_PATH))
        
        for case in dataset:
            assert "query" in case
            # Optional fields
            if "expected_answer" in case:
                assert isinstance(case["expected_answer"], str)
            if "context" in case:
                assert isinstance(case["context"], list)

    def test_evaluate_first_case(self) -> None:
        """Evaluate first test case from golden dataset."""
        dataset = load_golden_dataset(str(GOLDEN_DATASET_PATH))
        first_case = dataset[0]
        
        # If the case has context and expected answer, evaluate it
        if "context" in first_case and "expected_answer" in first_case:
            result = run_rag_evaluation(
                query=first_case["query"],
                answer=first_case["expected_answer"],
                context=first_case["context"],
                threshold=0.6,
            )
            
            # The golden dataset answers should be high quality
            assert result.average_score >= 0.5
