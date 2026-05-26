from django.urls import path

from apps.documents.api_views import DocumentListAPIView

urlpatterns = [
    path("", DocumentListAPIView.as_view(), name="api-document-list"),
]
