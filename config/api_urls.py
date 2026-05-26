from django.urls import include, path

urlpatterns = [
    path("documents/", include("apps.documents.api_urls")),
    path("study/", include("apps.study.api_urls")),
    path("progress/", include("apps.progress.api_urls")),
]
