"""Retrieval-Augmented Generation orchestration."""

from django.conf import settings

from ai.embeddings import embed_query
from ai.llm import chat_with_context, reexplain_with_context
from ai.vector_store import DocumentVectorStore
from apps.documents.models import Document


def retrieve_context(document_id: int, query: str, top_k: int | None = None) -> tuple[str, list[dict]]:
    """
    Retrieve relevant chunks and assemble context string.
    Returns (context_string, chunk_results).
    """
    top_k = top_k or settings.TOP_K_CHUNKS
    query_vector = embed_query(query)
    results = DocumentVectorStore(document_id).search(query_vector, top_k=top_k)

    if not results:
        document = Document.objects.filter(pk=document_id).first()
        if document and document.extracted_text:
            fallback = document.extracted_text[:2000]
            return fallback, []

    context_parts = [r["text"] for r in results]
    context = "\n\n".join(context_parts)
    return context, results


def answer_question(document_id: int, question: str) -> dict:
    """RAG pipeline: retrieve → generate grounded answer."""
    context, chunks = retrieve_context(document_id, question)
    answer = chat_with_context(context, question)
    return {
        "answer": answer,
        "context": context,
        "chunks": chunks,
    }


def reexplain_answer(
    document_id: int,
    question: str,
    previous_answer: str,
    difficulty: int = 1,
) -> dict:
    """Simplified re-explanation flow for 'I don't understand'."""
    context, chunks = retrieve_context(document_id, question, top_k=settings.TOP_K_CHUNKS + 2)
    answer = reexplain_with_context(context, question, previous_answer, difficulty)
    return {
        "answer": answer,
        "context": context,
        "chunks": chunks,
        "difficulty": difficulty,
    }
