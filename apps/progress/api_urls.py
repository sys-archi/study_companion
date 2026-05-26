from django.urls import path

from apps.progress.api_views import ProgressSummaryAPIView, QuizSubmitAPIView

urlpatterns = [
    path("summary/", ProgressSummaryAPIView.as_view(), name="api-progress-summary"),
    path("quiz/<int:material_id>/submit/", QuizSubmitAPIView.as_view(), name="api-quiz-submit"),
]
