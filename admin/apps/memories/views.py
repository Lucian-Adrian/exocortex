"""
Memories views - List, detail, delete memories.

Optimized: Uses sync functions, parallel queries, no asyncio overhead.
"""

from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET

from admin.apps.core.services import (
    get_supabase_client, 
    get_memory_by_id_sync, 
    get_memories_list,
    search_memories_sync,
    invalidate_stats_cache,
)
from admin.apps.core.models import ActivityLog
from admin.apps.core.utils import get_client_ip


@staff_member_required
def memory_list(request):
    """List all memories with filters."""
    source_type = request.GET.get("source_type", "")
    ordering = request.GET.get("ordering", "-created_at")
    has_commitments = request.GET.get("has_commitments", "") == "true"
    search = request.GET.get("search", "")
    
    try:
        # Optimized: parallel fetch of memories and source types
        memories, source_types = get_memories_list(
            source_type=source_type,
            ordering=ordering,
            has_commitments=has_commitments,
            search=search,
            limit=100,
        )
    except Exception as e:
        memories = []
        source_types = []
        messages.error(request, f"Error loading memories: {e}")
    
    return render(request, "memories/list.html", {
        "title": "Memories",
        "memories": memories,
        "source_types": source_types,
        "current_source_type": source_type,
        "current_ordering": ordering,
        "current_search": search,
        "has_commitments": "true" if has_commitments else "",
    })


@staff_member_required
def memory_detail(request, memory_id):
    """View a single memory."""
    memory_id_str = str(memory_id)
    
    try:
        # Direct sync call - no asyncio overhead
        memory = get_memory_by_id_sync(memory_id_str)
        
        if not memory:
            messages.error(request, "Memory not found.")
            return redirect("memories:list")
        
        # Log view asynchronously would be better, but keeping simple for now
        ActivityLog.objects.create(
            user=request.user,
            action="view",
            description=f"Viewed memory {memory_id_str}",
            metadata={"memory_id": memory_id_str},
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
    except Exception as e:
        messages.error(request, f"Error loading memory: {e}")
        return redirect("memories:list")
    
    return render(request, "memories/detail.html", {
        "title": f"Memory: {memory.get('summary', memory_id_str)[:50]}...",
        "memory": memory,
    })


@require_POST
@staff_member_required
def memory_delete(request, memory_id):
    """Delete a memory."""
    memory_id_str = str(memory_id)
    try:
        client = get_supabase_client()
        client.table("memories").delete().eq("id", memory_id_str).execute()
        
        # Invalidate stats cache since we deleted data
        invalidate_stats_cache()
        
        ActivityLog.objects.create(
            user=request.user,
            action="delete",
            description=f"Deleted memory {memory_id_str}",
            metadata={"memory_id": memory_id_str},
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        messages.success(request, "Memory deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting memory: {e}")
    
    return redirect("memories:list")


@require_GET
@staff_member_required
def memory_export(request):
    """Export memories as JSON."""
    import json
    
    try:
        client = get_supabase_client()
        response = client.table("memories").select("*").execute()
        memories = response.data or []
        
        ActivityLog.objects.create(
            user=request.user,
            action="export",
            description=f"Exported {len(memories)} memories",
            metadata={"count": len(memories)},
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        response = HttpResponse(
            json.dumps(memories, indent=2, default=str),
            content_type="application/json",
        )
        response["Content-Disposition"] = f'attachment; filename="exo_memories_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
        
    except Exception as e:
        messages.error(request, f"Error exporting memories: {e}")
        return redirect("memories:list")


@require_GET
@staff_member_required
def api_search(request):
    """API endpoint for memory search."""
    query = request.GET.get("q", "")
    source_type = request.GET.get("source_type", "")
    limit = int(request.GET.get("limit", 20))
    
    try:
        # Direct sync call
        memories = search_memories_sync(
            query=query,
            source_type=source_type or None,
            limit=limit,
        )
        return JsonResponse({"memories": memories})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
