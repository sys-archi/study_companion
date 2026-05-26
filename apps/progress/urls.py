from django.urls import path

from apps.progress import views

app_name = "progress"

urlpatterns = [
    path("", views.analytics_view, name="analytics"),
    path("quiz/<int:material_id>/submit/", views.submit_quiz_view, name="submit_quiz"),
]
