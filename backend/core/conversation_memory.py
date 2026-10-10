"""
core/conversation_memory.py — Persist and learn from each consultation turn.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from core.memory import _get_conn, init_database, embed_text, collection, add_event, get_all_events
from core.user_profile_engine import update_lived_experience, update_conversation_insights

_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}
_MONTH_ALT = "|".join(sorted(_MONTHS.keys(), key=len, reverse=True))
_DATE_DMY = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({_MONTH_ALT})(?:\s*,?\s*(\d{{4}}))?",
    re.I,
)
_DATE_MDY = re.compile(
    rf"\b({_MONTH_ALT})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{{4}}))?",
    re.I,
)
_SEMESTER = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\s+sem(?:ester)?\b", re.I)


def _ensure_conversation_table(user_id: str):
    init_database(user_id)
    conn = _get_conn(user_id)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_message TEXT,
            bot_message TEXT,
            topic TEXT,
            confidence INTEGER,
            convergence_json TEXT,
            extracted_json TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_conversation_turn(
    user_id: str,
    user_message: str,
    bot_message: str,
    brief: dict,
    extracted: Optional[dict] = None,
) -> int:
    _ensure_conversation_table(user_id)
    conn = _get_conn(user_id)
    cur = conn.execute(
        """INSERT INTO conversations
           (user_id, user_message, bot_message, topic, confidence, convergence_json, extracted_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            user_message[:4000],
            bot_message[:8000],
            brief.get("topic", "general"),
            int(brief.get("confidence", 0)),
            json.dumps(brief.get("convergence", {}), default=str),
            json.dumps(extracted or {}, default=str),
            datetime.now().isoformat(),
        ),
    )
    turn_id = cur.lastrowid
    conn.commit()
    conn.close()

    # Index for semantic recall
    doc = f"User: {user_message[:500]}\nGuruji: {bot_message[:800]}\nTopic: {brief.get('topic_label')}"
    emb = embed_text(doc)
    if emb:
        try:
            collection.add(
                documents=[doc],
                embeddings=[emb],
                metadatas=[{"user_id": user_id, "topic": brief.get("topic"), "type": "conversation"}],
                ids=[f"conv_{user_id}_{turn_id}"],
            )
        except Exception:
            pass
    return turn_id


def get_recent_conversations(user_id: str, limit: int = 8) -> List[dict]:
    _ensure_conversation_table(user_id)
    try:
        conn = _get_conn(user_id)
        rows = conn.execute(
            """SELECT user_message, bot_message, topic, confidence, created_at
               FROM conversations ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        return [
            {
                "user": r[0],
                "bot": r[1][:400],
                "topic": r[2],
                "confidence": r[3],
                "at": r[4],
            }
            for r in reversed(rows)
        ]
    except Exception:
        return []


def format_conversation_memory(user_id: str) -> str:
    rows = get_recent_conversations(user_id, limit=6)
    if not rows:
        return "No prior consultation turns stored for this profile."
    lines = ["PRIOR CONSULTATION MEMORY (learned from past chats):"]
    for i, r in enumerate(rows, 1):
        lines.append(f"  [{i}] ({r['topic']}, conf {r['confidence']}) User: {r['user'][:200]}")
        lines.append(f"      Guruji: {r['bot'][:250]}")
    return "\n".join(lines)


def _looks_like_question(text: str) -> bool:
    low = text.lower().strip()
    if len(low) < 90 and any(p in low for p in ("will i", "what will", "should i", "kya hoga")):
        return True
    return False


def _rule_extract(user_message: str) -> dict:
    """Lightweight fact extraction without LLM — concise facts, not the raw dump."""
    text = user_message.strip()
    low = text.lower()
    out: dict = {}

    if any(w in low for w in ["trade", "trading", "stock", "crypto", "forex", "account"]):
        out["trading"] = text[:400]

    prof_bits = []
    if any(w in low for w in ("internship", "intern")):
        prof_bits.append("searching for internship")
    if any(w in low for w in ("my startup", "my platform", "my business", "building a", "launching")):
        prof_bits.append("building own venture")
    sem = _SEMESTER.search(low)
    if sem:
        prof_bits.append(f"college student (semester {sem.group(1)})")
    if any(w in low for w in ("startup", "launch", "business")) and "after" in low:
        prof_bits.append("weighing job vs own business")
    if prof_bits:
        out["profession"] = "; ".join(dict.fromkeys(prof_bits))
    elif any(w in low for w in ["job", "work", "company", "business", "startup", "firm"]) and not _looks_like_question(text):
        out["profession"] = text[:300]

    if any(w in low for w in [
        "girlfriend", "boyfriend", "marriage", "love", "relationship", "partner",
        "crush", "propose", "proposal", "rejected", "girl", "feelings", "dating",
    ]):
        out["relationships"] = text[:500]

    if any(w in low for w in [
        "college", "semester", "exam", "study", "degree", "btech",
        "engineering", "backlog", "supplementary", "paper",
    ]):
        if "profession" not in out:
            out["profession"] = "college student"
        if any(w in low for w in ("backlog", "supplementary", "fail", "pass")):
            out["struggles"] = "academic pressure — clearing exams / backlog risk"
            out["goals"] = "clear exams and pass the semester"

    if any(w in low for w in ["struggle", "stuck", "fail", "loss", "blow", "depressed", "stress"]):
        out.setdefault("struggles", text[:300])
    if any(w in low for w in ["goal", "want to", "plan to", "dream", "ambition"]):
        out.setdefault("goals", text[:300])

    if any(w in low for w in ["rejected", "backlog", "fail", "worried", "anxious", "fear", "confused", "lost"]):
        out["emotional_tone"] = "anxious / seeking clarity"
    elif any(w in low for w in ["happy", "excited", "hope", "confident", "pulled"]):
        out["emotional_tone"] = "intense / emotionally charged"

    return out


def _years_in_text(text: str) -> List[int]:
    return [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]


def _infer_year(month: int, day: int, text: str, today: datetime) -> int:
    years = _years_in_text(text)
    if years:
        # Prefer a year that produces a plausible (not far-future) date
        for y in years:
            try:
                dt = datetime(y, month, day)
            except ValueError:
                continue
            if abs((dt - today).days) <= 800:
                return y
        return years[0]
    try:
        this_year = datetime(today.year, month, day)
    except ValueError:
        return today.year
    # Stories are usually about the past
    if this_year <= today:
        return today.year
    return today.year - 1


def _iso_date(year: int, month: int, day: int) -> Optional[str]:
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _title_from_window(text: str, start: int, end: int) -> tuple:
    """Return (title, domain, emotion, outcome) from text close to a date match."""
    local = text[max(0, start - 55): min(len(text), end + 60)].lower()
    whole = text.lower()

    if any(w in local for w in ("propose", "proposal")):
        rejected = any(w in local for w in ("reject", "no feeling", "did not have", "didn't have"))
        if rejected:
            return ("Proposal rejected", "relationship", -3, "No reciprocal feelings")
        return ("Proposed to partner", "relationship", 1, "")
    if any(w in local for w in ("reject", "no feeling")):
        return ("Romantic rejection", "relationship", -3, "No reciprocal feelings")
    if any(w in local for w in ("met someone", "meet someone", "started dating", "fell for")):
        return ("Met a romantic interest", "relationship", 2, "Strong pull / attachment")
    if any(w in whole for w in ("backlog", "supplementary")) and any(w in local for w in ("exam", "paper")):
        return ("Backlog / supplementary exam", "education", -2, "Risk if not cleared")
    if any(w in local for w in ("exam", "paper")):
        return ("Semester exam", "education", -1, "")
    if "intern" in local:
        return ("Internship search / movement", "career", 1, "")
    if any(w in local for w in ("job", "firm", "joined")):
        return ("Career / work event", "career", 1, "")
    if any(w in local for w in ("launch", "platform", "startup")):
        return ("Started building own platform", "career", 2, "")
    return ("Life event", "general", 0, "")


def extract_dated_events(user_message: str, today: Optional[datetime] = None) -> List[dict]:
    """Pull dated (and a few undated) life facts from a chat message."""
    today = today or datetime.now()
    text = user_message.strip()
    if len(text) < 8:
        return []
    events: List[dict] = []
    seen_dates = set()

    def _add(date_s: str, title: str, domain: str, emotion: int, outcome: str, desc: str):
        key = (date_s, title.lower()[:40])
        if key in seen_dates:
            return
        seen_dates.add(key)
        events.append({
            "date": date_s,
            "title": title[:80],
            "description": desc[:400],
            "domain": domain,
            "emotion_score": emotion,
            "outcome": outcome[:200],
        })

    for m in _DATE_DMY.finditer(text):
        day, mon, year_s = int(m.group(1)), _MONTHS[m.group(2).lower()], m.group(3)
        year = int(year_s) if year_s else _infer_year(mon, day, text, today)
        date_s = _iso_date(year, mon, day)
        if not date_s:
            continue
        title, domain, emotion, outcome = _title_from_window(text, m.start(), m.end())
        _add(date_s, title, domain, emotion, outcome, text[max(0, m.start() - 60): m.end() + 80].strip())

    for m in _DATE_MDY.finditer(text):
        mon, day, year_s = _MONTHS[m.group(1).lower()], int(m.group(2)), m.group(3)
        year = int(year_s) if year_s else _infer_year(mon, day, text, today)
        date_s = _iso_date(year, mon, day)
        if not date_s:
            continue
        title, domain, emotion, outcome = _title_from_window(text, m.start(), m.end())
        _add(date_s, title, domain, emotion, outcome, text[max(0, m.start() - 60): m.end() + 80].strip())

    low = text.lower()
    # Undated but clearly a current life fact
    if any(w in low for w in ("internship", "intern")) and not any(e["domain"] == "career" and "intern" in e["title"].lower() for e in events):
        _add(today.strftime("%Y-%m-%d"), "Searching for internship", "career", 1, "", text[:300])
    sem = _SEMESTER.search(low)
    if sem and not any(e["domain"] == "education" for e in events):
        _add(today.strftime("%Y-%m-%d"), f"Currently in semester {sem.group(1)}", "education", 0, "", text[:200])

    # Collapse duplicate dates — keep the first (usually the more specific mention)
    unique: List[dict] = []
    seen = set()
    for ev in events:
        key = (ev["date"], ev["domain"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(ev)
    return unique


def _event_is_duplicate(existing: List[dict], candidate: dict) -> bool:
    c_title = (candidate.get("title") or "").lower().strip()
    c_date = candidate.get("date") or ""
    is_status = c_title == "searching for internship" or c_title.startswith("currently in semester")
    for ev in existing:
        t = (ev.get("title") or "").lower().strip()
        d = ev.get("date") or ""
        if is_status and t == c_title:
            return True
        if d == c_date and (c_title == t or c_title[:28] in t or t[:28] in c_title):
            return True
        if c_title == t and d[:7] == c_date[:7]:
            return True
    return False


def log_life_events_from_message(user_id: str, user_message: str) -> List[dict]:
    """
    Parse a chat message, save dated life facts into the Events archive (SQLite),
    and return the events that were newly written.
    """
    if not user_id or not user_message or len(user_message.strip()) < 8:
        return []
    parsed = extract_dated_events(user_message)
    if not parsed:
        return []
    existing = get_all_events(user_id)
    saved = []
    for ev in parsed:
        if _event_is_duplicate(existing, ev) or _event_is_duplicate(saved, ev):
            continue
        try:
            add_event(
                date=ev["date"],
                title=ev["title"],
                description=ev.get("description") or user_message[:400],
                domain=ev.get("domain") or "general",
                emotion_score=int(ev.get("emotion_score") or 0),
                outcome=ev.get("outcome") or "",
                user_id=user_id,
            )
            saved.append(ev)
            existing.append(ev)
        except Exception as e:
            print(f"  [LIFE EVENT] skip '{ev.get('title')}': {e}")
    return saved


def format_logged_events(events: List[dict]) -> str:
    if not events:
        return ""
    lines = ["RECORDED AS LIFE EVENTS THIS TURN (acknowledge these, do not ignore):"]
    for ev in events:
        lines.append(f"  • {ev['date']} — {ev['title']} [{ev.get('domain', 'general')}]")
    return "\n".join(lines)


def learn_from_turn(user_id: str, user_message: str, bot_message: str, brief: dict) -> dict:
    """
    Extract learnings from a turn, merge into profile lived_experience + conversation_insights.
    Returns extracted dict.
    """
    extracted: dict = {}

    extracted.update(_rule_extract(user_message))

    logged = log_life_events_from_message(user_id, user_message)
    if logged:
        extracted["life_events"] = "; ".join(f"{e['date']}: {e['title']}" for e in logged)
        extracted["_logged_events"] = logged

    # LLM extraction for longer messages — facts only, never overwrite dated events
    if len(user_message.strip()) >= 40:
        try:
            from core.agent import LivedExperienceExtractor
            llm_data = LivedExperienceExtractor().extract_from_text(user_message)
            llm_data = {k: v for k, v in (llm_data or {}).items() if v}
            for k, v in llm_data.items():
                if k in ("life_events",) or k.startswith("_"):
                    continue
                if k == "profession" and _looks_like_question(str(v)):
                    continue
                if v and k not in extracted:
                    extracted[k] = v
        except Exception:
            pass

    if not extracted:
        return {}

    lived_patch = {k: v for k, v in extracted.items() if k in (
        "profession", "struggles", "goals", "life_events", "emotional_tone"
    )}
    if lived_patch:
        update_lived_experience(user_id, lived_patch)

    insights_patch = {k: v for k, v in extracted.items() if k in ("trading", "relationships")}
    if insights_patch:
        update_conversation_insights(user_id, insights_patch)

    return extracted
