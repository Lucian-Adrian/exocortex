"""
Logs views - View system logs and errors.

Optimized: Uses sync functions, no asyncio overhead.
"""

from datetime import datetime, timedelta, timezone

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from admin.apps.logs.models import SystemLog
from admin.apps.core.services import get_errors_sync


@staff_member_required
def logs_list(request):
    """View system logs."""
    level = request.GET.get("level", "")
    logger = request.GET.get("logger", "")
    
    logs = SystemLog.objects.all()
    
    if level:
        logs = logs.filter(level=level)
    if logger:
        logs = logs.filter(logger_name__icontains=logger)
    
    logs = logs[:500]
    
    # Get unique loggers for filter
    loggers = SystemLog.objects.values_list("logger_name", flat=True).distinct()[:50]
    
    return render(request, "logs/list.html", {
        "title": "System Logs",
        "logs": logs,
        "loggers": sorted(set(loggers)),
        "levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "current_level": level,
        "current_logger": logger,
    })


@staff_member_required
def errors_list(request):
    """View Supabase errors from _errors table."""
    try:
        # Direct sync call
        errors = get_errors_sync(limit=200)
    except Exception as e:
        errors = []
        messages.error(request, f"Error loading errors: {e}")
    
    return render(request, "logs/errors.html", {
        "title": "Pipeline Errors",
        "errors": errors,
    })


@require_GET
@staff_member_required
def api_logs(request):
    """API endpoint for logs."""
    level = request.GET.get("level", "")
    limit = int(request.GET.get("limit", 100))
    
    logs = SystemLog.objects.all()
    
    if level:
        logs = logs.filter(level=level)
    
    logs = logs[:limit]
    
    return JsonResponse({
        "logs": [
            {
                "id": log.id,
                "level": log.level,
                "logger_name": log.logger_name,
                "message": log.message,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    })


@staff_member_required
def log_detail(request, log_id):
    """View a single log entry."""
    try:
        log = SystemLog.objects.get(id=log_id)
    except SystemLog.DoesNotExist:
        messages.error(request, "Log not found.")
        return render(request, "logs/list.html", {"title": "System Logs"})
    
    return render(request, "logs/detail.html", {
        "title": f"Log: {log.id}",
        "log": log,
    })
