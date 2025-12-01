"""
Integration views for LangChain, n8n, and Langfuse.
"""
import os
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def langchain_view(request):
    """LangChain integration page - ExoRetriever usage and configuration."""
    context = {
        "page_title": "LangChain Integration",
        "retriever_code": '''
from exocortex.retriever import ExoRetriever
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize the ExoRetriever
retriever = ExoRetriever(
    top_k=5,  # Number of relevant documents to retrieve
)

# Create LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")

# Build RAG Chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
)

# Query with full RAG
result = qa_chain.invoke({"query": "What are my commitments?"})
print(result["result"])
print(result["source_documents"])
''',
        "retriever_docs": """
## ExoRetriever

The `ExoRetriever` class implements LangChain's `BaseRetriever` interface, 
enabling seamless integration with LangChain chains and agents.

### Features

- **Semantic Search**: Uses vector embeddings for semantic similarity search
- **Configurable Top-K**: Control how many documents are retrieved
- **Source Tracking**: Returns source metadata with each document
- **Filter Support**: Filter by source type, date range, tags

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top_k` | int | 5 | Number of documents to retrieve |
| `similarity_threshold` | float | 0.7 | Minimum similarity score |
| `filter_source` | str | None | Filter by source type |

### Usage in Chains

The retriever works with all LangChain chain types:
- RetrievalQA
- ConversationalRetrievalChain
- MultiQueryRetriever
- ContextualCompressionRetriever
""",
        "env_vars": {
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", "")[:8] + "..." if os.getenv("GOOGLE_API_KEY") else "Not set",
            "SUPABASE_URL": os.getenv("SUPABASE_URL", "Not set"),
            "EMBED_MODEL": os.getenv("EMBED_MODEL", "models/text-embedding-004"),
        },
    }
    return render(request, "integrations/langchain.html", context)


@login_required
def n8n_view(request):
    """n8n integration page - Webhook endpoints and automation."""
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    context = {
        "page_title": "n8n Webhooks",
        "api_base": api_base,
        "webhooks": [
            {
                "name": "Ingest Content",
                "method": "POST",
                "endpoint": f"{api_base}/ingest",
                "description": "Ingest new content into Exocortex memory",
                "payload": '''{
  "content": "Meeting notes from today...",
  "source": "n8n-automation",
  "metadata": {
    "type": "meeting_notes",
    "timestamp": "2024-01-15T10:00:00Z"
  }
}''',
                "response": '''{
  "id": "mem_abc123",
  "status": "success",
  "summary": "Meeting discussed project timeline...",
  "entities": ["project", "timeline", "deadline"]
}''',
            },
            {
                "name": "Query Knowledge",
                "method": "POST",
                "endpoint": f"{api_base}/query",
                "description": "Query the knowledge base with semantic search",
                "payload": '''{
  "query": "What are my deadlines this week?",
  "top_k": 5,
  "include_sources": true
}''',
                "response": '''{
  "answer": "Based on your records...",
  "sources": [
    {"id": "mem_123", "score": 0.92, "preview": "..."}
  ],
  "confidence": 0.85
}''',
            },
            {
                "name": "Batch Ingest",
                "method": "POST",
                "endpoint": f"{api_base}/ingest/batch",
                "description": "Ingest multiple documents at once",
                "payload": '''{
  "documents": [
    {"content": "Doc 1...", "source": "slack"},
    {"content": "Doc 2...", "source": "email"}
  ]
}''',
                "response": '''{
  "processed": 2,
  "failed": 0,
  "ids": ["mem_1", "mem_2"]
}''',
            },
            {
                "name": "Get Commitments",
                "method": "GET",
                "endpoint": f"{api_base}/commitments",
                "description": "Retrieve all extracted commitments/tasks",
                "payload": "Query params: ?status=open&limit=10",
                "response": '''{
  "commitments": [
    {
      "id": "com_123",
      "text": "Submit report by Friday",
      "due_date": "2024-01-19",
      "status": "open",
      "source_memory_id": "mem_456"
    }
  ],
  "total": 5
}''',
            },
        ],
        "n8n_workflow_example": '''
{
  "name": "Slack to Exocortex",
  "nodes": [
    {
      "type": "n8n-nodes-base.slack",
      "name": "Slack Trigger",
      "parameters": {
        "event": "message"
      }
    },
    {
      "type": "n8n-nodes-base.httpRequest",
      "name": "Ingest to Exocortex",
      "parameters": {
        "method": "POST",
        "url": "''' + api_base + '''/ingest",
        "body": {
          "content": "={{$json.text}}",
          "source": "slack",
          "metadata": {
            "channel": "={{$json.channel}}"
          }
        }
      }
    }
  ]
}
''',
    }
    return render(request, "integrations/n8n.html", context)


@login_required
def langfuse_view(request):
    """Langfuse observability page - LLMOps monitoring."""
    context = {
        "page_title": "Langfuse Observability",
        "langfuse_url": os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        "public_key": os.getenv("LANGFUSE_PUBLIC_KEY", "")[:12] + "..." if os.getenv("LANGFUSE_PUBLIC_KEY") else "Not configured",
        "secret_key": os.getenv("LANGFUSE_SECRET_KEY", "")[:8] + "..." if os.getenv("LANGFUSE_SECRET_KEY") else "Not configured",
        "features": [
            {
                "name": "Trace Logging",
                "description": "Automatic logging of all LLM calls with inputs, outputs, latency, and token usage",
                "icon": "📊",
            },
            {
                "name": "Cost Tracking",
                "description": "Track API costs per model, per user, and per session",
                "icon": "💰",
            },
            {
                "name": "Quality Scoring",
                "description": "Score outputs for quality, relevance, and accuracy",
                "icon": "⭐",
            },
            {
                "name": "Session Replay",
                "description": "Replay conversation sessions to debug issues",
                "icon": "🔄",
            },
            {
                "name": "A/B Testing",
                "description": "Compare different prompts and model configurations",
                "icon": "🧪",
            },
            {
                "name": "Alerting",
                "description": "Set up alerts for errors, high latency, or cost thresholds",
                "icon": "🔔",
            },
        ],
        "setup_code": '''
# .env configuration
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# Usage in code
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

langfuse = Langfuse()

# Create trace for a session
trace = langfuse.trace(
    name="exocortex-query",
    user_id="user-123",
    metadata={"source": "api"}
)

# Integrate with LangChain
handler = CallbackHandler()
chain.invoke({"query": "..."}, config={"callbacks": [handler]})
''',
        "metrics": [
            {"name": "Total Traces", "value": "—", "trend": "Connect to view"},
            {"name": "Avg Latency", "value": "—", "trend": "Connect to view"},
            {"name": "Token Usage", "value": "—", "trend": "Connect to view"},
            {"name": "Est. Cost", "value": "—", "trend": "Connect to view"},
        ],
    }
    return render(request, "integrations/langfuse.html", context)


@login_required
def deepeval_view(request):
    """DeepEval evaluation page - LLM testing and evaluation."""
    context = {
        "page_title": "DeepEval Testing",
        "features": [
            {
                "name": "Unit Tests for LLMs",
                "description": "Write pytest-style tests for your LLM outputs",
                "icon": "🧪",
            },
            {
                "name": "RAG Metrics",
                "description": "Measure faithfulness, answer relevancy, and contextual recall",
                "icon": "📏",
            },
            {
                "name": "Hallucination Detection",
                "description": "Automatically detect when LLM outputs hallucinate information",
                "icon": "🎭",
            },
            {
                "name": "Regression Testing",
                "description": "Track quality over time and catch regressions",
                "icon": "📈",
            },
        ],
        "test_code": '''
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRecallMetric,
)

def test_exocortex_query():
    """Test that Exocortex returns relevant answers."""
    test_case = LLMTestCase(
        input="What are my commitments for this week?",
        actual_output=query_result.answer,
        retrieval_context=[doc.page_content for doc in query_result.sources],
        expected_output="List of commitments extracted from documents"
    )
    
    # Check answer relevancy
    relevancy = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [relevancy])
    
    # Check faithfulness (no hallucination)
    faithfulness = FaithfulnessMetric(threshold=0.8)
    assert_test(test_case, [faithfulness])

# Run with: deepeval test run test_exocortex.py
''',
        "metrics_explanation": """
## RAG Metrics Explained

### Faithfulness
Measures whether the answer is grounded in the retrieved context.
High faithfulness = No hallucination.

### Answer Relevancy  
Measures how relevant the answer is to the original question.
Does the answer actually address what was asked?

### Contextual Recall
Measures whether the retrieval found all relevant documents.
Did we retrieve everything we needed?

### Contextual Precision
Measures whether retrieved documents are actually relevant.
Did we retrieve only what we needed?
""",
    }
    return render(request, "integrations/deepeval.html", context)
