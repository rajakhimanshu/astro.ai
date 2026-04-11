import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from core.user_profile_engine import (
    list_users, create_user_profile, load_user_profile,
    get_active_user_id, set_active_user, profile_to_context_text
)
from core.agent import ask_stream
from core.transit_engine import get_transit_analysis
from core.memory import init_database

# Initialize database
init_database()

app = FastAPI(title="Astro.AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    user_id: str = None

@app.get("/api/users")
def get_users():
    return {"users": list_users(), "active_user_id": get_active_user_id()}

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
        # Add formatted text version for easy UI display
        p["context_text"] = profile_to_context_text(p)
        return p
    except Exception as e:
        raise HTTPException(404, detail=str(e))

@app.post("/api/chat")
def chat(payload: ChatMessage):
    def generate():
        for chunk in ask_stream(payload.message, user_id=payload.user_id):
            yield chunk
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/api/live-sky")
def live_sky():
    try:
        return {"transit_analysis": get_transit_analysis()}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("=======================================================")
    print("  Astro.AI API Server - FastAPI")
    print("  Listening on http://0.0.0.0:8000")
    print("=======================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000)
