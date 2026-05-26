from django.conf import settings
from django.db import models


class Document(models.Model):
    TYPE_PDF = "pdf"
    TYPE_TEXT = "text"
    TYPE_CHOICES = [
        (TYPE_PDF, "PDF"),
        (TYPE_TEXT, "Text Notes"),
    ]

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_READY = "ready"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_READY, "Ready"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_PDF)
    file = models.FileField(upload_to="documents/%Y/%m/", blank=True, null=True)
    text_content = models.TextField(blank=True, help_text="For pasted text notes")
    extracted_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    chunk_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    subject = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_ready(self):
        return self.status == self.STATUS_READY


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]
        unique_together = [["document", "chunk_index"]]

    def __str__(self):
        return f"{self.document.title} — chunk {self.chunk_index}"
