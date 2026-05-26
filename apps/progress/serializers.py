from rest_framework import serializers

from apps.progress.models import QuestionLog, QuizAttempt, WeakTopic


class WeakTopicSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True, default="")

    class Meta:
        model = WeakTopic
        fields = ["topic", "reason", "occurrence_count", "document_title", "last_seen"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    percentage = serializers.IntegerField(read_only=True)
    material_title = serializers.CharField(source="material.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ["material_title", "score", "total", "percentage", "created_at"]


class ProgressSummarySerializer(serializers.Serializer):
    total_questions = serializers.IntegerField()
    reexplain_count = serializers.IntegerField()
    quiz_attempts = serializers.IntegerField()
    average_quiz_score = serializers.IntegerField()
    weak_topics = WeakTopicSerializer(many=True)
    recent_attempts = QuizAttemptSerializer(many=True)
