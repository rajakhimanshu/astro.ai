"""
core/pattern_engine.py — Per-user historical pattern matching.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from core.astro_engine import get_planet_snapshot_dict, calculate_vimshottari_dasha
from core.memory import _get_user_db_path


def _get_current_signature_from_profile(profile: dict) -> dict:
    birth = profile["meta"]["birth"]
    birth_dt = datetime(
        birth["year"], birth["month"], birth["day"],
        birth["hour"], birth["minute"],
    )
    moon_lon = profile["planets"]["Moon"]["abs_pos"]
    dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon)

    return {
        "mahadasha": dasha_info.get("current_mahadasha", {}).get("lord"),
        "antardasha": dasha_info.get("current_antardasha", {}).get("lord"),
        "saturn_house": profile["planets"].get("Saturn", {}).get("house"),
        "jupiter_house": profile["planets"].get("Jupiter", {}).get("house"),
        "rahu_house": profile["planets"].get("Rahu", {}).get("house"),
        "ketu_house": profile["planets"].get("Ketu", {}).get("house"),
        "saturn_sign": profile["planets"].get("Saturn", {}).get("sign"),
        "jupiter_sign": profile["planets"].get("Jupiter", {}).get("sign"),
    }


def get_event_signature(planet_snapshot_json):
    snap = json.loads(planet_snapshot_json)
    return {
        "mahadasha": snap.get("mahadasha"),
        "antardasha": snap.get("antardasha"),
        "saturn_house": snap.get("saturn", {}).get("house"),
        "jupiter_house": snap.get("jupiter", {}).get("house"),
        "rahu_house": snap.get("rahu", {}).get("house"),
        "ketu_house": snap.get("ketu", {}).get("house"),
        "saturn_sign": snap.get("saturn", {}).get("sign"),
        "jupiter_sign": snap.get("jupiter", {}).get("sign"),
    }


def calculate_similarity_score(sig1, sig2):
    score = 0
    matches = []

    if sig1["mahadasha"] == sig2["mahadasha"]:
        score += 25
        matches.append("Same Mahadasha")

    if sig1["antardasha"] == sig2["antardasha"]:
        score += 20
        matches.append("Same Antardasha")

    s1, s2 = sig1["saturn_house"], sig2["saturn_house"]
    if s1 and s2:
        diff = abs(s1 - s2)
        if diff == 0:
            score += 20
            matches.append("Saturn in same house")
        elif diff == 1 or diff == 11:
            score += 10
            matches.append("Saturn in adjacent house")

    j1, j2 = sig1["jupiter_house"], sig2["jupiter_house"]
    if j1 and j2:
        diff = abs(j1 - j2)
        if diff == 0:
            score += 20
            matches.append("Jupiter in same house")
        elif diff == 1 or diff == 11:
            score += 10
            matches.append("Jupiter in adjacent house")

    r1, r2 = sig1["rahu_house"], sig2["rahu_house"]
    if r1 and r2:
        diff = abs(r1 - r2)
        if diff == 0:
            score += 15
            matches.append("Rahu/Ketu axis identical")
        elif diff == 1 or diff == 11:
            score += 7
            matches.append("Rahu/Ketu axis similar")

    return score, matches


def find_similar_past_periods(current_dasha=None, natal_planets=None, top_n=3, user_id: str = None, profile: dict = None):
    if profile:
        current_sig = _get_current_signature_from_profile(profile)
    elif current_dasha and natal_planets:
        current_sig = {
            "mahadasha": current_dasha.get("current_mahadasha", {}).get("lord"),
            "antardasha": current_dasha.get("current_antardasha", {}).get("lord"),
            "saturn_house": natal_planets.get("Saturn", {}).get("house"),
            "jupiter_house": natal_planets.get("Jupiter", {}).get("house"),
            "rahu_house": natal_planets.get("Rahu", {}).get("house"),
            "ketu_house": natal_planets.get("Ketu", {}).get("house"),
        }
    else:
        return []

    db_path = _get_user_db_path(user_id)
    if not Path(db_path).exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    events = conn.execute(
        "SELECT * FROM events WHERE planet_snapshot IS NOT NULL ORDER BY date DESC"
    ).fetchall()
    conn.close()

    scored_events = []
    for ev in events:
        try:
            ev_sig = get_event_signature(ev["planet_snapshot"])
            score, matches = calculate_similarity_score(current_sig, ev_sig)
            scored_events.append({
                "id": ev["id"],
                "date": ev["date"],
                "title": ev["title"],
                "description": ev["description"],
                "outcome": ev["outcome"],
                "emotion_score": ev["emotion_score"],
                "score": score,
                "matches": matches,
            })
        except Exception as e:
            print(f"  [PATTERN] Event {ev['id']} error: {e}")

    scored_events.sort(key=lambda x: x["score"], reverse=True)
    return scored_events[:top_n]


def format_pattern_report(similar_events):
    if not similar_events:
        return "PATTERN ANALYSIS: No similar past periods found. Log life events with dates to enable this."

    lines = [f"PATTERN ANALYSIS: {len(similar_events)} similar past period(s) found.\n"]

    for i, ev in enumerate(similar_events):
        signal = "LOW"
        if ev["score"] >= 70:
            signal = "HIGH"
        elif ev["score"] >= 40:
            signal = "MEDIUM"

        lines.append(f"MATCH {i + 1} (Score: {ev['score']}/100) — {ev['date']}")
        lines.append(f"Event: {ev['title']}")
        lines.append(f"Details: {ev['description']}")
        lines.append(f"Matching factors: {', '.join(ev['matches'])}")
        lines.append(f"Past outcome: {ev['outcome']}")
        lines.append(f"Past emotion: {ev['emotion_score']}")
        lines.append(f"Pattern signal: {signal} SIMILARITY\n")

    return "\n".join(lines)
