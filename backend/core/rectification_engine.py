"""
core/rectification_engine.py
────────────────────────────────────────────────────
Birth Time Rectification — event-driven, Lahiri sidereal, whole-sign.
Matches logged life events to Dasha lords + Jupiter/Saturn transits.
────────────────────────────────────────────────────
"""
from datetime import datetime, timedelta
from typing import Optional

from kerykeion import AstrologicalSubject

from core.astro_engine import (
    calculate_vimshottari_dasha,
    get_sky_on_date,
    get_house_from_asc,
    SIGNS,
)
from core.user_profile_engine import SIGN_IDX, SIGN_LORDS, _birth_path, _profile_path, _compute_profile_from_kerykeion
from core.memory import get_all_events
import json
import yaml
import os
from dotenv import load_dotenv

EVENT_HOUSE_MAP = {
    "career": [10, 6, 2, 11],
    "job": [10, 6, 2, 11],
    "work": [10, 6, 2, 11],
    "marriage": [7, 2, 11],
    "relationship": [7, 2, 11],
    "love": [7, 2, 11],
    "child": [5, 9],
    "children": [5, 9],
    "loss": [12, 8],
    "death": [12, 8],
    "travel": [9, 12],
    "property": [4],
    "education": [4, 5, 9],
    "accident": [8, 6],
    "health": [6, 8, 12],
    "finance": [2, 11, 8],
    "wealth": [2, 11],
    "spiritual": [9, 12],
    "general": [1, 10],
}

DOMAIN_ALIASES = {
    "career": "career",
    "job": "career",
    "work": "career",
    "relationship": "marriage",
    "love": "marriage",
    "finance": "finance",
    "wealth": "finance",
    "health": "health",
    "education": "education",
    "spiritual": "spiritual",
    "general": "general",
}


def _normalize_domain(domain: str) -> str:
    d = (domain or "general").lower().strip()
    return DOMAIN_ALIASES.get(d, d if d in EVENT_HOUSE_MAP else "general")


def _build_subject(birth_info: dict, hour: int, minute: int) -> AstrologicalSubject:
    load_dotenv()
    geonames_user = os.getenv("GEONAMES_USERNAME", "demo_user")
    return AstrologicalSubject(
        birth_info["name"],
        int(birth_info["year"]),
        int(birth_info["month"]),
        int(birth_info["day"]),
        int(hour),
        int(minute),
        birth_info["city"],
        birth_info["nation"],
        geonames_username=geonames_user,
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
        houses_system_identifier="W",
    )


def _planet_houses_from_subject(subject) -> tuple[dict, float, float]:
    m = subject.model()
    asc = float(m.ascendant.abs_pos)
    lagna_idx = int(asc // 30) % 12
    keys = {
        "Sun": m.sun, "Moon": m.moon, "Mars": m.mars, "Mercury": m.mercury,
        "Jupiter": m.jupiter, "Venus": m.venus, "Saturn": m.saturn,
        "Rahu": m.true_north_lunar_node, "Ketu": m.true_south_lunar_node,
    }
    houses = {}
    for name, p in keys.items():
        houses[name] = get_house_from_asc(float(p.abs_pos), asc)
    return houses, asc, float(m.moon.abs_pos)


def _score_candidate(
    birth_info: dict,
    test_dt: datetime,
    events: list,
) -> tuple[int, list[str]]:
    info = dict(birth_info)
    subject = _build_subject(info, test_dt.hour, test_dt.minute)
    planet_houses, asc, moon_lon = _planet_houses_from_subject(subject)
    birth_dt = test_dt
    score = 0
    reasons = []

    for ev in events:
        try:
            ev_dt = datetime.strptime(ev["date"][:10], "%Y-%m-%d")
        except Exception:
            continue

        domain = _normalize_domain(ev.get("domain", "general"))
        topic_houses = EVENT_HOUSE_MAP.get(domain, EVENT_HOUSE_MAP["general"])
        positive = int(ev.get("emotion_score", 0)) >= 0

        dasha = calculate_vimshottari_dasha(birth_dt, moon_lon, target_dt=ev_dt)
        if "error" in dasha:
            continue

        md = dasha["current_mahadasha"]["lord"]
        ad = dasha["current_antardasha"]["lord"]

        for lord, pts in [(md, 3), (ad, 2)]:
            lh = planet_houses.get(lord, 0)
            if lh in topic_houses:
                score += pts if positive else max(1, pts - 1)
                reasons.append(f"{ev['date']}: {lord} dasha lord in H{lh} for {domain}")

        try:
            sky = get_sky_on_date(
                ev_dt.year, ev_dt.month, ev_dt.day, 12, 0,
                birth_info["city"], birth_info["nation"],
            )
            sm = sky.model()
            jup_h = get_house_from_asc(float(sm.jupiter.abs_pos), asc)
            sat_h = get_house_from_asc(float(sm.saturn.abs_pos), asc)
            if positive and jup_h in topic_houses:
                score += 2
                reasons.append(f"{ev['date']}: Jupiter transit H{jup_h}")
            if not positive and sat_h in topic_houses:
                score += 2
                reasons.append(f"{ev['date']}: Saturn transit H{sat_h}")
        except Exception:
            pass

    return score, reasons


def rectify_birth_time(
    birth_info: dict,
    events: list,
    window_minutes: int = 30,
    step_seconds: int = 60,
) -> dict:
    """
    Scan birth time within ±window_minutes and return best-fit rectified time.
    Requires at least 3 logged events for meaningful results.
    """
    if len(events) < 3:
        return {
            "status": "insufficient_events",
            "message": "Log at least 3 dated life events (career, marriage, etc.) for rectification.",
            "event_count": len(events),
            "rectified_time": None,
            "confidence_score": 0,
            "confidence_label": "unverified",
        }

    approx = datetime(
        int(birth_info["year"]),
        int(birth_info["month"]),
        int(birth_info["day"]),
        int(birth_info["hour"]),
        int(birth_info["minute"]),
    )

    best_time = approx
    best_score = -1
    best_reasons = []
    scores = []

    for delta in range(-window_minutes * 60, window_minutes * 60 + 1, step_seconds):
        test_dt = approx + timedelta(seconds=delta)
        sc, reasons = _score_candidate(birth_info, test_dt, events)
        scores.append(sc)
        if sc > best_score:
            best_score = sc
            best_time = test_dt
            best_reasons = reasons[:8]

    max_possible = len(events) * 7
    ratio = best_score / max_possible if max_possible else 0

    if ratio >= 0.55:
        label = "high"
    elif ratio >= 0.35:
        label = "medium"
    elif ratio >= 0.2:
        label = "low"
    else:
        label = "unverified"

    shift_min = int((best_time - approx).total_seconds() // 60)

    return {
        "status": "success",
        "original_time": approx.strftime("%H:%M"),
        "rectified_time": best_time.strftime("%H:%M"),
        "shift_minutes": shift_min,
        "confidence_score": best_score,
        "confidence_ratio": round(ratio, 3),
        "confidence_label": label,
        "event_count": len(events),
        "top_matches": best_reasons,
        "birth_datetime": best_time.isoformat(),
    }


def rectify_user_profile(user_id: str, window_minutes: int = 30) -> dict:
    """Load user events, rectify birth time, update birth_data.yaml and recompute profile."""
    bpath = _birth_path(user_id)
    if not bpath.exists():
        return {"status": "error", "message": f"No birth data for user {user_id}"}

    with open(bpath, "r", encoding="utf-8") as f:
        birth_info = yaml.safe_load(f)

    events = get_all_events(user_id)
    result = rectify_birth_time(birth_info, events, window_minutes=window_minutes)

    if result["status"] != "success" or result.get("rectified_time") is None:
        return result

    if result["shift_minutes"] != 0 and result["confidence_label"] in ("high", "medium"):
        parts = result["rectified_time"].split(":")
        birth_info["hour"] = int(parts[0])
        birth_info["minute"] = int(parts[1])
        birth_info["rectified"] = True
        birth_info["rectification"] = {
            "original_time": result["original_time"],
            "shift_minutes": result["shift_minutes"],
            "confidence_label": result["confidence_label"],
            "confidence_score": result["confidence_score"],
            "rectified_at": datetime.now().isoformat(),
        }
        with open(bpath, "w", encoding="utf-8") as f:
            yaml.dump(birth_info, f, default_flow_style=False)

        profile = _compute_profile_from_kerykeion(birth_info)
        profile["meta"]["rectification"] = birth_info["rectification"]
        with open(_profile_path(user_id), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False, default=str)

        result["profile_updated"] = True
    else:
        result["profile_updated"] = False
        result["message"] = (
            "Birth time unchanged — either already optimal or confidence too low to adjust."
        )

    return result
