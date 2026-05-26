"""Document ingestion: parse, chunk, embed, index."""

import logging

import fitz
from django.conf import settings
from django.db import transaction

from ai.chunking import chunk_text
from ai.embeddings import embed_texts
from ai.vector_store import DocumentVectorStore
from apps.documents.models import Document, DocumentChunk

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract plain text from a PDF using PyMuPDF."""
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()


def extract_text_from_file(document: Document) -> str:
    """Extract text based on document type."""
    if document.doc_type == Document.TYPE_TEXT:
        if document.text_content:
            return document.text_content.strip()
        if document.file:
            return document.file.read().decode("utf-8", errors="replace").strip()
        return ""

    if document.file:
        return extract_text_from_pdf(document.file.path)
    return ""


@transaction.atomic
def process_document(document_id: int) -> Document:
    """
    Full ingestion pipeline: extract → chunk → embed → FAISS index.
    """
    document = Document.objects.select_for_update().get(pk=document_id)
    document.status = Document.STATUS_PROCESSING
    document.save(update_fields=["status"])

    try:
        raw_text = extract_text_from_file(document)
        if not raw_text:
            document.status = Document.STATUS_FAILED
            document.error_message = "No text could be extracted from this file."
            document.save(update_fields=["status", "error_message"])
            return document

        document.extracted_text = raw_text
        chunks = chunk_text(
            raw_text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )

        DocumentChunk.objects.filter(document=document).delete()
        DocumentVectorStore(document.id).delete()

        chunk_objects = []
        for idx, chunk in enumerate(chunks):
            chunk_objects.append(
                DocumentChunk(
                    document=document,
                    chunk_index=idx,
                    text=chunk,
                )
            )
        DocumentChunk.objects.bulk_create(chunk_objects)
        saved_chunks = list(
            DocumentChunk.objects.filter(document=document).order_by("chunk_index")
        )

        chunk_texts = [c.text for c in saved_chunks]
        vectors = embed_texts(chunk_texts)

        meta_records = [
            {
                "chunk_id": c.id,
                "chunk_index": c.chunk_index,
                "text": c.text,
            }
            for c in saved_chunks
        ]
        DocumentVectorStore(document.id).build(meta_records, vectors)

        document.chunk_count = len(saved_chunks)
        document.status = Document.STATUS_READY
        document.error_message = ""
        document.save(
            update_fields=["extracted_text", "chunk_count", "status", "error_message"]
        )
        logger.info("Document %s processed: %s chunks", document.id, len(saved_chunks))

    except Exception as exc:
        logger.exception("Document processing failed: %s", exc)
        document.status = Document.STATUS_FAILED
        document.error_message = str(exc)[:500]
        document.save(update_fields=["status", "error_message"])

    return document
