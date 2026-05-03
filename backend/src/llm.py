"""
llm.py — Groq LLM (free tier) via OpenAI-compatible SDK.

Groq is 100% cloud — no local model download needed.
Models available free: llama-3.1-8b-instant, llama-3.1-70b-versatile,
                       mixtral-8x7b-32768, gemma2-9b-it
"""

from __future__ import annotations
import logging
from groq import Groq
from .config import GROQ_API_KEY, GROQ_MODEL
from .models import SourceChunk, Message

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are NutriBot, an expert AI nutritionist powered by the Human Nutrition textbook.

Your expertise covers:
- Macronutrients (proteins, carbohydrates, fats) and their metabolic roles
- Micronutrients (vitamins, minerals) and deficiency symptoms
- Meal planning, dietary patterns (Mediterranean, keto, vegan, plant-based)
- Weight management, metabolism, and body composition
- Sports nutrition and physical performance
- Digestive health and gut microbiome

Guidelines:
1. Base your answers PRIMARILY on the provided CONTEXT from the knowledge base
2. Cite source numbers like [1], [2] and mention page numbers when available
3. If context doesn't fully answer the question, say so and give general guidance
4. Recommend consulting a registered dietitian for personalized medical advice
5. Be friendly, clear, and structured — use bullet points for complex topics
6. Keep responses focused and practical (150–300 words)"""


def build_context(chunks: list[SourceChunk]) -> str:
    if not chunks:
        return "No specific context retrieved from the knowledge base."
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[{i}] (Page {c.page}, Relevance: {c.similarity:.0%})\n{c.content}"
        )
    return "\n\n---\n\n".join(parts)


def generate_answer(
    query: str,
    chunks: list[SourceChunk],
    history: list[Message],
) -> tuple[str, int]:
    """
    Generate a grounded answer using Groq (cloud, free tier).
    Returns (answer_text, total_tokens_used).
    """
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com"
        )

    client = Groq(api_key=GROQ_API_KEY)
    context = build_context(chunks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Last 6 turns of conversation history
    for msg in history[-6:]:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({
        "role": "user",
        "content": f"CONTEXT FROM KNOWLEDGE BASE:\n{context}\n\nUSER QUESTION: {query}",
    })

    logger.info(f"Calling Groq ({GROQ_MODEL})…")
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,  # type: ignore[arg-type]
        temperature=0.4,
        max_tokens=600,
        top_p=0.9,
    )

    answer = completion.choices[0].message.content or ""
    tokens = completion.usage.total_tokens if completion.usage else 0
    logger.info(f"Groq response received ({tokens} tokens)")
    return answer.strip(), tokens
