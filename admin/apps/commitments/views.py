"""
Commitments views - Track and manage commitments.

Optimized: Uses sync functions, no asyncio overhead.
"""

from datetime import datetime, date

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from admin.apps.core.services import get_supabase_client, get_commitments_sync, invalidate_stats_cache
from admin.apps.core.models import ActivityLog
from admin.apps.core.utils import get_client_ip


@staff_member_required
def commitment_list(request):
    """List all commitments with filters."""
    status = request.GET.get("status", "")
    from_party = request.GET.get("from_party", "")
    to_party = request.GET.get("to_party", "")
    
    try:
        # Direct sync call
        commitments = get_commitments_sync(status=status or None)
        
        # Filter by parties if specified
        if from_party:
            commitments = [c for c in commitments if from_party.lower() in c.get("from_party", "").lower()]
        if to_party:
            commitments = [c for c in commitments if to_party.lower() in c.get("to_party", "").lower()]
        
        # Mark overdue and calculate stats
        today = date.today()
        stats = {"open": 0, "complete": 0, "overdue": 0, "due_soon": 0}
        
        for c in commitments:
            if c.get("due_date"):
                try:
                    due = datetime.fromisoformat(c["due_date"].replace("Z", "+00:00")).date()
                    c["is_overdue"] = due < today and c.get("status") == "open"
                    days_until = (due - today).days
                    if 0 <= days_until <= 7 and c.get("status") == "open":
                        stats["due_soon"] += 1
                except (ValueError, TypeError):
                    c["is_overdue"] = False
            else:
                c["is_overdue"] = False
            
            if c.get("status") == "open":
                stats["overdue" if c.get("is_overdue") else "open"] += 1
            elif c.get("status") == "complete":
                stats["complete"] += 1
        
    except Exception as e:
        commitments = []
        stats = {"open": 0, "complete": 0, "overdue": 0, "due_soon": 0}
        messages.error(request, f"Error loading commitments: {e}")
    
    return render(request, "commitments/list.html", {
        "title": "Commitments",
        "commitments": commitments,
        "stats": stats,
        "current_status": status,
        "current_from_party": from_party,
        "current_to_party": to_party,
        "statuses": ["open", "complete", "overdue"],
    })


@staff_member_required
def commitment_detail(request, commitment_id):
    """View a single commitment."""
    try:
        client = get_supabase_client()
        response = client.table("commitments").select(
            "*, memories(id, summary, content)"
        ).eq("id", commitment_id).single().execute()
        
        commitment = response.data
        
        if not commitment:
            messages.error(request, "Commitment not found.")
            return redirect("commitments:list")
        
    except Exception as e:
        messages.error(request, f"Error loading commitment: {e}")
        return redirect("commitments:list")
    
    return render(request, "commitments/detail.html", {
        "title": f"Commitment: {commitment.get('description', '')[:50]}...",
        "commitment": commitment,
    })


@staff_member_required
def update_status(request, commitment_id):
    """Update commitment status."""
    new_status = request.POST.get("status", "")
    
    if new_status not in ["open", "complete", "overdue"]:
        messages.error(request, "Invalid status.")
        return redirect("commitments:list")
    
    try:
        client = get_supabase_client()
        client.table("commitments").update({
            "status": new_status
        }).eq("id", commitment_id).execute()
        
        # Invalidate stats cache
        invalidate_stats_cache()
        
        ActivityLog.objects.create(
            user=request.user,
            action="edit",
            description=f"Updated commitment {commitment_id} status to {new_status}",
            metadata={"commitment_id": str(commitment_id), "new_status": new_status},
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        
        messages.success(request, f"Commitment marked as {new_status}.")
    except Exception as e:
        messages.error(request, f"Error updating commitment: {e}")
    
    return redirect("commitments:list")


@staff_member_required
def api_commitments(request):
    """API endpoint for commitments."""
    status = request.GET.get("status", "")
    
    try:
        commitments = get_commitments_sync(status=status or None)
        return JsonResponse({"commitments": commitments})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def calendar_view(request):
    """Calendar view of commitments with due dates."""
    try:
        commitments = get_commitments_sync()
        
        # Group by date
        by_date = {}
        for c in commitments:
            if c.get("due_date"):
                try:
                    due = c["due_date"][:10]  # YYYY-MM-DD
                    if due not in by_date:
                        by_date[due] = []
                    by_date[due].append(c)
                except (ValueError, TypeError):
                    pass
        
    except Exception as e:
        by_date = {}
        messages.error(request, f"Error loading commitments: {e}")
    
    return render(request, "commitments/calendar.html", {
        "title": "Commitment Calendar",
        "commitments_by_date": by_date,
    })
