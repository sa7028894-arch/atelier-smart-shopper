# Atelier — Smart E-Commerce Personal Shopper & Recommendation Agent

A conversational shopping agent: you describe what you want in plain language,
it asks one clarifying question if needed, then retrieves and explains
product recommendations from a catalog.

## How it works

1. **Retrieval** — `backend/recommender.py` builds a TF-IDF index over the
   product catalog (`backend/products.json`) and ranks products by cosine
   similarity to your query, blended with product rating.
2. **Slot filling** — the agent extracts budget and category from your
   messages (e.g. "under 4000", "gaming laptop") and asks one clarifying
   question if a budget isn't mentioned.
3. **Explanation** — each recommendation comes with a plain-English reason
   (matched tags, budget fit, rating). This is template-based by default so
   the whole app works with **no API key**. See "Upgrading to a real LLM"
   below to make explanations fully generative.
4. **Frontend** — a chat panel + catalog-style results grid, with a circular
   "match %" dial as the visual signature of each recommendation.

## Floating general assistant widget

There's also a separate floating "AI" chat bubble (bottom-right corner of
the page) — a general-purpose assistant like a mini ChatGPT/Gemini, kept
completely separate from the shopping agent. It can answer anything, not
just product questions.

- Backend: `backend/general_assistant.py` + `/api/assistant/chat` route
- Frontend: `frontend/src/components/FloatingAssistant.jsx`
- Uses the same `GROQ_API_KEY` as the recommendation explanations — no
  extra setup needed if you've already added the key
- If no key is set, it shows a clear message instead of crashing

## Project structure

```
smart-shopper/
├── backend/
│   ├── app.py            # Flask API (chat, session, products)
│   ├── recommender.py    # TF-IDF retrieval + slot extraction
│   ├── products.json     # sample catalog (30 products)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── components/ChatPanel.jsx
    │   ├── components/ProductCard.jsx
    │   └── components/MatchDial.jsx
    └── .env              # VITE_API_URL
```

## Run it locally

**1. Backend**

```
cd backend
pip install -r requirements.txt
python app.py
```

This starts the API on `http://localhost:5000`.

**2. Frontend** (in a new terminal)

```
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`).

## Upgrading to a real LLM (already built in — just add a key)

The app now has a real LLM layer wired in (`backend/llm_explainer.py`), using
Groq's free API. **It's optional** — with no key, everything falls back to
the template-based explanations, so the app always works.

To turn it on:

1. Get a free API key at `https://console.groq.com`
2. In `backend/`, copy `.env.example` to `.env`:
   ```
   cp .env.example .env
   ```
3. Paste your key into `.env`:
   ```
   GROQ_API_KEY=your_key_here
   ```
4. Restart the backend (`python app.py`)

Once enabled:
- Each product's `reason` is generated live by an LLM based on the actual
  query and product details, instead of the template
- The chat intro line ("Here's what I'd suggest...") also becomes
  LLM-generated for a more natural tone
- The frontend shows a small **AI** badge on any card whose explanation came
  from the LLM (`reason_source: "llm"` vs `"template"` in the API response)
- If the Groq call fails for any reason (rate limit, network, bad key), it
  silently falls back to the template — the app never breaks because of this

You could extend this further by also using the LLM for slot extraction
(budget/category) instead of the regex-based `extract_budget`/
`extract_category` in `recommender.py` — more robust for messy phrasing.

## Deploying

- **Backend**: Render, Railway, or PythonAnywhere (free tiers work fine for
  a class project).
- **Frontend**: Vercel or Netlify. Set `VITE_API_URL` in the frontend's
  environment variables to your deployed backend URL.

## Extending the catalog

Add more entries to `backend/products.json` following the existing shape
(`id`, `name`, `category`, `price`, `rating`, `tags`, `description`). No
retraining needed — the TF-IDF index rebuilds on server start.
