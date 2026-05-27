"""Study chat helpers."""

from apps.study.models import ChatMessage


def get_question_for_assistant(assistant_msg: ChatMessage) -> str:
    """Return the user question that prompted this assistant reply."""
    user_msg = (
        assistant_msg.session.messages.filter(
            role=ChatMessage.ROLE_USER,
            created_at__lte=assistant_msg.created_at,
        )
        .order_by("-created_at")
        .first()
    )
    return user_msg.content if user_msg else "Explain again"
