import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.study.models import GeneratedMaterial
from services.progress_service import get_progress_summary, log_quiz_attempt


@login_required
def analytics_view(request):
    progress = get_progress_summary(request.user)
    return render(request, "progress/analytics.html", {"progress": progress})


@login_required
@require_POST
def submit_quiz_view(request, material_id):
    material = get_object_or_404(
        GeneratedMaterial,
        pk=material_id,
        user=request.user,
        material_type=GeneratedMaterial.TYPE_QUIZ,
    )

    try:
        payload = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        payload = request.POST.dict()

    answers = payload.get("answers", {})
    quiz_data = material.structured_data or {}
    questions = quiz_data.get("questions", [])

    score = 0
    for i, q in enumerate(questions):
        selected = answers.get(str(i))
        if selected is not None and int(selected) == q.get("correct_index"):
            score += 1

    total = len(questions) or 1
    attempt = log_quiz_attempt(request.user, material, score, total, answers)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "score": score,
                "total": total,
                "percentage": attempt.percentage,
            }
        )

    return redirect("study:material_detail", pk=material.pk)
