# """Retrieval-Augmented Generation orchestration."""
#
# from django.conf import settings
#
# from ai.embeddings import embed_query
# from ai.llm import chat_with_context, reexplain_with_context
# from ai.vector_store import DocumentVectorStore
# from apps.documents.models import Document
#
#
# def retrieve_context(document_id: int, query: str, top_k: int | None = None) -> tuple[str, list[dict]]:
#     """
#     Retrieve relevant chunks and assemble context string.
#     Returns (context_string, chunk_results).
#     """
#     top_k = top_k or settings.TOP_K_CHUNKS
#     query_vector = embed_query(query)
#     results = DocumentVectorStore(document_id).search(query_vector, top_k=top_k)
#
#     if not results:
#         document = Document.objects.filter(pk=document_id).first()
#         if document and document.extracted_text:
#             fallback = document.extracted_text[:2000]
#             return fallback, []
#
#     context_parts = [r["text"] for r in results]
#     context = "\n\n".join(context_parts)
#     return context, results
#
#
# def answer_question(document_id: int, question: str) -> dict:
#     """RAG pipeline: retrieve → generate grounded answer."""
#     context, chunks = retrieve_context(document_id, question)
#     answer = chat_with_context(context, question)
#     return {
#         "answer": answer,
#         "context": context,
#         "chunks": chunks,
#     }
#
#
# def reexplain_answer(
#     document_id: int,
#     question: str,
#     previous_answer: str,
#     difficulty: int = 1,
# ) -> dict:
#     """Simplified re-explanation flow for 'I don't understand'."""
#     context, chunks = retrieve_context(document_id, question, top_k=settings.TOP_K_CHUNKS + 2)
#     answer = reexplain_with_context(context, question, previous_answer, difficulty)
#     return {
#         "answer": answer,
#         "context": context,
#         "chunks": chunks,
#         "difficulty": difficulty,
#     }


"""Retrieval-Augmented Generation orchestration."""

import time
import traceback

from django.conf import settings

from ai.embeddings import embed_query
from ai.llm import chat_with_context, reexplain_with_context
from ai.vector_store import DocumentVectorStore
from apps.documents.models import Document


def log_step(step_name):
    print(f"\n[RAG] {step_name}")


def retrieve_context(document_id: int, query: str, top_k: int | None = None) -> tuple[str, list[dict]]:
    """
    Retrieve relevant chunks and assemble context string.
    Returns (context_string, chunk_results).
    """

    start_total = time.time()

    try:
        top_k = top_k or settings.TOP_K_CHUNKS

        # STEP 1 — Embedding
        log_step("Creating query embedding...")
        start = time.time()

        query_vector = embed_query(query)

        print(f"[RAG] Embedding completed in {time.time() - start:.2f}s")

        # STEP 2 — Vector Search
        log_step("Searching vector database...")
        start = time.time()

        store = DocumentVectorStore(document_id)

        results = store.search(query_vector, top_k=top_k)

        print(f"[RAG] Vector search completed in {time.time() - start:.2f}s")

        # STEP 3 — Fallback
        if not results:
            log_step("No vector results found. Using extracted_text fallback.")

            document = Document.objects.filter(pk=document_id).first()

            if document and document.extracted_text:
                fallback = document.extracted_text[:2000]

                print(f"[RAG] Total retrieval time: {time.time() - start_total:.2f}s")

                return fallback, []

            return "", []

        # STEP 4 — Build Context
        log_step("Building context...")

        context_parts = [r["text"] for r in results]

        context = "\n\n".join(context_parts)

        print(f"[RAG] Total retrieval time: {time.time() - start_total:.2f}s")

        return context, results

    except Exception as exc:
        print("\n========== RETRIEVE_CONTEXT ERROR ==========")
        traceback.print_exc()
        print("===========================================\n")

        raise Exception(f"retrieve_context failed: {str(exc)}")


def answer_question(document_id: int, question: str) -> dict:
    """RAG pipeline: retrieve → generate grounded answer."""

    try:
        total_start = time.time()

        # RETRIEVE
        log_step("Starting retrieval...")
        context, chunks = retrieve_context(document_id, question)

        if not context:
            context = "No study material context available."

        # GENERATE
        log_step("Generating AI answer...")
        start = time.time()

        answer = chat_with_context(context, question)

        print(f"[RAG] LLM generation completed in {time.time() - start:.2f}s")

        print(f"[RAG] TOTAL PIPELINE TIME: {time.time() - total_start:.2f}s")

        return {
            "answer": answer,
            "context": context,
            "chunks": chunks,
        }

    except Exception as exc:
        print("\n========== ANSWER QUESTION ERROR ==========")
        traceback.print_exc()
        print("===========================================\n")

        raise Exception(f"answer_question failed: {str(exc)}")


def reexplain_answer(
    document_id: int,
    question: str,
    previous_answer: str,
    difficulty: int = 1,
) -> dict:
    """Simplified re-explanation flow."""

    try:
        total_start = time.time()

        log_step("Starting re-explanation retrieval...")

        context, chunks = retrieve_context(
            document_id,
            question,
            top_k=settings.TOP_K_CHUNKS + 2,
        )

        if not context:
            context = "No study material context available."

        log_step("Generating simplified explanation...")

        start = time.time()

        answer = reexplain_with_context(
            context,
            question,
            previous_answer,
            difficulty,
        )

        print(f"[RAG] Re-explanation completed in {time.time() - start:.2f}s")

        print(f"[RAG] TOTAL REEXPLAIN TIME: {time.time() - total_start:.2f}s")

        return {
            "answer": answer,
            "context": context,
            "chunks": chunks,
            "difficulty": difficulty,
        }

    except Exception as exc:
        print("\n========== REEXPLAIN ERROR ==========")
        traceback.print_exc()
        print("====================================\n")

        raise Exception(f"reexplain_answer failed: {str(exc)}")