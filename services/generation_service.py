"""Auto-generation of notes, summaries, and quizzes."""

import json
import logging
import re

from django.conf import settings

from ai.llm import generate_study_material
from ai.prompts import (
    GENERATE_NOTES_TEMPLATE,
    GENERATE_QUIZ_TEMPLATE,
    GENERATE_SUMMARY_TEMPLATE,
)
from apps.documents.models import Document
from apps.study.models import GeneratedMaterial

logger = logging.getLogger(__name__)


def _get_document_context(document: Document, max_chars: int = 6000) -> str:
    if document.extracted_text:
        return document.extracted_text[:max_chars]
    from apps.documents.models import DocumentChunk

    chunks = DocumentChunk.objects.filter(document=document).order_by("chunk_index")[:12]
    return "\n\n".join(c.text for c in chunks)


def generate_notes(document: Document, user) -> GeneratedMaterial:
    context = _get_document_context(document)
    content = generate_study_material(GENERATE_NOTES_TEMPLATE, context)
    return GeneratedMaterial.objects.create(
        user=user,
        document=document,
        material_type=GeneratedMaterial.TYPE_NOTES,
        title=f"Revision Notes — {document.title}",
        content=content,
    )


def generate_summary(document: Document, user) -> GeneratedMaterial:
    context = _get_document_context(document)
    content = generate_study_material(GENERATE_SUMMARY_TEMPLATE, context)
    return GeneratedMaterial.objects.create(
        user=user,
        document=document,
        material_type=GeneratedMaterial.TYPE_SUMMARY,
        title=f"Summary — {document.title}",
        content=content,
    )


def generate_quiz(document: Document, user) -> GeneratedMaterial:
    context = _get_document_context(document)
    raw = generate_study_material(GENERATE_QUIZ_TEMPLATE, context)

    quiz_data = _parse_quiz_json(raw)
    return GeneratedMaterial.objects.create(
        user=user,
        document=document,
        material_type=GeneratedMaterial.TYPE_QUIZ,
        title=quiz_data.get("title", f"Quiz — {document.title}"),
        content=raw,
        structured_data=quiz_data,
    )


def _parse_quiz_json(raw: str) -> dict:
    """Extract and validate quiz JSON from LLM output."""
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            if "questions" in data:
                return data
    except json.JSONDecodeError:
        logger.warning("Failed to parse quiz JSON from LLM output")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"title": "Study Quiz", "questions": []}
