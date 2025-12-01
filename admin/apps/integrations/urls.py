from django.urls import path
from . import views

app_name = "integrations"

urlpatterns = [
    path("langchain/", views.langchain_view, name="langchain"),
    path("n8n/", views.n8n_view, name="n8n"),
    path("langfuse/", views.langfuse_view, name="langfuse"),
    path("deepeval/", views.deepeval_view, name="deepeval"),
]
