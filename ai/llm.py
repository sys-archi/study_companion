"""OpenAI-compatible LLM client with grounded fallback when no API key is set."""

import json
import logging
import re

from django.conf import settings

from ai.prompts import SYSTEM_TUTOR

logger = logging.getLogger(__name__)


def _has_api_key() -> bool:
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())


def _call_openai(messages: list[dict], temperature: float = 0.3) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def generate(messages: list[dict], temperature: float = 0.3) -> str:
    """Generate text via LLM API or grounded fallback."""
    if _has_api_key():
        try:
            return _call_openai(messages, temperature=temperature)
        except Exception as exc:
            logger.warning("LLM API call failed, using fallback: %s", exc)

    user_content = ""
    for msg in messages:
        if msg["role"] == "user":
            user_content = msg["content"]
            break
    return _grounded_fallback(user_content)


def _grounded_fallback(user_prompt: str) -> str:
    """
    Build a response from retrieved context embedded in the prompt.
    Ensures the app remains functional without an API key.
    """
    context_match = re.search(
        r"(?:Study material context:|Material:)\s*\n---\s*\n(.*?)\n---",
        user_prompt,
        re.DOTALL,
    )
    context = context_match.group(1).strip() if context_match else ""

    question_match = re.search(
        r"(?:Student question:|Original question:)\s*(.+?)(?:\n\n|$)",
        user_prompt,
        re.DOTALL,
    )
    question = question_match.group(1).strip() if question_match else "your question"

    if "Re-explain" in user_prompt or "SIMPLER" in user_prompt:
        return _fallback_reexplain(context, question)
    if "revision notes" in user_prompt.lower():
        return _fallback_notes(context)
    if "quiz" in user_prompt.lower() and "JSON" in user_prompt:
        return json.dumps(_fallback_quiz(context))
    if "Summarize" in user_prompt:
        return _fallback_summary(context)

    return _fallback_answer(context, question)


def _fallback_answer(context: str, question: str) -> str:
    if not context:
        return (
            "I don't have enough material from your uploads to answer that. "
            "Try uploading a textbook or notes on this topic first."
        )
    snippets = [s.strip() for s in context.split("\n\n") if s.strip()][:3]
    body = "\n\n".join(f"• {s[:400]}{'...' if len(s) > 400 else ''}" for s in snippets)
    return (
        f"**Answer (from your study material)**\n\n"
        f"Based on what you uploaded, here's what relates to *{question}*:\n\n"
        f"{body}\n\n"
        f"*Tip:* Click **I still don't understand** if you'd like a simpler explanation "
        f"with examples and step-by-step breakdown."
    )


def _fallback_reexplain(context: str, question: str) -> str:
    steps = [
        "Let's break this down into smaller pieces.",
        "Think of it like building blocks — each part connects to the next.",
        "Focus on one idea at a time before moving on.",
    ]
    analogy = (
        "Imagine explaining this to a friend who's never seen the topic before — "
        "use everyday examples they already know."
    )
    watch_out = "- New vocabulary\n- Skipping steps\n- Mixing up similar concepts"
    return (
        f"**Simpler explanation**\n\n"
        f"**Your question:** {question}\n\n"
        f"**Step by step:**\n"
        + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
        + f"\n\n**Analogy:** {analogy}\n\n"
        f"**From your material:**\n{context[:600]}{'...' if len(context) > 600 else ''}\n\n"
        f"**Watch out for:**\n{watch_out}\n\n"
        f"**Check yourself:** Can you explain the main idea in one sentence?"
    )


def _fallback_notes(context: str) -> str:
    lines = [ln.strip() for ln in context.split("\n") if ln.strip()][:12]
    bullets = "\n".join(f"- {ln[:200]}" for ln in lines[:8])
    return f"**Revision Notes**\n\n{bullets}\n\n**Remember:**\n- Review in short sessions\n- Test yourself with the quiz feature"


def _fallback_summary(context: str) -> str:
    sentences = re.split(r"[.!?]+\s+", context)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
    return "\n".join(f"- {s}" for s in sentences) or "- Upload more content for a richer summary."


def _fallback_quiz(context: str) -> dict:
    sentences = [s.strip() for s in re.split(r"[.!?]+\s+", context) if len(s.strip()) > 30]
    questions = []
    for i, sent in enumerate(sentences[:5]):
        words = sent.split()
        if len(words) < 5:
            continue
        key_word = words[len(words) // 2] if len(words) > 3 else words[0]
        questions.append(
            {
                "question": f"According to your material, which statement best relates to: '{sent[:80]}...'?",
                "options": [
                    f"It involves '{key_word}' and related concepts",
                    "This topic is not covered in the material",
                    "The opposite is stated in the material",
                    "None of the above",
                ],
                "correct_index": 0,
                "explanation": "This answer is grounded in your uploaded study material.",
            }
        )
    if not questions:
        questions = [
            {
                "question": "Have you uploaded study material for this document?",
                "options": ["Yes", "No", "Partially", "Not sure"],
                "correct_index": 0,
                "explanation": "Upload PDFs or notes to generate better quizzes.",
            }
        ]
    return {"title": "Study Quiz", "questions": questions[:5]}


def chat_with_context(context: str, question: str, system: str = SYSTEM_TUTOR) -> str:
    from ai.prompts import CHAT_USER_TEMPLATE

    user_msg = CHAT_USER_TEMPLATE.format(context=context, question=question)
    return generate(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]
    )


def reexplain_with_context(
    context: str, question: str, previous_answer: str, difficulty: int = 1
) -> str:
    from ai.prompts import REEXPLAIN_USER_TEMPLATE

    user_msg = REEXPLAIN_USER_TEMPLATE.format(
        context=context,
        question=question,
        previous_answer=previous_answer,
        difficulty=difficulty,
    )
    return generate(
        [
            {"role": "system", "content": SYSTEM_TUTOR},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.5,
    )


def generate_study_material(prompt_template: str, context: str, **kwargs) -> str:
    user_msg = prompt_template.format(context=context, **kwargs)
    return generate(
        [
            {"role": "system", "content": SYSTEM_TUTOR},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
    )
