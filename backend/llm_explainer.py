"""
Optional LLM layer for generating natural-language recommendation
explanations using Groq's free/fast API.

Design: this is a thin, isolated wrapper. If GROQ_API_KEY isn't set, or the
API call fails for any reason (network, rate limit, bad key), every
function here returns None and the caller (recommender.py / app.py) falls
back to the template-based explanation. The app never breaks because of
this layer — it only enhances it when available.
"""

import os
import json
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # fast + free-tier friendly

SYSTEM_PROMPT = (
    "You are a concise personal shopping assistant. Given a product and what "
    "the shopper asked for, write exactly ONE short sentence (max 20 words) "
    "explaining why this product is a good match. Be specific and natural, "
    "not generic. Do not repeat the product name verbatim if avoidable. "
    "Do not use markdown, quotes, or a trailing period space."
)


def _api_key():
    return os.environ.get("GROQ_API_KEY")


def is_enabled():
    return bool(_api_key())


def generate_explanation(product: dict, query: str, budget: int = None, timeout: float = 6.0):
    """Return an LLM-generated 1-sentence explanation, or None on any failure."""
    api_key = _api_key()
    if not api_key:
        return None

    user_context = {
        "shopper_query": query,
        "budget": budget,
        "product": {
            "name": product["name"],
            "category": product["category"],
            "price": product["price"],
            "rating": product["rating"],
            "tags": product["tags"],
            "description": product["description"],
        },
    }

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(user_context)},
                ],
                "temperature": 0.6,
                "max_tokens": 60,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text if text else None
    except Exception:
        # Network issue, bad key, rate limit, unexpected response shape, etc.
        # Silently fall back — this layer is an enhancement, not a dependency.
        return None


def generate_intro_message(query: str, product_count: int, timeout: float = 6.0):
    """Optional: a more natural intro line for the recommendations reply."""
    api_key = _api_key()
    if not api_key:
        return None

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly personal shopping assistant. Write ONE short, "
                            "warm sentence introducing a list of product recommendations you "
                            "found for the shopper's request. No markdown, no product names "
                            "(they'll be shown separately), max 18 words."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Shopper asked for: {query}. Found {product_count} matching products.",
                    },
                ],
                "temperature": 0.7,
                "max_tokens": 40,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text if text else None
    except Exception:
        return None
