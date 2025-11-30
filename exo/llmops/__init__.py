"""
LLMOps module for Exo.

Provides observability and evaluation tooling for the RAG pipeline.

Usage:
    from exo.llmops import observe, evaluate
    
    # Observability with Langfuse
    @observe
    def my_function():
        ...
    
    # Evaluation with DeepEval
    from exo.llmops.evaluate import evaluate_rag
"""

from exo.llmops.observe import observe, trace_generation, get_langfuse_client
from exo.llmops.evaluate import (
    evaluate_answer_relevancy,
    evaluate_faithfulness,
    evaluate_contextual_relevancy,
    run_rag_evaluation,
    DEEPEVAL_AVAILABLE,
)

__all__ = [
    # Observability
    "observe",
    "trace_generation",
    "get_langfuse_client",
    # Evaluation
    "evaluate_answer_relevancy",
    "evaluate_faithfulness",
    "evaluate_contextual_relevancy",
    "run_rag_evaluation",
    "DEEPEVAL_AVAILABLE",
]
