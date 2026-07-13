"""
A general-purpose conversational assistant (like a mini ChatGPT/Gemini
widget) — separate from the product-recommendation chat. Uses the same
Groq API key as llm_explainer.py. It has no retrieval/ranking logic like
recommender.py, but it IS given a compact summary of the real catalog in
its system prompt, so it doesn't invent fake facts about what Atelier
sells when asked (e.g. "we sell handmade artisanal goods" — it doesn't;
it sells the specific catalog below).
"""

import json
import os
from pathlib import Path

import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

DATA_PATH = Path(__file__).parent / "products.json"


def _build_catalog_summary():
    """A compact, token-cheap summary of the real catalog for grounding —
    not the full descriptions, just enough to answer 'what do you sell',
    'do you have X', 'what's your price range' accurately."""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            products = json.load(f)
    except Exception:
        return "No catalog data available."

    by_category = {}
    for p in products:
        by_category.setdefault(p["category"], []).append(p)

    lines = []
    for category, items in sorted(by_category.items()):
        prices = [p["price"] for p in items]
        names = ", ".join(p["name"] for p in items)
        lines.append(
            f"- {category} (₹{min(prices)}–₹{max(prices)}): {names}"
        )
    return "\n".join(lines)


CATALOG_SUMMARY = _build_catalog_summary()

SYSTEM_PROMPT = (
    "You are a helpful, friendly general-purpose AI assistant embedded as a "
    "floating widget on an e-commerce site called Atelier. You can answer "
    "any question the visitor has — not just shopping related. Be concise, "
    "warm, and direct. Use plain text, no markdown headers.\n\n"
    "Atelier's actual product catalog (this is the real, complete list — "
    "do not invent products, categories, or a different store concept "
    "beyond what's listed here):\n"
    f"{CATALOG_SUMMARY}\n\n"
    "If asked what the site sells or for product suggestions, answer only "
    "from this list. If asked something the catalog can't answer, say so "
    "plainly rather than making something up. For detailed personalized "
    "recommendations, mention the shopper can use the main chat panel on "
    "the page, which does full budget-aware matching."
)

# In-memory conversation history per widget session: {session_id: [ {role, content}, ... ]}
CONVERSATIONS = {}
MAX_HISTORY_MESSAGES = 20  # keep the last N messages to bound token usage


def _api_key():
    return os.environ.get("GROQ_API_KEY")


def is_enabled():
    return bool(_api_key())


def get_history(session_id: str):
    return CONVERSATIONS.setdefault(session_id, [])


def reset_history(session_id: str):
    CONVERSATIONS.pop(session_id, None)


def send_message(session_id: str, message: str, timeout: float = 15.0):
    """Send a message in the general assistant conversation.
    Returns (reply_text, error). error is None on success, or a short
    user-facing string if something went wrong (e.g. no key configured).
    """
    api_key = _api_key()
    if not api_key:
        return None, "The AI assistant isn't configured yet — add GROQ_API_KEY to backend/.env to enable it."

    history = get_history(session_id)
    history.append({"role": "user", "content": message})
    # Trim to bound context size
    trimmed = history[-MAX_HISTORY_MESSAGES:]

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + trimmed,
                "temperature": 0.7,
                "max_tokens": 400,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        reply = data["choices"][0]["message"]["content"].strip()
        history.append({"role": "assistant", "content": reply})
        return reply, None
    except requests.exceptions.Timeout:
        return None, "The assistant took too long to respond. Try again."
    except Exception:
        return None, "Something went wrong reaching the assistant. Try again in a moment."
