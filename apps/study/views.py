import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.documents.models import Document
from apps.study.models import ChatMessage, ChatSession, GeneratedMaterial
from services.generation_service import generate_notes, generate_quiz, generate_summary
from services.progress_service import log_question
from services.rag_service import answer_question, reexplain_answer


@login_required
def chat_list_view(request):
    sessions = ChatSession.objects.filter(user=request.user).select_related("document")
    documents = Document.objects.filter(user=request.user, status=Document.STATUS_READY)
    return render(
        request,
        "study/chat_list.html",
        {"sessions": sessions, "documents": documents},
    )


@login_required
def chat_start_view(request, document_id):
    document = get_object_or_404(
        Document, pk=document_id, user=request.user, status=Document.STATUS_READY
    )
    session = ChatSession.objects.create(
        user=request.user,
        document=document,
        title=f"Study: {document.title}",
    )
    return redirect("study:chat", session_id=session.id)


@login_required
def chat_view(request, session_id):
    session = get_object_or_404(
        ChatSession.objects.select_related("document"),
        pk=session_id,
        user=request.user,
    )
    chat_messages = session.messages.all()
    return render(
        request,
        "study/chat.html",
        {"session": session, "chat_messages": chat_messages},
    )


@login_required
@require_POST
def chat_ask_view(request, session_id):
    session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
    question = request.POST.get("question", "").strip()
    if not question:
        messages.warning(request, "Please enter a question.")
        return redirect("study:chat", session_id=session.id)

    user_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.ROLE_USER,
        content=question,
    )

    result = answer_question(session.document_id, question)
    assistant_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.ROLE_ASSISTANT,
        content=result["answer"],
    )

    log_question(request.user, session.document, question, asked_reexplain=False)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "user_message": {"id": user_msg.id, "content": user_msg.content},
                "assistant_message": {
                    "id": assistant_msg.id,
                    "content": assistant_msg.content,
                },
            }
        )

    return redirect("study:chat", session_id=session.id)


@login_required
@require_POST
def chat_reexplain_view(request, session_id):
    session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
    message_id = request.POST.get("message_id")
    assistant_msg = get_object_or_404(
        ChatMessage,
        pk=message_id,
        session=session,
        role=ChatMessage.ROLE_ASSISTANT,
    )

    user_msgs = session.messages.filter(role=ChatMessage.ROLE_USER).order_by("-created_at")
    question = user_msgs.first().content if user_msgs.exists() else "Explain again"

    prev_level = assistant_msg.reexplain_level
    new_level = prev_level + 1

    result = reexplain_answer(
        session.document_id,
        question,
        assistant_msg.content,
        difficulty=new_level,
    )

    reexplain_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.ROLE_ASSISTANT,
        content=result["answer"],
        is_reexplain=True,
        reexplain_level=new_level,
        parent_message=assistant_msg,
    )

    log_question(request.user, session.document, question, asked_reexplain=True)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "assistant_message": {
                    "id": reexplain_msg.id,
                    "content": reexplain_msg.content,
                    "is_reexplain": True,
                }
            }
        )

    return redirect("study:chat", session_id=session.id)


@login_required
def materials_list_view(request):
    materials = GeneratedMaterial.objects.filter(user=request.user).select_related(
        "document"
    )
    documents = Document.objects.filter(user=request.user, status=Document.STATUS_READY)
    return render(
        request,
        "study/materials_list.html",
        {"materials": materials, "documents": documents},
    )


@login_required
def material_detail_view(request, pk):
    material = get_object_or_404(GeneratedMaterial, pk=pk, user=request.user)
    quiz_data = material.structured_data if material.material_type == GeneratedMaterial.TYPE_QUIZ else None
    return render(
        request,
        "study/material_detail.html",
        {"material": material, "quiz_data": quiz_data},
    )


@login_required
@require_POST
def generate_material_view(request, document_id):
    document = get_object_or_404(
        Document, pk=document_id, user=request.user, status=Document.STATUS_READY
    )
    gen_type = request.POST.get("type", "notes")

    try:
        if gen_type == "notes":
            material = generate_notes(document, request.user)
        elif gen_type == "summary":
            material = generate_summary(document, request.user)
        elif gen_type == "quiz":
            material = generate_quiz(document, request.user)
        else:
            messages.error(request, "Unknown generation type.")
            return redirect("study:materials")
        messages.success(request, f'Generated "{material.title}" successfully!')
        return redirect("study:material_detail", pk=material.pk)
    except Exception as exc:
        messages.error(request, f"Generation failed: {exc}")
        return redirect("study:materials")
