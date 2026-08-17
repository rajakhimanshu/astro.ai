"""
core/prediction_ledger.py
────────────────────────────────────────────────────────────────────────
Prediction Ledger — every timing claim is stored, scored, and used to
calibrate future readings. This is how the system learns to beat generic advice.
────────────────────────────────────────────────────────────────────────
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from core.memory import _get_conn, init_database
from core.convergence_scorer import score_convergence, detect_topic
from core.nakshatra_gochara_engine import analyze_nakshatra_activations


def _init_predictions_table(user_id: str):
    init_database(user_id)
    conn = _get_conn(user_id)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            question TEXT,
            topic TEXT,
            prediction_text TEXT,
            window_start TEXT,
            window_end TEXT,
            confidence INTEGER,
            convergence_json TEXT,
            gochara_json TEXT,
            dasha_snapshot TEXT,
            status TEXT DEFAULT 'pending',
            outcome TEXT,
            outcome_date TEXT,
            outcome_score INTEGER,
            verified_at TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def _estimate_window(confidence: int, can_narrow: bool) -> tuple[str, str]:
    today = datetime.now()
    if can_narrow and confidence >= 65:
        end = today + timedelta(days=90)
    elif confidence >= 45:
        end = today + timedelta(days=180)
    else:
        end = today + timedelta(days=365)
    return today.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _build_prediction_text(topic: str, conv: dict, gochara: dict) -> str:
    label = conv.get("label", topic)
    conf = conv.get("confidence", 0)
    mandate = conv.get("timing_rule", "")
    hits = gochara.get("activations", [])[:2]
    hit_str = ""
    if hits:
        hit_str = f" Nakshatra triggers: {hits[0].get('natal_anchor')} via {hits[0].get('transit_planet')} in {hits[0].get('transit_nakshatra')}."
    return (
        f"Topic: {label}. Confidence {conf}/100. {mandate}.{hit_str}"
    )


def log_prediction(
    user_id: str,
    question: str,
    profile: dict,
    force: bool = False,
) -> Optional[int]:
    """
    Auto-log a prediction when user asks timing/outcome questions.
    Returns prediction id or None if not a prediction-worthy question.
    """
    if not user_id or not question:
        return None

    q = question.lower()
    timing_keywords = [
        "when", "will i", "predict", "forecast", "future", "partnership",
        "marriage", "relationship", "launch", "upgrade", "career", "job",
        "happen", "come", "get a", "timing", "muhurta", "auspicious",
    ]
    if not force and not any(k in q for k in timing_keywords):
        return None

    _init_predictions_table(user_id)
    topic = detect_topic(question)
    conv = score_convergence(profile, topic=topic, question=question)
    gochara = analyze_nakshatra_activations(profile)

    if not force and conv.get("confidence", 0) < 25 and gochara.get("major_count", 0) == 0:
        return None

    w_start, w_end = _estimate_window(
        conv.get("confidence", 0),
        conv.get("can_narrow_window", False),
    )
    pred_text = _build_prediction_text(topic, conv, gochara)

    dasha_snap = profile.get("dasha", {}).get("summary", "")
    now = datetime.now().isoformat()

    conn = _get_conn(user_id)
    conn.execute(
        """INSERT INTO predictions
           (user_id, question, topic, prediction_text, window_start, window_end,
            confidence, convergence_json, gochara_json, dasha_snapshot, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            user_id, question[:500], topic, pred_text, w_start, w_end,
            conv.get("confidence", 0),
            json.dumps(conv, default=str),
            json.dumps(gochara, default=str),
            dasha_snap, "pending", now,
        ),
    )
    conn.commit()
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"  [PREDICTION] Logged #{pid} topic={topic} conf={conv.get('confidence')}")
    return pid


def verify_prediction(
    user_id: str,
    prediction_id: int,
    happened: bool,
    outcome_date: str = "",
    outcome_note: str = "",
    emotion_score: int = 0,
) -> dict:
    """User confirms whether prediction happened — feeds accuracy + learning."""
    _init_predictions_table(user_id)
    conn = _get_conn(user_id)
    row = conn.execute(
        "SELECT topic, prediction_text, window_start, window_end FROM predictions WHERE id=?",
        (prediction_id,),
    ).fetchone()
    if not row:
        conn.close()
        return {"error": "Prediction not found"}

    topic, pred_text, w_start, w_end = row
    status = "hit" if happened else "miss"
    verified = datetime.now().isoformat()
    odate = outcome_date or datetime.now().strftime("%Y-%m-%d")

    conn.execute(
        """UPDATE predictions SET status=?, outcome=?, outcome_date=?,
           outcome_score=?, verified_at=? WHERE id=?""",
        (status, outcome_note[:1000], odate, emotion_score, verified, prediction_id),
    )
    conn.commit()
    conn.close()

    if happened:
        try:
            from core.memory import add_event
            add_event(
                date=odate,
                title=f"Prediction confirmed: {topic}",
                description=f"{pred_text}\n\nUser note: {outcome_note}",
                domain=topic if topic in ("career", "marriage", "wealth", "health") else "general",
                emotion_score=max(1, emotion_score) if emotion_score else 3,
                outcome="Prediction ledger HIT",
                user_id=user_id,
            )
        except Exception as e:
            print(f"  [PREDICTION] Event sync failed: {e}")

    return {"status": status, "prediction_id": prediction_id, "topic": topic}


def get_pending_predictions(user_id: str) -> list:
    _init_predictions_table(user_id)
    conn = _get_conn(user_id)
    rows = conn.execute(
        """SELECT id, question, topic, prediction_text, window_start, window_end,
                  confidence, status, created_at FROM predictions
           WHERE status='pending' ORDER BY created_at DESC LIMIT 20"""
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0], "question": r[1], "topic": r[2], "prediction_text": r[3],
            "window_start": r[4], "window_end": r[5], "confidence": r[6],
            "status": r[7], "created_at": r[8],
        }
        for r in rows
    ]


def get_all_predictions(user_id: str) -> list:
    _init_predictions_table(user_id)
    conn = _get_conn(user_id)
    rows = conn.execute(
        """SELECT id, topic, prediction_text, window_start, window_end, confidence,
                  status, outcome, outcome_date, created_at, verified_at
           FROM predictions ORDER BY created_at DESC LIMIT 100"""
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0], "topic": r[1], "prediction_text": r[2],
            "window_start": r[3], "window_end": r[4], "confidence": r[5],
            "status": r[6], "outcome": r[7], "outcome_date": r[8],
            "created_at": r[9], "verified_at": r[10],
        }
        for r in rows
    ]


def format_pending_for_agent(user_id: str) -> str:
    pending = get_pending_predictions(user_id)
    if not pending:
        return "No pending predictions awaiting user verification."
    lines = ["PENDING PREDICTIONS — Ask user if these happened:"]
    for p in pending[:5]:
        lines.append(
            f"  ID {p['id']}: [{p['topic']}] {p['prediction_text'][:120]} "
            f"(window {p['window_start']} to {p['window_end']})"
        )
    return "\n".join(lines)
