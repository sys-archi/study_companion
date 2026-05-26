from django.contrib import admin

from apps.documents.models import Document, DocumentChunk


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    readonly_fields = ("chunk_index", "text")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "doc_type", "status", "chunk_count", "created_at")
    list_filter = ("status", "doc_type")
    search_fields = ("title", "user__username")
    inlines = [DocumentChunkInline]
