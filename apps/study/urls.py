from django.urls import path

from apps.study import views

app_name = "study"

urlpatterns = [
    path("chat/", views.chat_list_view, name="chat_list"),
    path("chat/start/<int:document_id>/", views.chat_start_view, name="chat_start"),
    path("chat/<int:session_id>/", views.chat_view, name="chat"),
    path("chat/<int:session_id>/ask/", views.chat_ask_view, name="chat_ask"),
    path("chat/<int:session_id>/reexplain/", views.chat_reexplain_view, name="chat_reexplain"),
    path("materials/", views.materials_list_view, name="materials"),
    path("materials/<int:pk>/", views.material_detail_view, name="material_detail"),
    path("generate/<int:document_id>/", views.generate_material_view, name="generate"),
]
