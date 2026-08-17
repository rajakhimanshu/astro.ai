import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── FastAPI app must be created FIRST before any routes ──────────────────────
app = FastAPI(title="Astro.AI API — World-Class Jyotish Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Now import everything else ────────────────────────────────────────────────
from core.user_profile_engine import (
    list_users, create_user_profile, load_user_profile,
    get_active_user_id, set_active_user, profile_to_context_text,
    update_lived_experience
)
from core.agent import ask_stream, set_llm_mode, set_groq_model
from core.memory import init_database, add_event, get_all_events
from core.transit_engine import get_transit_analysis
from core.rectification_engine import rectify_user_profile
from core.convergence_scorer import score_convergence, format_convergence_report, detect_topic

# Initialize database on startup
init_database()

# ── Pydantic Models ───────────────────────────────────────────────────────────

class BirthInfo(BaseModel):
    name: str
    gender: str = "Male"
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    nation: str
    timezone: str = "UTC"

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_history: Optional[List[dict]] = []

class ConfigUpdate(BaseModel):
    llm_mode: Optional[str] = None
    groq_model: Optional[str] = None

class LivedExperienceUpdate(BaseModel):
    profession: Optional[str] = None
    struggles: Optional[str] = None
    goals: Optional[str] = None
    life_events: Optional[str] = None
    emotional_tone: Optional[str] = None

class UserStory(BaseModel):
    story: str

class LifeEvent(BaseModel):
    date: str                    # Format: YYYY-MM-DD
    title: str
    description: str
    domain: str                  # e.g. "career", "health", "relationship", "finance"
    emotion_score: int = 0       # -5 to +5
    outcome: str = ""

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/users")
def get_users():
    from core.agent import LLM_MODE, GROQ_MODEL
    return {
        "users": list_users(),
        "active_user_id": get_active_user_id(),
        "llm_mode": LLM_MODE,
        "groq_model": GROQ_MODEL
    }

@app.post("/api/config")
def update_config(config: ConfigUpdate):
    if config.llm_mode:
        if not set_llm_mode(config.llm_mode):
            raise HTTPException(400, detail="Invalid LLM mode. Choose 'ollama' or 'groq'.")
    if config.groq_model:
        set_groq_model(config.groq_model)
    return {"status": "success", "llm_mode": config.llm_mode, "groq_model": config.groq_model}

@app.post("/api/users")
def create_profile(info: BirthInfo):
    uid = create_user_profile(info.model_dump())
    set_active_user(uid)
    return {"status": "success", "user_id": uid}

@app.post("/api/users/active")
def set_active(payload: dict):
    uid = payload.get("user_id")
    if uid:
        set_active_user(uid)
        return {"status": "success", "active_user": uid}
    raise HTTPException(400, detail="Missing user_id")

@app.get("/api/users/{user_id}/profile")
def get_profile(user_id: str):
    try:
        p = load_user_profile(user_id)
        p["context_text"] = profile_to_context_text(p)
        return p
    except Exception as e:
        raise HTTPException(404, detail=str(e))

@app.post("/api/users/{user_id}/experience")
def update_experience(user_id: str, data: LivedExperienceUpdate):
    update_lived_experience(user_id, data.model_dump(exclude_unset=True))
    return {"status": "success"}

@app.post("/api/users/{user_id}/story")
def process_story(user_id: str, payload: UserStory):
    from core.agent import _extract_and_save_lived_experience
    _extract_and_save_lived_experience(payload.story, user_id)
    return {"status": "success", "message": "Story processed and context extracted."}

# ── Life Events Endpoints ─────────────────────────────────────────────────────

@app.post("/api/users/{user_id}/events")
def log_event(user_id: str, event: LifeEvent):
    """Log a significant life event — feeds the ML Empirical Feedback Engine."""
    try:
        event_id = add_event(
            user_id=user_id,
            date=event.date,
            title=event.title,
            description=event.description,
            domain=event.domain,
            emotion_score=event.emotion_score,
            outcome=event.outcome
        )
        return {"status": "success", "event_id": event_id, "message": "Event logged and indexed."}
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to log event: {str(e)}")

@app.get("/api/users/{user_id}/events")
def get_events(user_id: str):
    """Retrieve all logged life events for a user."""
    try:
        events = get_all_events(user_id)
        return {"status": "success", "events": events}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/api/users/{user_id}/rectify")
def rectify_profile(user_id: str, payload: dict = None):
    """
    Birth-time rectification from logged life events.
    Requires ≥3 events. Updates birth time when confidence is medium/high.
    """
    window = 30
    if payload and isinstance(payload.get("window_minutes"), int):
        window = max(5, min(120, payload["window_minutes"]))
    try:
        result = rectify_user_profile(user_id, window_minutes=window)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/users/{user_id}/gochara")
def get_gochara(user_id: str, question: str = ""):
    """Nakshatra-level transit activations (Magha/Ketu/lagna-lord style analysis)."""
    try:
        from core.nakshatra_gochara_engine import format_gochara_report, analyze_nakshatra_activations
        profile = load_user_profile(user_id)
        return {
            "status": "success",
            "report": format_gochara_report(profile, question),
            "data": analyze_nakshatra_activations(profile),
        }
    except Exception as e:
        raise HTTPException(404, detail=str(e))


@app.get("/api/users/{user_id}/convergence")
def get_convergence(user_id: str, topic: str = "general", question: str = ""):
    """Returns convergence score and timing mandate for a topic."""
    try:
        profile = load_user_profile(user_id)
        t = topic if topic != "general" else detect_topic(question)
        result = score_convergence(profile, topic=t, question=question)
        return {
            "status": "success",
            "report": format_convergence_report(result),
            "data": result,
        }
    except Exception as e:
        raise HTTPException(404, detail=str(e))


@app.get("/api/users/{user_id}/predictions")
def list_predictions(user_id: str, pending_only: bool = False):
    try:
        from core.prediction_ledger import get_pending_predictions, get_all_predictions
        preds = get_pending_predictions(user_id) if pending_only else get_all_predictions(user_id)
        return {"status": "success", "predictions": preds}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


class PredictionVerify(BaseModel):
    happened: bool
    outcome_date: str = ""
    outcome_note: str = ""
    emotion_score: int = 0


class YouTubeIngestRequest(BaseModel):
    urls: List[str]
    force: bool = False


@app.get("/api/knowledge/stats")
def knowledge_stats():
    try:
        from core.knowledge_base import get_knowledge_stats
        return {"status": "success", "data": get_knowledge_stats()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/api/knowledge/youtube")
def ingest_youtube(payload: YouTubeIngestRequest):
    """
    Paste YouTube video or playlist URLs — captions are fetched, normalized
    (Hindi / English / Hinglish), and indexed into the RAG knowledge base.
    Requires Ollama (nomic-embed-text). Playlists need yt-dlp.
    """
    urls = [u.strip() for u in (payload.urls or []) if u and u.strip()]
    if not urls:
        raise HTTPException(400, detail="Provide at least one YouTube URL")
    try:
        from core.youtube_ingest import ingest_urls
        result = ingest_urls(urls, force=payload.force)
        return {"status": "success", **result}
    except RuntimeError as e:
        raise HTTPException(503, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/api/users/{user_id}/predictions/{prediction_id}/verify")
def verify_user_prediction(user_id: str, prediction_id: int, body: PredictionVerify):
    try:
        from core.prediction_ledger import verify_prediction
        result = verify_prediction(
            user_id, prediction_id, body.happened,
            outcome_date=body.outcome_date,
            outcome_note=body.outcome_note,
            emotion_score=body.emotion_score,
        )
        if result.get("error"):
            raise HTTPException(404, detail=result["error"])
        return {"status": "success", **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/users/{user_id}/accuracy")
def get_accuracy(user_id: str):
    try:
        from core.accuracy_engine import compute_accuracy_report, format_accuracy_report
        report = compute_accuracy_report(user_id)
        return {
            "status": "success",
            "report": format_accuracy_report(user_id),
            "data": report,
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/users/{user_id}/kakshya")
def get_kakshya(user_id: str):
    try:
        from core.kakshya_engine import format_kakshya_report
        profile = load_user_profile(user_id)
        return {"status": "success", "report": format_kakshya_report(profile)}
    except Exception as e:
        raise HTTPException(404, detail=str(e))


@app.get("/api/users/{user_id}/gochara-bala")
def get_gochara_bala(user_id: str):
    try:
        from core.gochara_bala_engine import format_gochara_bala_report
        profile = load_user_profile(user_id)
        return {"status": "success", "report": format_gochara_bala_report(profile)}
    except Exception as e:
        raise HTTPException(404, detail=str(e))

# ── Chat Endpoint ─────────────────────────────────────────────────────────────

@app.post("/api/chat")
def chat(payload: ChatMessage):
    """
    Streaming chat endpoint. Accepts optional conversation_history for multi-turn awareness.
    The history is a list of {role: 'user'|'bot', content: str} objects.
    """
    def generate():
        try:
            for chunk in ask_stream(
                question=payload.message,
                user_id=payload.user_id,
                conversation_history=payload.conversation_history or []
            ):
                yield chunk
        except Exception as e:
            yield f"\n⚠️ Server error: {str(e)[:300]}\n"
    return StreamingResponse(generate(), media_type="text/plain")

# ── Utility Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/live-sky")
def live_sky():
    try:
        return {"transit_analysis": get_transit_analysis()}
    except Exception as e:
        return {"error": str(e)}

# ── Server Entry ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=======================================================")
    print("  Astro.AI API Server — World-Class Jyotish Engine")
    print("  Listening on http://0.0.0.0:8001")
    print("=======================================================")
    uvicorn.run(app, host="0.0.0.0", port=8001)
