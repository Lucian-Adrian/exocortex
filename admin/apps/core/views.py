"""
Core views - Dashboard, analytics, settings.

Optimized: Uses sync functions directly, no asyncio.run overhead.
"""

import os
from datetime import datetime, timedelta

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from admin.apps.core.services import get_supabase_client, get_stats_sync


def dashboard_callback(request, context):
    """Callback for Unfold dashboard - adds stats to context."""
    try:
        stats = get_stats_sync()
        context.update({
            "stats": stats,
            "kpi": [
                {
                    "title": "Total Memories",
                    "metric": stats.get("total_memories", 0),
                    "icon": "psychology",
                    "footer": {
                        "text": f"+{stats.get('memories_today', 0)} today",
                        "link": "/memories/",
                    },
                },
                {
                    "title": "Open Commitments",
                    "metric": stats.get("open_commitments", 0),
                    "icon": "task_alt",
                    "footer": {
                        "text": f"{stats.get('overdue_commitments', 0)} overdue",
                        "link": "/commitments/?status=overdue",
                    },
                },
                {
                    "title": "Queries Today",
                    "metric": stats.get("queries_today", 0),
                    "icon": "search",
                    "footer": {
                        "text": "View analytics",
                        "link": "/analytics/",
                    },
                },
                {
                    "title": "Errors (24h)",
                    "metric": stats.get("errors_24h", 0),
                    "icon": "error",
                    "footer": {
                        "text": "View logs",
                        "link": "/errors/",
                    },
                },
            ],
        })
    except Exception as e:
        context["error"] = str(e)
    
    return context


@login_required
def home(request):
    """Main dashboard view with comprehensive stats."""
    try:
        stats = get_stats_sync()
    except Exception as e:
        stats = {"error": str(e)}
    
    # Static integration info (no DB calls needed)
    integrations = {
        "langchain": {"name": "LangChain", "status": "active", "description": "ExoRetriever available", "icon": "🦜"},
        "n8n": {"name": "n8n Webhooks", "status": "active" if os.getenv("API_BASE_URL") else "configure", "description": f"API at {os.getenv('API_BASE_URL', 'localhost:8000')}", "icon": "🔗"},
        "langfuse": {"name": "Langfuse", "status": "active" if os.getenv("LANGFUSE_PUBLIC_KEY") else "not_configured", "description": "LLM Observability", "icon": "📊"},
        "deepeval": {"name": "DeepEval", "status": "available", "description": "LLM Testing", "icon": "🧪"},
    }
    
    return render(request, "dashboard/home.html", {
        "page_title": "Dashboard",
        "stats": stats,
        "integrations": integrations,
        "api_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
    })


@login_required
def analytics(request):
    """Analytics page with charts."""
    try:
        stats = get_stats_sync()
    except Exception as e:
        stats = {"error": str(e)}
    
    return render(request, "core/analytics.html", {
        "page_title": "Analytics",
        "stats": stats,
    })


@login_required
def settings_view(request):
    """Settings page."""
    from admin.apps.core.models import AdminSettings
    
    settings_list = AdminSettings.objects.all()
    
    return render(request, "core/settings.html", {
        "page_title": "Settings",
        "settings": settings_list,
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_key": os.getenv("SUPABASE_KEY"),
        "gemini_key": os.getenv("GEMINI_API_KEY"),
        "embed_model": os.getenv("EMBED_MODEL"),
        "langfuse_configured": bool(os.getenv("LANGFUSE_PUBLIC_KEY")),
    })


@require_GET
@login_required
def api_stats(request):
    """API endpoint for stats (for AJAX updates)."""
    try:
        stats = get_stats_sync()
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def landing(request):
    """Public landing page - redirects to login or dashboard."""
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("core:home")
    
    return render(request, "core/landing.html", {"title": "Exocortex Admin"})
