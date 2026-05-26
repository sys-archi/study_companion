from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import dashboard_view, landing_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", landing_view, name="landing"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("accounts/", include("apps.accounts.urls")),
    path("documents/", include("apps.documents.urls")),
    path("study/", include("apps.study.urls")),
    path("progress/", include("apps.progress.urls")),
    path("api/", include("config.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
