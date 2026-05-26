from django.contrib import admin

from apps.study.models import ChatMessage, ChatSession, GeneratedMaterial


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "document", "created_at")
    inlines = [ChatMessageInline]


@admin.register(GeneratedMaterial)
class GeneratedMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "material_type", "document", "created_at")
    list_filter = ("material_type",)
