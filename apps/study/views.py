import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.documents.models import Document
from apps.study.models import ChatMessage, ChatSession, GeneratedMaterial
from apps.study.utils import get_question_for_assistant
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


# @login_required
# @require_POST
# def chat_ask_view(request, session_id):
#     session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
#     question = request.POST.get("question", "").strip()
#     if not question:
#         messages.warning(request, "Please enter a question.")
#         return redirect("study:chat", session_id=session.id)
#
#     user_msg = ChatMessage.objects.create(
#         session=session,
#         role=ChatMessage.ROLE_USER,
#         content=question,
#     )
#
#     result = answer_question(session.document_id, question)
#     assistant_msg = ChatMessage.objects.create(
#         session=session,
#         role=ChatMessage.ROLE_ASSISTANT,
#         content=result["answer"],
#     )
#
#     log_question(request.user, session.document, question, asked_reexplain=False)
#
#     if request.headers.get("X-Requested-With") == "XMLHttpRequest":
#         return JsonResponse(
#             {
#                 "user_message": {"id": user_msg.id, "content": user_msg.content},
#                 "assistant_message": {
#                     "id": assistant_msg.id,
#                     "content": assistant_msg.content,
#                 },
#             }
#         )
#
#     return redirect("study:chat", session_id=session.id)
#

@login_required
@require_POST
def chat_ask_view(request, session_id):
    session = get_object_or_404(ChatSession, pk=session_id, user=request.user)

    question = request.POST.get("question", "").strip()

    if not question:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"error": "Please enter a question."},
                status=400,
            )

        messages.warning(request, "Please enter a question.")
        return redirect("study:chat", session_id=session.id)

    try:
        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.ROLE_USER,
            content=question,
        )

        # Generate answer
        result = answer_question(session.document_id, question)

        if not isinstance(result, dict):
            raise Exception("answer_question() did not return a dictionary")

        answer_text = result.get("answer")

        if not answer_text:
            raise Exception("No answer returned from AI service")

        # Save assistant response
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.ROLE_ASSISTANT,
            content=answer_text,
        )

        log_question(
            request.user,
            session.document,
            question,
            asked_reexplain=False,
        )

        # AJAX response
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "user_message": {
                        "id": user_msg.id,
                        "content": user_msg.content,
                    },
                    "assistant_message": {
                        "id": assistant_msg.id,
                        "content": assistant_msg.content,
                    },
                }
            )

        return redirect("study:chat", session_id=session.id)

    except Exception as exc:
        import traceback

        print("\n========== CHAT ERROR ==========")
        traceback.print_exc()
        print("================================\n")

        error_message = str(exc)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "error": error_message,
                },
                status=500,
            )

        messages.error(request, f"Chat failed: {error_message}")
        return redirect("study:chat", session_id=session.id)
#
# @login_required
# @require_POST
# def chat_reexplain_view(request, session_id):
#     session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
#     message_id = request.POST.get("message_id")
#     assistant_msg = get_object_or_404(
#         ChatMessage,
#         pk=message_id,
#         session=session,
#         role=ChatMessage.ROLE_ASSISTANT,
#     )
#
#     question = get_question_for_assistant(assistant_msg)
#
#     prev_level = assistant_msg.reexplain_level
#     new_level = prev_level + 1
#
#     result = reexplain_answer(
#         session.document_id,
#         question,
#         assistant_msg.content,
#         difficulty=new_level,
#     )
#
#     reexplain_msg = ChatMessage.objects.create(
#         session=session,
#         role=ChatMessage.ROLE_ASSISTANT,
#         content=result["answer"],
#         is_reexplain=True,
#         reexplain_level=new_level,
#         parent_message=assistant_msg,
#     )
#
#     log_question(request.user, session.document, question, asked_reexplain=True)
#
#     if request.headers.get("X-Requested-With") == "XMLHttpRequest":
#         return JsonResponse(
#             {
#                 "assistant_message": {
#                     "id": reexplain_msg.id,
#                     "content": reexplain_msg.content,
#                     "is_reexplain": True,
#                     "reexplain_level": new_level,
#                 }
#             }
#         )
#
#     return redirect("study:chat", session_id=session.id)
#
@login_required
@require_POST
def chat_reexplain_view(request, session_id):
    session = get_object_or_404(ChatSession, pk=session_id, user=request.user)

    try:
        message_id = request.POST.get("message_id")

        assistant_msg = get_object_or_404(
            ChatMessage,
            pk=message_id,
            session=session,
            role=ChatMessage.ROLE_ASSISTANT,
        )

        question = get_question_for_assistant(assistant_msg)

        prev_level = assistant_msg.reexplain_level
        new_level = prev_level + 1

        result = reexplain_answer(
            session.document_id,
            question,
            assistant_msg.content,
            difficulty=new_level,
        )

        if not isinstance(result, dict):
            raise Exception("reexplain_answer() did not return a dictionary")

        answer_text = result.get("answer")

        if not answer_text:
            raise Exception("No re-explanation returned")

        reexplain_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.ROLE_ASSISTANT,
            content=answer_text,
            is_reexplain=True,
            reexplain_level=new_level,
            parent_message=assistant_msg,
        )

        log_question(
            request.user,
            session.document,
            question,
            asked_reexplain=True,
        )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "assistant_message": {
                        "id": reexplain_msg.id,
                        "content": reexplain_msg.content,
                        "is_reexplain": True,
                        "reexplain_level": new_level,
                    },
                }
            )

        return redirect("study:chat", session_id=session.id)

    except Exception as exc:
        import traceback

        print("\n======= REEXPLAIN ERROR =======")
        traceback.print_exc()
        print("================================\n")

        error_message = str(exc)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "error": error_message,
                },
                status=500,
            )

        messages.error(request, f"Re-explain failed: {error_message}")
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




