from django.contrib import admin
from unfold.admin import ModelAdmin

from admin.apps.query.models import QueryHistory


@admin.register(QueryHistory)
class QueryHistoryAdmin(ModelAdmin):
    list_display = ["question_preview", "confidence", "execution_time_ms", "user", "created_at"]
    list_filter = ["user", "created_at"]
    search_fields = ["question", "answer"]
    readonly_fields = ["user", "question", "answer", "confidence", "sources", "commitments", "parameters", "execution_time_ms", "created_at"]
    date_hierarchy = "created_at"
    
    def question_preview(self, obj):
        return obj.question[:80] + "..." if len(obj.question) > 80 else obj.question
    question_preview.short_description = "Question"
