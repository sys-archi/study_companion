from rest_framework import serializers

from apps.study.models import ChatMessage, ChatSession, GeneratedMaterial


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "is_reexplain", "reexplain_level", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    document_title = serializers.CharField(source="document.title", read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "document", "document_title", "messages", "created_at"]


class GeneratedMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedMaterial
        fields = [
            "id",
            "document",
            "material_type",
            "title",
            "content",
            "structured_data",
            "created_at",
        ]
