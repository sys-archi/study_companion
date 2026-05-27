"""OpenAI-compatible LLM client with grounded fallback systems."""

import json
import logging
import random
import re

from django.conf import settings

from ai.prompts import SYSTEM_TUTOR

logger = logging.getLogger(__name__)


# =========================================================
# API AVAILABILITY
# =========================================================

def _has_api_key() -> bool:
    return bool(
        settings.OPENAI_API_KEY
        and settings.OPENAI_API_KEY.strip()
    )


# =========================================================
# OPENAI / GROQ CALL
# =========================================================

def _call_openai(messages: list[dict], temperature: float = 0.3) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        timeout=60,
    )

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
    )

    return response.choices[0].message.content or ""


# =========================================================
# MAIN GENERATION ENTRY
# =========================================================

def generate(messages: list[dict], temperature: float = 0.3) -> str:
    """
    Generate text using API if available.
    Otherwise use grounded fallback logic.
    """

    if _has_api_key():
        try:
            return _call_openai(messages, temperature=temperature)

        except Exception as exc:
            logger.warning(
                "LLM API call failed. Using fallback. Error: %s",
                exc,
            )

    user_content = ""

    for msg in messages:
        if msg["role"] == "user":
            user_content = msg["content"]
            break

    return _grounded_fallback(user_content)


# =========================================================
# FALLBACK ROUTER
# =========================================================

def _grounded_fallback(user_prompt: str) -> str:

    context_match = re.search(
        r"(?:Study material context:|Material:)\s*\n---\s*\n(.*?)\n---",
        user_prompt,
        re.DOTALL,
    )

    context = (
        context_match.group(1).strip()
        if context_match
        else ""
    )

    question_match = re.search(
        r"(?:Student question:|Original question:)\s*(.+?)(?:\n\n|$)",
        user_prompt,
        re.DOTALL,
    )

    question = (
        question_match.group(1).strip()
        if question_match
        else "your question"
    )

    lowered = user_prompt.lower()

    if "re-explain" in lowered or "simpler" in lowered:
        return _fallback_reexplain(context, question)

    if "revision notes" in lowered:
        return _fallback_notes(context)

    if "quiz" in lowered and "json" in lowered:
        return json.dumps(_fallback_quiz(context))

    if "summarize" in lowered or "summary" in lowered:
        return _fallback_summary(context)

    return _fallback_answer(context, question)


# =========================================================
# CLEAN TEXT HELPERS
# =========================================================

def _clean_context(context: str) -> str:

    lines = []

    for line in context.splitlines():

        stripped = line.strip()

        if not stripped:
            continue

        lower = stripped.lower()

        noisy_patterns = [
            "created by",
            "copyright",
            "ministry",
            "science branch",
            "isurupaya",
            "page ",
        ]

        if any(p in lower for p in noisy_patterns):
            continue

        if len(stripped) < 4:
            continue

        lines.append(stripped)

    return "\n".join(lines)


# =========================================================
# FALLBACK ANSWER
# =========================================================

def _fallback_answer(context: str, question: str) -> str:

    context = _clean_context(context)

    if not context:
        return (
            "I could not find enough relevant study material "
            "to answer this question."
        )

    snippets = [
        s.strip()
        for s in context.split("\n\n")
        if s.strip()
    ][:3]

    body = "\n\n".join(
        f"• {s[:350]}{'...' if len(s) > 350 else ''}"
        for s in snippets
    )

    return (
        f"**Answer based on your uploaded material**\n\n"
        f"Question: {question}\n\n"
        f"{body}\n\n"
        f"If this still feels confusing, click "
        f"**I still don't understand** for a simpler explanation."
    )


# =========================================================
# FALLBACK REEXPLAIN
# =========================================================

def _fallback_reexplain(context: str, question: str) -> str:

    context = _clean_context(context)

    short_context = context[:700]

    return (
        f"## Simpler Explanation\n\n"
        f"### Your Question\n"
        f"{question}\n\n"
        f"### Main Idea\n"
        f"The topic can be understood by focusing on the "
        f"core concept step by step.\n\n"
        f"### From Your Material\n"
        f"{short_context}\n\n"
        f"### Study Tip\n"
        f"Try explaining the concept in your own words "
        f"using one simple sentence."
    )


# =========================================================
# FALLBACK NOTES
# =========================================================

def _fallback_notes(context: str) -> str:

    context = _clean_context(context)

    lines = [
        ln.strip()
        for ln in context.split("\n")
        if len(ln.strip()) > 20
    ]

    unique = []

    seen = set()

    for line in lines:

        normalized = line.lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        unique.append(line)

    bullets = "\n".join(
        f"- {ln[:180]}"
        for ln in unique[:8]
    )

    return (
        f"## Revision Notes\n\n"
        f"{bullets}\n\n"
        f"### Study Advice\n"
        f"- Review actively\n"
        f"- Test yourself regularly\n"
        f"- Revisit difficult concepts"
    )


# =========================================================
# FALLBACK SUMMARY
# =========================================================

def _fallback_summary(context: str) -> str:

    context = _clean_context(context)

    sentences = [
        s.strip()
        for s in re.split(r"[.!?]+\s+", context)
        if len(s.strip()) > 40
    ]

    unique = []

    seen = set()

    for sentence in sentences:

        normalized = sentence.lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        unique.append(sentence)

    if not unique:
        return (
            "- No meaningful educational content "
            "was detected in the uploaded document."
        )

    return "\n".join(
        f"- {s[:250]}"
        for s in unique[:6]
    )


# =========================================================
# FALLBACK QUIZ
# =========================================================

def _fallback_quiz(context: str) -> dict:
    """
    Generate educational MCQs from uploaded material.
    """

    context = _clean_context(context)

    sentences = [
        s.strip()
        for s in re.split(r"[.!?]+\s+", context)
        if len(s.strip()) > 70
    ]

    questions = []

    used_concepts = set()

    for sent in sentences[:30]:

        lower = sent.lower()

        if any(noise in lower for noise in [
            "created by",
            "copyright",
            "ministry",
            "page ",
        ]):
            continue

        words = [
            w.strip(".,:;!?()")
            for w in sent.split()
        ]

        candidate_words = [
            w.lower()
            for w in words
            if (
                len(w) > 6
                and w.isalpha()
                and w.lower() not in {
                    "because",
                    "therefore",
                    "however",
                    "activity",
                    "programme",
                    "question",
                    "students",
                    "teacher",
                }
            )
        ]

        if not candidate_words:
            continue

        concept = candidate_words[0]

        if concept in used_concepts:
            continue

        used_concepts.add(concept)

        question_text = (
            f"According to your uploaded material, "
            f"which statement best explains '{concept}'?"
        )

        correct_answer = sent[:180]

        wrong_answers = [
            f"{concept.capitalize()} is unrelated to the study topic.",
            f"The document states that {concept} should be ignored.",
            f"{concept.capitalize()} is presented as unimportant in the material.",
        ]

        options = [
            correct_answer,
            *wrong_answers,
        ]

        # RANDOMIZE OPTION ORDER
        random.shuffle(options)

        correct_index = options.index(correct_answer)

        explanation = (
            f"Correct answer:\n\n"
            f"{correct_answer}\n\n"
            f"This was taken directly from your uploaded study material."
        )

        questions.append({
            "question": question_text,
            "options": options,
            "correct_index": correct_index,
            "explanation": explanation,
        })

        if len(questions) >= 5:
            break

    if not questions:

        questions = [
            {
                "question": (
                    "Was enough educational material detected "
                    "to generate a meaningful quiz?"
                ),
                "options": [
                    "Yes",
                    "No",
                    "Partially",
                    "Unclear",
                ],
                "correct_index": 0,
                "explanation": (
                    "The uploaded document may not contain enough "
                    "clean educational text for quiz generation."
                ),
            }
        ]

    return {
        "title": "Study Quiz",
        "questions": questions,
    }


# =========================================================
# CHAT
# =========================================================

def chat_with_context(
    context: str,
    question: str,
    system: str = SYSTEM_TUTOR,
) -> str:

    from ai.prompts import CHAT_USER_TEMPLATE

    user_msg = CHAT_USER_TEMPLATE.format(
        context=context,
        question=question,
    )

    return generate(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]
    )


# =========================================================
# REEXPLAIN
# =========================================================

def reexplain_with_context(
    context: str,
    question: str,
    previous_answer: str,
    difficulty: int = 1,
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


# =========================================================
# STUDY MATERIAL GENERATION
# =========================================================

def generate_study_material(
    prompt_template: str,
    context: str,
    **kwargs,
) -> str:

    user_msg = prompt_template.format(
        context=context,
        **kwargs,
    )

    return generate(
        [
            {"role": "system", "content": SYSTEM_TUTOR},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
    )