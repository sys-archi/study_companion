from django.conf import settings
from django.db import models


class QuestionLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_logs",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="question_logs",
    )
    question = models.TextField()
    topic_hint = models.CharField(max_length=200, blank=True)
    asked_reexplain = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    material = models.ForeignKey(
        "study.GeneratedMaterial",
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    answers = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def percentage(self):
        if self.total == 0:
            return 0
        return round((self.score / self.total) * 100)


class WeakTopic(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weak_topics",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="weak_topics",
        null=True,
        blank=True,
    )
    topic = models.CharField(max_length=200)
    reason = models.CharField(max_length=255, blank=True)
    occurrence_count = models.PositiveIntegerField(default=1)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurrence_count", "-last_seen"]
        unique_together = [["user", "topic", "document"]]

    def __str__(self):
        return self.topic
