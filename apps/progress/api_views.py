from rest_framework.response import Response
from rest_framework.views import APIView

from apps.progress.serializers import ProgressSummarySerializer
from apps.study.models import GeneratedMaterial
from services.progress_service import get_progress_summary, log_quiz_attempt


class ProgressSummaryAPIView(APIView):
    def get(self, request):
        data = get_progress_summary(request.user)
        weak_serialized = [
            {
                "topic": w.topic,
                "reason": w.reason,
                "occurrence_count": w.occurrence_count,
                "document_title": w.document.title if w.document else "",
                "last_seen": w.last_seen,
            }
            for w in data["weak_topics"]
        ]
        attempts_serialized = [
            {
                "material_title": a.material.title,
                "score": a.score,
                "total": a.total,
                "percentage": a.percentage,
                "created_at": a.created_at,
            }
            for a in data["recent_attempts"]
        ]
        payload = {
            "total_questions": data["total_questions"],
            "reexplain_count": data["reexplain_count"],
            "quiz_attempts": data["quiz_attempts"],
            "average_quiz_score": data["average_quiz_score"],
            "weak_topics": weak_serialized,
            "recent_attempts": attempts_serialized,
        }
        serializer = ProgressSummarySerializer(payload)
        return Response(serializer.data)


class QuizSubmitAPIView(APIView):
    def post(self, request, material_id):
        material = GeneratedMaterial.objects.filter(
            pk=material_id,
            user=request.user,
            material_type=GeneratedMaterial.TYPE_QUIZ,
        ).first()
        if not material:
            return Response({"error": "Quiz not found"}, status=404)

        answers = request.data.get("answers", {})
        questions = (material.structured_data or {}).get("questions", [])
        score = sum(
            1
            for i, q in enumerate(questions)
            if answers.get(str(i)) is not None
            and int(answers.get(str(i))) == q.get("correct_index")
        )
        total = len(questions) or 1
        attempt = log_quiz_attempt(request.user, material, score, total, answers)
        return Response({"score": score, "total": total, "percentage": attempt.percentage})
