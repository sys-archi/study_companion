"""Prompt templates for RAG and study companion flows."""

SYSTEM_TUTOR = """You are a friendly, patient study companion for school students.
Answer ONLY using the provided study material context.
If the context does not contain enough information, say so clearly — do not invent facts.
Use clear, educational language appropriate for students.
Structure answers with short paragraphs or bullet points when helpful."""

CHAT_USER_TEMPLATE = """Study material context:
---
{context}
---

Student question: {question}

Provide a helpful, accurate explanation based on the context above."""

REEXPLAIN_USER_TEMPLATE = """The student did not understand your previous explanation.

Previous explanation:
{previous_answer}

Study material context:
---
{context}
---

Original question: {question}

Re-explain using a SIMPLER approach:
1. Use simpler words and shorter sentences
2. Give a real-world analogy or example
3. Break the concept into numbered steps
4. List 2-3 concepts that might be confusing (as "Watch out for:")
5. End with one check question to verify understanding

Difficulty level: {difficulty} (1=simplest, higher=more detail)"""

GENERATE_NOTES_TEMPLATE = """Based ONLY on this study material, create concise revision notes.

Material:
---
{context}
---

Format:
- Title line
- 5-8 bullet key points
- 2-3 "Remember:" tips
Keep it student-friendly."""

GENERATE_QUIZ_TEMPLATE = """Based ONLY on this study material, create a short quiz.

Material:
---
{context}
---

Return valid JSON with this exact structure:
{{
  "title": "Quiz title",
  "questions": [
    {{
      "question": "Question text",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "Why this is correct"
    }}
  ]
}}

Create exactly 5 multiple-choice questions. Ground every question in the material."""

GENERATE_SUMMARY_TEMPLATE = """Summarize this study material in 3-5 bullet points for quick revision.

Material:
---
{context}
---"""
