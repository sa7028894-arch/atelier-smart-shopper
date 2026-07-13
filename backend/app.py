import os
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from recommender import ProductRecommender
import llm_explainer
import general_assistant

load_dotenv()

app = Flask(__name__)
CORS(app)

recommender = ProductRecommender()

# In-memory session store: {session_id: {"turns": int, "text": str, "budget": int, "category": str}}
SESSIONS = {}

CLARIFYING_QUESTIONS = [
    "Got it — what's your budget for this?",
    "Nice choice. Any brand, color, or feature you care about most?",
    "Is this for daily use, a specific occasion, or a gift?",
]


def get_session(session_id: str):
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {"turns": 0, "text": "", "budget": None, "category": None}
    return SESSIONS[session_id]


@app.route("/api/session", methods=["POST"])
def new_session():
    session_id = str(uuid.uuid4())
    get_session(session_id)
    return jsonify({"session_id": session_id})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    session = get_session(session_id)
    session["turns"] += 1
    session["text"] += " " + message

    # Update slots from the cumulative conversation
    budget = recommender.extract_budget(session["text"])
    category = recommender.extract_category(session["text"])
    if budget:
        session["budget"] = budget
    if category:
        session["category"] = category

    # Ask at most one clarifying question, only on the first turn, and only
    # if we have neither a budget nor a clear enough query to retrieve well.
    if session["turns"] == 1 and not session["budget"]:
        question = CLARIFYING_QUESTIONS[0]
        return jsonify({
            "session_id": session_id,
            "type": "question",
            "message": question,
            "products": [],
        })

    results = recommender.recommend(
        query=session["text"],
        budget=session["budget"],
        category=session["category"],
        top_k=4,
    )

    if not results:
        return jsonify({
            "session_id": session_id,
            "type": "no_results",
            "message": "I couldn't find a close match — try widening your budget or describing it differently.",
            "products": [],
        })

    # Enhance with LLM-generated explanations if GROQ_API_KEY is configured.
    # Falls back silently to the template-based reason already on each
    # product if the LLM call fails or isn't configured.
    if llm_explainer.is_enabled():
        for product in results:
            llm_reason = llm_explainer.generate_explanation(
                product, session["text"], session["budget"]
            )
            if llm_reason:
                product["reason"] = llm_reason
                product["reason_source"] = "llm"
            else:
                product["reason_source"] = "template"
    else:
        for product in results:
            product["reason_source"] = "template"

    intro = llm_explainer.generate_intro_message(message, len(results)) if llm_explainer.is_enabled() else None
    reply_message = intro or f"Here's what I'd suggest based on \"{message}\":"

    return jsonify({
        "session_id": session_id,
        "type": "recommendations",
        "message": reply_message,
        "products": results,
    })


@app.route("/api/products", methods=["GET"])
def all_products():
    return jsonify(recommender.products)


@app.route("/api/assistant/chat", methods=["POST"])
def assistant_chat():
    """General-purpose chat widget — separate from the shopping agent above.
    No product retrieval here, just open-ended conversation via Groq.
    """
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not message:
        return jsonify({"session_id": session_id, "message": "", "error": "Empty message."}), 400

    reply, error = general_assistant.send_message(session_id, message)

    return jsonify({
        "session_id": session_id,
        "message": reply,
        "error": error,
    })


@app.route("/api/assistant/reset", methods=["POST"])
def assistant_reset():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")
    if session_id:
        general_assistant.reset_history(session_id)
    return jsonify({"ok": True})


@app.route("/api/reset", methods=["POST"])
def reset():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")
    if session_id in SESSIONS:
        del SESSIONS[session_id]
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
