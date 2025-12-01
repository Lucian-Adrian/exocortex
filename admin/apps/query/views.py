"""
Query views - RAG query interface.
"""

import asyncio
import json
import time
import logging

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

from admin.apps.core.models import ActivityLog
from admin.apps.core.utils import get_client_ip
from admin.apps.query.models import QueryHistory

logger = logging.getLogger("exo")


@staff_member_required
def query_page(request):
    """Main query page."""
    from admin.apps.core.services import get_supabase_client
    
    # Get recent queries for quick re-run
    recent_queries = QueryHistory.objects.filter(
        user=request.user
    ).order_by("-created_at")[:10]
    
    # Get source types for filter
    source_types = []
    try:
        client = get_supabase_client()
        source_response = client.table("memories").select("source_type").execute()
        source_types = list(set(
            item.get("source_type") 
            for item in source_response.data or [] 
            if item.get("source_type")
        ))
    except Exception:
        pass
    
    return render(request, "query/page.html", {
        "title": "Query Knowledge Base",
        "recent_queries": recent_queries,
        "source_types": sorted(source_types),
        "default_top_k": 5,
        "default_threshold": 0.5,
    })


@require_POST
@staff_member_required
def run_query(request):
    """Execute a RAG query."""
    from exo.schemas.query import QueryRequest
    from exo.pipeline import PipelineOrchestrator
    from exo.schemas.errors import ExoError
    
    question = request.POST.get("question", "").strip()
    top_k = int(request.POST.get("top_k", 5))
    threshold = float(request.POST.get("threshold", 0.5))
    
    if not question:
        messages.error(request, "Please enter a question.")
        return render(request, "query/query.html", {
            "title": "Query Knowledge Base",
            "error": "Please enter a question.",
        })
    
    try:
        start_time = time.time()
        
        # Create query request
        query_request = QueryRequest(
            question=question,
            top_k=top_k,
            similarity_threshold=threshold,
        )
        
        # Run the query
        orchestrator = PipelineOrchestrator()
        result = asyncio.run(orchestrator.query(query_request))
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        if isinstance(result, ExoError):
            logger.error(f"Query failed: {result.message}")
            return render(request, "query/query.html", {
                "title": "Query Knowledge Base",
                "error": result.message,
                "question": question,
            })
        
        # Save to history
        history = QueryHistory.objects.create(
            user=request.user,
            question=question,
            answer=result.answer,
            confidence=result.confidence,
            sources=[{
                "memory_id": s.memory_id,
                "content_preview": s.content_preview,
                "similarity": s.similarity,
            } for s in result.sources],
            commitments=result.commitments,
            parameters={"top_k": top_k, "threshold": threshold},
            execution_time_ms=execution_time_ms,
        )
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action="query",
            description=f"Query: {question[:100]}",
            metadata={
                "query_id": history.id,
                "confidence": result.confidence,
                "sources_count": len(result.sources),
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        logger.info(f"User {request.user} ran query: {question[:50]}...")
        
        return render(request, "query/result.html", {
            "title": "Query Result",
            "question": question,
            "result": result,
            "history": history,
            "execution_time_ms": execution_time_ms,
        })
        
    except Exception as e:
        logger.exception(f"Query error: {e}")
        return render(request, "query/query.html", {
            "title": "Query Knowledge Base",
            "error": str(e),
            "question": question,
        })


@require_POST
@staff_member_required
def api_query(request):
    """API endpoint for query (for AJAX)."""
    from exo.schemas.query import QueryRequest
    from exo.pipeline import PipelineOrchestrator
    from exo.schemas.errors import ExoError
    
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
        top_k = int(data.get("top_k", 5))
        threshold = float(data.get("threshold", 0.5))
        
        if not question:
            return JsonResponse({"error": "No question provided"}, status=400)
        
        start_time = time.time()
        
        query_request = QueryRequest(
            question=question,
            top_k=top_k,
            similarity_threshold=threshold,
        )
        
        orchestrator = PipelineOrchestrator()
        result = asyncio.run(orchestrator.query(query_request))
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        if isinstance(result, ExoError):
            return JsonResponse({
                "success": False,
                "error": result.message,
            }, status=400)
        
        # Save to history
        QueryHistory.objects.create(
            user=request.user,
            question=question,
            answer=result.answer,
            confidence=result.confidence,
            sources=[{
                "memory_id": s.memory_id,
                "content_preview": s.content_preview,
                "similarity": s.similarity,
            } for s in result.sources],
            commitments=result.commitments,
            parameters={"top_k": top_k, "threshold": threshold},
            execution_time_ms=execution_time_ms,
        )
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action="query",
            description=f"API Query: {question[:100]}",
            metadata={"confidence": result.confidence},
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        return JsonResponse({
            "success": True,
            "answer": result.answer,
            "confidence": result.confidence,
            "sources": [{
                "memory_id": s.memory_id,
                "content_preview": s.content_preview,
                "similarity": s.similarity,
            } for s in result.sources],
            "commitments": result.commitments,
            "execution_time_ms": execution_time_ms,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.exception(f"API query error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
@staff_member_required
def query_history(request):
    """View query history."""
    queries = QueryHistory.objects.filter(user=request.user).order_by("-created_at")[:100]
    
    return render(request, "query/history.html", {
        "title": "Query History",
        "queries": queries,
    })
