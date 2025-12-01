"""
Ingest views - Upload content for processing.

Optimized: Cache invalidation on ingest.
"""

import asyncio
import json
import logging

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from admin.apps.core.models import ActivityLog
from admin.apps.core.utils import get_client_ip
from admin.apps.core.services import invalidate_stats_cache

logger = logging.getLogger("exo")


@staff_member_required
def ingest_page(request):
    """Main ingest page."""
    from admin.apps.core.services import get_supabase_client
    
    # Get recent memories for display
    recent_memories = []
    try:
        client = get_supabase_client()
        response = client.table("memories").select("id, summary, source_type, created_at").order("created_at", desc=True).limit(5).execute()
        recent_memories = response.data or []
    except Exception:
        pass
    
    return render(request, "ingest/page.html", {
        "title": "Ingest Content",
        "source_types": ["markdown", "audio", "telegram", "slack", "code"],
        "recent_memories": recent_memories,
    })


@require_POST
@staff_member_required
def ingest_submit(request):
    """Unified submit handler that routes to appropriate ingest method."""
    ingest_type = request.POST.get("ingest_type", "text")
    
    if ingest_type == "file":
        return ingest_file(request)
    elif ingest_type == "json":
        return ingest_json(request)
    else:
        return ingest_text(request)


@require_POST
@staff_member_required
def ingest_json(request):
    """Ingest JSON content."""
    from exo.schemas.content import RawContent, SourceType
    from exo.pipeline import PipelineOrchestrator
    from exo.schemas.errors import ExoError
    
    json_content = request.POST.get("json_content", "").strip()
    
    if not json_content:
        messages.error(request, "Please provide JSON content to ingest.")
        return redirect("ingest:page")
    
    try:
        data = json.loads(json_content)
        text = data.get("content", "")
        source_type = data.get("source_type", "markdown")
        source_file = data.get("source_file", f"json_ingest_{request.user.username}")
        
        if not text:
            messages.error(request, "JSON must contain a 'content' field.")
            return redirect("ingest:page")
        
        try:
            st = SourceType(source_type)
        except ValueError:
            st = SourceType.MARKDOWN
        
        content = RawContent(
            text=text,
            source_type=st,
            source_file=source_file,
        )
        
        orchestrator = PipelineOrchestrator()
        result = asyncio.run(orchestrator.ingest(content))
        
        if isinstance(result, ExoError):
            logger.error(f"Ingest failed: {result.message}")
            messages.error(request, f"Ingest failed: {result.message}")
            return redirect("ingest:page")
        
        ActivityLog.objects.create(
            user=request.user,
            action="ingest",
            description=f"Ingested JSON content ({len(text)} chars)",
            metadata={
                "memory_id": str(result.id),
                "source_type": source_type,
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        invalidate_stats_cache()
        messages.success(request, f"JSON ingested successfully! Memory ID: {result.id}")
        return redirect("memories:detail", memory_id=result.id)
        
    except json.JSONDecodeError as e:
        messages.error(request, f"Invalid JSON: {e}")
        return redirect("ingest:page")
    except Exception as e:
        logger.exception(f"Ingest error: {e}")
        messages.error(request, f"Error during ingest: {e}")
        return redirect("ingest:page")


@require_POST
@staff_member_required
def ingest_text(request):
    """Ingest text content."""
    from exo.schemas.content import RawContent, SourceType
    from exo.pipeline import PipelineOrchestrator
    from exo.schemas.errors import ExoError
    
    text = request.POST.get("content", "").strip() or request.POST.get("text", "").strip()
    source_type = request.POST.get("source_type", "markdown")
    source_file = request.POST.get("source_file", "")
    
    if not text:
        messages.error(request, "Please provide some text to ingest.")
        return redirect("ingest:page")
    
    try:
        # Validate source type
        try:
            st = SourceType(source_type)
        except ValueError:
            st = SourceType.MARKDOWN
        
        # Create raw content
        content = RawContent(
            text=text,
            source_type=st,
            source_file=source_file or f"admin_ingest_{request.user.username}",
        )
        
        # Run the pipeline
        orchestrator = PipelineOrchestrator()
        result = asyncio.run(orchestrator.ingest(content))
        
        if isinstance(result, ExoError):
            logger.error(f"Ingest failed: {result.message}")
            messages.error(request, f"Ingest failed: {result.message}")
            return redirect("ingest:page")
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action="ingest",
            description=f"Ingested text content ({len(text)} chars)",
            metadata={
                "memory_id": str(result.id),
                "source_type": source_type,
                "char_count": len(text),
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        invalidate_stats_cache()
        logger.info(f"User {request.user} ingested content: {result.id}")
        messages.success(request, f"Content ingested successfully! Memory ID: {result.id}")
        
        # Redirect to the new memory
        return redirect("memories:detail", memory_id=result.id)
        
    except Exception as e:
        logger.exception(f"Ingest error: {e}")
        messages.error(request, f"Error during ingest: {e}")
        return redirect("ingest:page")


@require_POST
@staff_member_required
def ingest_file(request):
    """Ingest file content."""
    from exo.schemas.content import RawContent, SourceType
    from exo.pipeline import PipelineOrchestrator
    from exo.schemas.errors import ExoError
    
    uploaded_file = request.FILES.get("file")
    source_type = request.POST.get("source_type", "markdown")
    
    if not uploaded_file:
        messages.error(request, "Please upload a file.")
        return redirect("ingest:page")
    
    try:
        # Read file content
        content_bytes = uploaded_file.read()
        
        # Try to decode as text
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            messages.error(request, "Could not read file as text. Please upload a text file.")
            return redirect("ingest:page")
        
        # Determine source type from file extension if not specified
        filename = uploaded_file.name.lower()
        if filename.endswith(".md"):
            st = SourceType.MARKDOWN
        elif filename.endswith(".json"):
            # Check if it's a telegram export or transcript
            try:
                data = json.loads(text)
                if "messages" in data:
                    st = SourceType.TELEGRAM
                elif "segments" in data or "transcript" in data:
                    st = SourceType.AUDIO
                else:
                    st = SourceType(source_type) if source_type else SourceType.MARKDOWN
            except json.JSONDecodeError:
                st = SourceType(source_type) if source_type else SourceType.MARKDOWN
        else:
            try:
                st = SourceType(source_type)
            except ValueError:
                st = SourceType.MARKDOWN
        
        # Create raw content
        content = RawContent(
            text=text,
            source_type=st,
            source_file=uploaded_file.name,
        )
        
        # Run the pipeline
        orchestrator = PipelineOrchestrator()
        result = asyncio.run(orchestrator.ingest(content))
        
        if isinstance(result, ExoError):
            logger.error(f"Ingest failed: {result.message}")
            messages.error(request, f"Ingest failed: {result.message}")
            return redirect("ingest:page")
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action="ingest",
            description=f"Ingested file: {uploaded_file.name}",
            metadata={
                "memory_id": str(result.id),
                "source_type": str(st.value),
                "filename": uploaded_file.name,
                "file_size": len(content_bytes),
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        invalidate_stats_cache()
        logger.info(f"User {request.user} ingested file: {uploaded_file.name}")
        messages.success(request, f"File ingested successfully! Memory ID: {result.id}")
        
        return redirect("memories:detail", memory_id=result.id)
        
    except Exception as e:
        logger.exception(f"Ingest error: {e}")
        messages.error(request, f"Error during ingest: {e}")
        return redirect("ingest:page")


@require_POST
@staff_member_required
def api_ingest(request):
    """API endpoint for ingest (for AJAX)."""
    from exo.schemas.content import RawContent, SourceType
    from exo.pipeline import PipelineOrchestrator
    from exo.schemas.errors import ExoError
    
    try:
        data = json.loads(request.body)
        text = data.get("text", "").strip()
        source_type = data.get("source_type", "markdown")
        
        if not text:
            return JsonResponse({"error": "No text provided"}, status=400)
        
        try:
            st = SourceType(source_type)
        except ValueError:
            st = SourceType.MARKDOWN
        
        content = RawContent(
            text=text,
            source_type=st,
            source_file=f"api_ingest_{request.user.username}",
        )
        
        orchestrator = PipelineOrchestrator()
        result = asyncio.run(orchestrator.ingest(content))
        
        if isinstance(result, ExoError):
            return JsonResponse({
                "success": False,
                "error": result.message,
            }, status=400)
        
        # Log the activity
        ActivityLog.objects.create(
            user=request.user,
            action="ingest",
            description=f"API ingest ({len(text)} chars)",
            metadata={
                "memory_id": str(result.id),
                "source_type": source_type,
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        return JsonResponse({
            "success": True,
            "memory_id": str(result.id),
            "summary": result.summary,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.exception(f"API ingest error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
