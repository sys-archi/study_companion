"""Progress tracking and weak-topic identification."""

from apps.progress.models import QuestionLog, QuizAttempt, WeakTopic


def log_question(user, document, question: str, asked_reexplain: bool = False):
    topic_hint = question[:120].strip()
    QuestionLog.objects.create(
        user=user,
        document=document,
        question=question,
        topic_hint=topic_hint,
        asked_reexplain=asked_reexplain,
    )
    if asked_reexplain:
        _record_weak_topic(user, document, topic_hint, "Asked for simpler explanation")


def log_quiz_attempt(user, material, score: int, total: int, answers: dict):
    attempt = QuizAttempt.objects.create(
        user=user,
        material=material,
        score=score,
        total=total,
        answers=answers,
    )
    if total > 0 and (score / total) < 0.6:
        doc = material.document
        _record_weak_topic(
            user,
            doc,
            material.title,
            f"Low quiz score ({score}/{total})",
        )
    return attempt


def _record_weak_topic(user, document, topic: str, reason: str):
    obj, created = WeakTopic.objects.get_or_create(
        user=user,
        document=document,
        topic=topic[:200],
        defaults={"reason": reason},
    )
    if not created:
        obj.occurrence_count += 1
        obj.reason = reason
        obj.save(update_fields=["occurrence_count", "reason", "last_seen"])


def get_progress_summary(user) -> dict:
    questions = QuestionLog.objects.filter(user=user)
    attempts = QuizAttempt.objects.filter(user=user)
    weak = WeakTopic.objects.filter(user=user)[:10]

    total_questions = questions.count()
    reexplain_count = questions.filter(asked_reexplain=True).count()
    avg_quiz = 0
    if attempts.exists():
        scores = [a.percentage for a in attempts]
        avg_quiz = round(sum(scores) / len(scores))

    return {
        "total_questions": total_questions,
        "reexplain_count": reexplain_count,
        "quiz_attempts": attempts.count(),
        "average_quiz_score": avg_quiz,
        "weak_topics": list(weak),
        "recent_questions": list(questions[:5]),
        "recent_attempts": list(attempts[:5]),
    }
