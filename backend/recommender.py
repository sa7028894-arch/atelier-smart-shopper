"""
Core recommendation logic for the Smart E-Commerce Personal Shopper Agent.

Pipeline:
1. Load product catalog
2. Build a pure-Python TF-IDF index over product text (description + tags
   + category) — no scipy/scikit-learn, so it installs cleanly anywhere,
   including Termux/Android where compiled scientific packages often fail.
3. Given a user query + optional filters (budget, category), retrieve top-N
   candidates via cosine similarity
4. Re-rank using a simple score blend (semantic similarity + rating)
5. Generate a natural-language explanation for each pick (template-based
   by default — see the docstring on _explain for how to swap in a real LLM).
"""

import json
import math
import re
from collections import Counter
from pathlib import Path

DATA_PATH = Path(__file__).parent / "products.json"

TOKEN_RE = re.compile(r"[a-z0-9]+")

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "of", "in", "on", "to",
    "is", "are", "it", "this", "that", "i", "want", "need", "looking",
    "some", "any", "my", "me", "please", "like", "would", "could",
}


def tokenize(text: str):
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


class ProductRecommender:
    def __init__(self, data_path: Path = DATA_PATH):
        with open(data_path, "r", encoding="utf-8") as f:
            self.products = json.load(f)

        self.corpus_tokens = [
            tokenize(f"{p['name']} {p['category']} {' '.join(p['tags'])} {p['description']}")
            for p in self.products
        ]

        # --- Build TF-IDF vectors by hand ---
        self.doc_count = len(self.corpus_tokens)
        df = Counter()
        for tokens in self.corpus_tokens:
            for term in set(tokens):
                df[term] += 1
        self.idf = {
            term: math.log((self.doc_count + 1) / (freq + 1)) + 1
            for term, freq in df.items()
        }

        self.doc_vectors = [self._vectorize(tokens) for tokens in self.corpus_tokens]
        self.doc_norms = [self._norm(vec) for vec in self.doc_vectors]

    def _vectorize(self, tokens):
        tf = Counter(tokens)
        return {term: count * self.idf.get(term, 0) for term, count in tf.items()}

    @staticmethod
    def _norm(vec):
        return math.sqrt(sum(v * v for v in vec.values())) or 1e-9

    def _cosine_sim(self, query_vec, query_norm, doc_idx):
        doc_vec = self.doc_vectors[doc_idx]
        doc_norm = self.doc_norms[doc_idx]
        # dot product over the smaller vector's keys
        shorter, longer = (query_vec, doc_vec) if len(query_vec) < len(doc_vec) else (doc_vec, query_vec)
        dot = sum(v * longer.get(term, 0) for term, v in shorter.items())
        return dot / (query_norm * doc_norm)

    # ---------- Slot extraction (lightweight, no LLM required) ----------
    def extract_budget(self, text: str):
        """Look for patterns like 'under 3000', 'below 5k', 'budget 2000'."""
        text = text.lower()
        match = re.search(r"(?:under|below|less than|budget of|around)\s*₹?\s*(\d+)(k)?", text)
        if match:
            value = int(match.group(1))
            if match.group(2):
                value *= 1000
            return value
        match = re.search(r"₹?\s*(\d{3,6})", text)
        if match:
            return int(match.group(1))
        return None

    def extract_category(self, text: str):
        text_lower = text.lower()
        categories = {p["category"].lower() for p in self.products}
        for cat in categories:
            if cat in text_lower:
                return cat
        return None

    # ---------- Retrieval ----------
    def recommend(self, query: str, budget: int = None, category: str = None, top_k: int = 4):
        query_tokens = tokenize(query)
        query_vec = self._vectorize(query_tokens)
        query_norm = self._norm(query_vec)

        scored = []
        for idx, product in enumerate(self.products):
            sim_score = self._cosine_sim(query_vec, query_norm, idx)
            if sim_score <= 0:
                continue
            if category and category not in product["category"].lower():
                continue
            if budget and product["price"] > budget:
                continue

            # Blend: semantic similarity (main signal) + normalized rating
            blended = (sim_score * 0.75) + ((product["rating"] / 5) * 0.25)
            scored.append((blended, sim_score, product))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for blended, sim_score, product in scored[:top_k]:
            results.append({
                **product,
                "match_score": round(min(sim_score, 1.0) * 100),
                "reason": self._explain(product, query, budget),
            })
        return results

    # ---------- Explanation layer ----------
    def _explain(self, product: dict, query: str, budget: int = None):
        """Template-based reasoning fallback (works with no API key).
        Swap this out for an LLM call (see app.py) for richer, conversational
        explanations — e.g. call Groq/OpenAI/Anthropic with the product's
        fields and the user's query, asking for a 1-sentence justification.
        """
        reasons = []
        matched_tags = [t for t in product["tags"] if t in query.lower()]
        if matched_tags:
            reasons.append(f"matches your interest in {', '.join(matched_tags)}")
        if budget and product["price"] <= budget:
            reasons.append(f"fits within your ₹{budget} budget")
        if product["rating"] >= 4.4:
            reasons.append(f"highly rated ({product['rating']}★)")
        if not reasons:
            reasons.append("closely matches what you described")
        return "Recommended because it " + " and ".join(reasons) + "."
