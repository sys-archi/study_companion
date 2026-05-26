from django.urls import path

from apps.documents import views

app_name = "documents"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("upload/", views.upload_view, name="upload"),
    path("<int:pk>/", views.detail_view, name="detail"),
    path("<int:pk>/reprocess/", views.reprocess_view, name="reprocess"),
]
