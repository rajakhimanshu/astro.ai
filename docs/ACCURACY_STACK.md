# Jyotish AI — Accuracy Stack (Local Run)

This document describes how to run the full accuracy pipeline locally (₹0) and how the system learns from your chart.

## Quick start (Windows)

### 1. Backend (port 8001)

```powershell
cd backend
pip install -r requirements.txt
# Optional: set GROQ_API_KEY in .env for faster LLM (free tier)
# Optional: run Ollama locally for RAG embeddings (nomic-embed-text)
python main.py
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` — API points to `http://127.0.0.1:8001/api`.

## Accuracy layers (in order of impact)

| Layer | Module | What it does |
|-------|--------|--------------|
| **Convergence gate** | `convergence_scorer.py` | 7-signal score; forbids precise dates when confidence is low |
| **Nakshatra gochara** | `nakshatra_gochara_engine.py` | Transit nakshatra ↔ natal anchors (Magha/Ketu/Sun style) |
| **Kakshya / BAV** | `kakshya_engine.py` | 3°45′ delivery windows via Ashtakavarga |
| **Tarabala + Chandrabala** | `gochara_bala_engine.py` | Daily transit quality for the native Moon |
| **Prediction ledger** | `prediction_ledger.py` | Auto-logs timing questions; verify hit/miss |
| **Empirical ML** | `memory.py` | Learns from life events + verified predictions |
| **Rectification** | `rectification_engine.py` | Refines birth time from ≥3 logged events |

## Learning loop

1. **Ask** timing questions in Consultation → predictions auto-log to DB.
2. **Verify** in the **Predictions** tab (Yes/No) → hit rate updates.
3. **Log life events** in Events tab → empirical planet scores update.
4. **Run rectification** via `POST /api/users/{id}/rectify` after 3+ events.

## API endpoints

- `GET /api/users/{id}/convergence?question=...`
- `GET /api/users/{id}/gochara?question=...`
- `GET /api/users/{id}/kakshya`
- `GET /api/users/{id}/gochara-bala`
- `GET /api/users/{id}/predictions`
- `POST /api/users/{id}/predictions/{id}/verify` — body: `{ "happened": true }`
- `GET /api/users/{id}/accuracy`

## Oracle Cloud (optional, free tier)

Deploy backend Docker on Ampere Always Free (2 OCPU / 12 GB). Point frontend `API_BASE` to your VPS IP. Swiss Ephemeris + SQLite work on ARM.

## YouTube knowledge ingest

1. Start **Ollama** and run `ollama pull nomic-embed-text`
2. Install: `pip install youtube-transcript-api yt-dlp deep-translator langdetect`
3. **UI:** Knowledge tab → paste video or playlist URL → **Ingest & Learn**
4. **CLI:** `python scripts/ingest_youtube.py "https://youtube.com/..."`

| Language | Handling |
|----------|----------|
| Hindi (Devanagari captions) | Auto-translated to English for RAG search |
| Hinglish | Kept + optional English gloss |
| English | Indexed as-is |

Playlists require `yt-dlp` on PATH. Videos need captions enabled on YouTube.

## Astrology-only chat

Non-Jyotish questions are blocked before the LLM runs (code, recipes, general trivia). Greetings and chart follow-ups still work.


- Software encodes technique; it does not guarantee outcomes.
- Hit rate improves only after you verify predictions and log events.
- Shadbala/Bhava Bala still ~25% off reference — ranks are usable, absolute rupas are approximate.
