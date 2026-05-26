from django.contrib import admin

from apps.progress.models import QuestionLog, QuizAttempt, WeakTopic


@admin.register(QuestionLog)
class QuestionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "topic_hint", "asked_reexplain", "created_at")
    list_filter = ("asked_reexplain",)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "material", "score", "total", "created_at")


@admin.register(WeakTopic)
class WeakTopicAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "occurrence_count", "last_seen")
