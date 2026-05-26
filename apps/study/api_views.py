from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study.models import ChatMessage, ChatSession, GeneratedMaterial
from apps.study.serializers import GeneratedMaterialSerializer
from services.progress_service import log_question
from services.rag_service import answer_question, reexplain_answer


class GeneratedMaterialListAPIView(APIView):
    def get(self, request):
        materials = GeneratedMaterial.objects.filter(user=request.user)
        serializer = GeneratedMaterialSerializer(materials, many=True)
        return Response(serializer.data)


class ChatAskAPIView(APIView):
    def post(self, request, session_id):
        session = ChatSession.objects.filter(pk=session_id, user=request.user).first()
        if not session:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        question = request.data.get("question", "").strip()
        if not question:
            return Response({"error": "Question required"}, status=status.HTTP_400_BAD_REQUEST)

        ChatMessage.objects.create(session=session, role=ChatMessage.ROLE_USER, content=question)
        result = answer_question(session.document_id, question)
        msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.ROLE_ASSISTANT,
            content=result["answer"],
        )
        log_question(request.user, session.document, question)
        return Response({"answer": result["answer"], "message_id": msg.id})


class ChatReexplainAPIView(APIView):
    def post(self, request, session_id):
        session = ChatSession.objects.filter(pk=session_id, user=request.user).first()
        if not session:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        message_id = request.data.get("message_id")
        assistant_msg = ChatMessage.objects.filter(
            pk=message_id, session=session, role=ChatMessage.ROLE_ASSISTANT
        ).first()
        if not assistant_msg:
            return Response({"error": "Message not found"}, status=status.HTTP_404_NOT_FOUND)

        user_msgs = session.messages.filter(role=ChatMessage.ROLE_USER).order_by("-created_at")
        question = user_msgs.first().content if user_msgs.exists() else "Explain again"
        new_level = assistant_msg.reexplain_level + 1

        result = reexplain_answer(
            session.document_id, question, assistant_msg.content, difficulty=new_level
        )
        msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.ROLE_ASSISTANT,
            content=result["answer"],
            is_reexplain=True,
            reexplain_level=new_level,
            parent_message=assistant_msg,
        )
        log_question(request.user, session.document, question, asked_reexplain=True)
        return Response({"answer": result["answer"], "message_id": msg.id})
