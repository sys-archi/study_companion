from rest_framework import serializers

from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    is_ready = serializers.BooleanField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "subject",
            "doc_type",
            "status",
            "chunk_count",
            "is_ready",
            "created_at",
        ]
        read_only_fields = fields
