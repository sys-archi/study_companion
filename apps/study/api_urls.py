from django.urls import path

from apps.study.api_views import (
    ChatAskAPIView,
    ChatReexplainAPIView,
    GeneratedMaterialListAPIView,
)

urlpatterns = [
    path("materials/", GeneratedMaterialListAPIView.as_view(), name="api-materials"),
    path("chat/<int:session_id>/ask/", ChatAskAPIView.as_view(), name="api-chat-ask"),
    path(
        "chat/<int:session_id>/reexplain/",
        ChatReexplainAPIView.as_view(),
        name="api-chat-reexplain",
    ),
]
