"""
core/convergence_scorer.py
────────────────────────────────────────────────────────────────────────
Master Jyotish Convergence Engine — gates timing predictions before LLM.

Requires ≥3 agreeing signals before allowing narrow timing windows.
Mimics how a senior astrologer cross-checks D1/D9, Vimshottari, Jaimini,
slow transits, and Ashtakavarga before committing to a date range.
────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime
from typing import Optional

from core.astro_engine import (
    calculate_vimshottari_dasha,
    get_sky_on_date,
    get_house_from_asc,
    SIGNS,
)
from core.nakshatra_gochara_engine import analyze_nakshatra_activations
from core.user_profile_engine import SIGN_IDX, SIGN_LORDS

TOPIC_MAP = {
    "career": {
        "label": "Career & Profession",
        "houses": [1, 2, 6, 10, 11],
        "karakas": ["Sun", "Saturn", "Mercury"],
        "varga_key": "10",
    },
    "wealth": {
        "label": "Wealth & Finance",
        "houses": [2, 5, 9, 11],
        "karakas": ["Jupiter", "Venus"],
        "varga_key": "2",
    },
    "marriage": {
        "label": "Marriage & Partnership",
        "houses": [2, 5, 7, 11],
        "karakas": ["Venus", "Jupiter"],
        "varga_key": "9",
    },
    "health": {
        "label": "Health & Vitality",
        "houses": [1, 6, 8, 12],
        "karakas": ["Sun", "Mars", "Saturn"],
        "varga_key": "6",
    },
    "education": {
        "label": "Education & Wisdom",
        "houses": [4, 5, 9],
        "karakas": ["Mercury", "Jupiter"],
        "varga_key": "9",
    },
    "children": {
        "label": "Children & Creativity",
        "houses": [5, 9],
        "karakas": ["Jupiter"],
        "varga_key": "7",
    },
    "spiritual": {
        "label": "Spiritual Path",
        "houses": [5, 9, 12],
        "karakas": ["Jupiter", "Ketu"],
        "varga_key": "9",
    },
    "forecast": {
        "label": "General Forecast",
        "houses": [1, 5, 9, 10, 11],
        "karakas": ["Sun", "Jupiter"],
        "varga_key": "9",
    },
    "general": {
        "label": "General Life",
        "houses": [1, 5, 9],
        "karakas": ["Sun", "Moon"],
        "varga_key": "9",
    },
}

KARAKA_HOUSES = {
    "career": ["career", "job", "work", "business", "promotion", "profession"],
    "wealth": ["money", "wealth", "finance", "income", "investment"],
    "marriage": ["marriage", "love", "spouse", "relationship", "partner"],
    "health": ["health", "illness", "disease", "body"],
    "education": ["education", "study", "exam", "degree"],
    "children": ["child", "children", "pregnancy", "baby"],
    "spiritual": ["spiritual", "meditation", "moksha", "guru"],
    "forecast": ["when will", "next year", "future", "forecast", "predict", "upcoming"],
}


def detect_topic(question: str) -> str:
    q = question.lower()
    for topic, keywords in KARAKA_HOUSES.items():
        if any(k in q for k in keywords):
            return topic
    return "general"


def _lord_of_house(lagna_sign: str, house: int) -> str:
    sign = SIGNS[(SIGN_IDX[lagna_sign] + house - 1) % 12]
    return SIGN_LORDS[sign]


def _planet_in_topic_houses(planet: str, houses: list, profile: dict) -> bool:
    pdata = profile.get("planets", {}).get(planet, {})
    return pdata.get("house") in houses


def _shadbala_score(profile: dict, planet: str) -> float:
    return float(profile.get("shadbala", {}).get(planet, 0))


def _sav_for_house(profile: dict, house: int) -> int:
    sav = profile.get("ashtakavarga", {}).get("sarvashtakavarga", {})
    return int(sav.get(house, sav.get(str(house), 25)))


def _natal_promise(profile: dict, topic_cfg: dict) -> dict:
    lagna = profile["lagna"]["sign"]
    houses = topic_cfg["houses"]
    hits = []

    for h in houses:
        lord = _lord_of_house(lagna, h)
        lord_h = profile.get("planets", {}).get(lord, {}).get("house")
        lord_str = _shadbala_score(profile, lord)
        if lord_h in {1, 4, 5, 7, 9, 10, 11} or lord_str >= 6:
            hits.append(f"{h}H lord {lord} supported (H{lord_h}, Shadbala {lord_str:.1f})")

    for karaka in topic_cfg["karakas"]:
        k_h = profile.get("planets", {}).get(karaka, {}).get("house")
        k_str = _shadbala_score(profile, karaka)
        if k_h in houses or k_str >= 6:
            hits.append(f"Karaka {karaka} active (H{k_h}, Shadbala {k_str:.1f})")

    varga = topic_cfg.get("varga_key")
    div = profile.get("divisional_charts", {}).get(varga, {})
    for karaka in topic_cfg["karakas"]:
        if karaka in div and div[karaka].get("house") in {1, 4, 5, 7, 9, 10, 11}:
            hits.append(f"D{varga} {karaka} in favourable house H{div[karaka]['house']}")

    strong = len(hits) >= 2
    return {
        "signal": "natal_promise",
        "active": strong,
        "weight": 25 if strong else 8,
        "detail": "; ".join(hits) if hits else "Natal promise for this topic is weak or mixed.",
    }


def _dasha_signal(profile: dict, topic_cfg: dict, target_dt: Optional[datetime] = None) -> dict:
    birth = profile["meta"]["birth"]
    birth_dt = datetime(
        birth["year"], birth["month"], birth["day"],
        birth["hour"], birth["minute"],
    )
    moon_lon = profile["planets"]["Moon"]["abs_pos"]
    dasha = calculate_vimshottari_dasha(birth_dt, moon_lon, target_dt=target_dt or datetime.now())
    if "error" in dasha:
        return {"signal": "vimshottari", "active": False, "weight": 0, "detail": "Dasha unavailable"}

    houses = topic_cfg["houses"]
    md = dasha["current_mahadasha"]["lord"]
    ad = dasha["current_antardasha"]["lord"]
    pd = dasha["current_pratyantardasha"]["lord"]
    hits = []

    for lord, label in [(md, "MD"), (ad, "AD"), (pd, "PD")]:
        if _planet_in_topic_houses(lord, houses, profile):
            hits.append(f"{label} {lord} occupies topic house")
        elif _lord_of_house(profile["lagna"]["sign"], houses[0]) == lord:
            hits.append(f"{label} {lord} rules primary topic house")

    active = len(hits) >= 1
    return {
        "signal": "vimshottari",
        "active": active,
        "weight": 20 if len(hits) >= 2 else (12 if active else 0),
        "detail": f"{' | '.join(hits)} | Period: {dasha.get('summary', '')}",
        "md": md,
        "ad": ad,
        "pd": pd,
    }


def _jaimini_signal(profile: dict, topic_cfg: dict) -> dict:
    chara = profile.get("chara_dasha", {})
    cmd = chara.get("current_md", {})
    if not cmd:
        return {"signal": "jaimini_chara", "active": False, "weight": 0, "detail": "Chara dasha not computed"}

    sign = cmd.get("sign", "")
    if not sign:
        return {"signal": "jaimini_chara", "active": False, "weight": 0, "detail": "Chara dasha sign missing"}

    lagna_idx = profile["lagna"]["sign_idx"]
    sign_idx = SIGN_IDX.get(sign, -1)
    house_from_lagna = (sign_idx - lagna_idx + 12) % 12 + 1 if sign_idx >= 0 else 0
    active = house_from_lagna in topic_cfg["houses"]
    return {
        "signal": "jaimini_chara",
        "active": active,
        "weight": 15 if active else 0,
        "detail": f"Chara MD sign {sign} falls in natal H{house_from_lagna} "
                  f"({'aligned' if active else 'not aligned'} with topic)",
    }


def _transit_signal(profile: dict, topic_cfg: dict, target_dt: Optional[datetime] = None) -> dict:
    dt = target_dt or datetime.now()
    birth = profile["meta"]["birth"]
    try:
        sky = get_sky_on_date(
            dt.year, dt.month, dt.day, dt.hour, dt.minute,
            birth["city"], birth["nation"],
        )
    except Exception as e:
        return {"signal": "slow_transits", "active": False, "weight": 0, "detail": str(e)}

    m = sky.model()
    asc_pos = profile["lagna"]["abs_pos"]
    houses = topic_cfg["houses"]
    hits = []

    for label, body in [("Jupiter", m.jupiter), ("Saturn", m.saturn)]:
        th = get_house_from_asc(float(body.abs_pos), asc_pos)
        if th in houses:
            hits.append(f"{label} transiting H{th}")

    rahu_h = get_house_from_asc(float(m.true_north_lunar_node.abs_pos), asc_pos)
    if rahu_h in houses or ((rahu_h + 5) % 12 + 1) in houses:
        hits.append(f"Rahu/Ketu axis touches topic houses (Rahu H{rahu_h})")

    active = len(hits) >= 1
    return {
        "signal": "slow_transits",
        "active": active,
        "weight": 18 if len(hits) >= 2 else (10 if active else 0),
        "detail": " | ".join(hits) if hits else "Slow planets not strongly activating topic houses now.",
    }


def _ashtakavarga_signal(profile: dict, topic_cfg: dict) -> dict:
    houses = topic_cfg["houses"]
    scores = [_sav_for_house(profile, h) for h in houses[:3]]
    avg = sum(scores) / len(scores) if scores else 25
    strong_houses = [h for h in houses if _sav_for_house(profile, h) >= 28]
    active = avg >= 27 or len(strong_houses) >= 1
    return {
        "signal": "ashtakavarga",
        "active": active,
        "weight": 12 if avg >= 30 else (8 if active else 0),
        "detail": f"Avg SAV {avg:.0f} for topic houses; strong: {strong_houses or 'none'}",
    }


def _gochara_signal(profile: dict, topic_cfg: dict) -> dict:
    try:
        analysis = analyze_nakshatra_activations(profile)
        hits = analysis.get("activations", [])
        topic_houses = set(topic_cfg["houses"])
        relevant = [
            h for h in hits
            if h["transit_house"] in topic_houses
            or h["natal_anchor"] in ("7th Lord", "Venus", "Jupiter", "Sun", "Lagna Lord", "Mercury")
            or h["strength"] == "EXACT"
        ]
        active = len(relevant) >= 1 or analysis.get("major_count", 0) >= 1
        detail_parts = [h["narrative"][:100] for h in relevant[:3]]
        if not detail_parts and hits:
            detail_parts = [hits[0]["narrative"][:100]]
        return {
            "signal": "nakshatra_gochara",
            "active": active,
            "weight": 20 if any(h.get("nakshatra_lord_resonance") for h in hits) else (15 if active else 0),
            "detail": " | ".join(detail_parts) if detail_parts else "No nakshatra-to-natal activation now",
        }
    except Exception as e:
        return {"signal": "nakshatra_gochara", "active": False, "weight": 0, "detail": str(e)}


def _yoga_signal(profile: dict, topic: str) -> dict:
    yogas = profile.get("yogas", [])
    keywords = {
        "career": ["raja", "dhana", "gajakesari", "dasamsa"],
        "wealth": ["dhana", "lakshmi", "gajakesari"],
        "marriage": ["kalathra", "venus", "7"],
        "health": ["viparita", "neecha"],
    }.get(topic, ["raja", "dhana", "gajakesari"])

    matched = [y["name"] for y in yogas if any(k in y["name"].lower() for k in keywords)]
    active = len(matched) > 0
    return {
        "signal": "yogas",
        "active": active,
        "weight": 10 if active else 0,
        "detail": f"Relevant yogas: {', '.join(matched)}" if matched else "No topic-specific yoga flagged.",
    }


def score_convergence(
    profile: dict,
    topic: str = "general",
    question: str = "",
    target_dt: Optional[datetime] = None,
) -> dict:
    """Returns full convergence analysis for a topic."""
    if topic == "general" and question:
        topic = detect_topic(question)

    cfg = TOPIC_MAP.get(topic, TOPIC_MAP["general"])
    signals = [
        _natal_promise(profile, cfg),
        _dasha_signal(profile, cfg, target_dt),
        _jaimini_signal(profile, cfg),
        _gochara_signal(profile, cfg),
        _transit_signal(profile, cfg, target_dt),
        _ashtakavarga_signal(profile, cfg),
        _yoga_signal(profile, topic),
    ]

    active_count = sum(1 for s in signals if s["active"])
    total_weight = sum(s["weight"] for s in signals if s["active"])
    confidence = min(100, total_weight)

    rect = profile.get("meta", {}).get("rectification", {})
    birth_conf = rect.get("confidence_label", "unverified")
    if birth_conf == "low":
        confidence = max(0, confidence - 20)

    can_time = active_count >= 3 and confidence >= 45
    can_narrow = active_count >= 4 and confidence >= 65

    if can_narrow:
        timing_rule = "WINDOW_ALLOWED: Give a quarter-to-quarter window only (3–6 months), never a single date."
    elif can_time:
        timing_rule = "BROAD_WINDOW_ONLY: Give a 6–18 month thematic period; state what must align further."
    else:
        timing_rule = "NO_PRECISE_TIMING: Discuss themes and preparation only. Do not give dates."

    return {
        "topic": topic,
        "label": cfg["label"],
        "confidence": confidence,
        "active_signals": active_count,
        "total_signals": len(signals),
        "can_predict_timing": can_time,
        "can_narrow_window": can_narrow,
        "timing_rule": timing_rule,
        "birth_time_confidence": birth_conf,
        "signals": signals,
    }


def format_convergence_report(result: dict) -> str:
    lines = [
        "═══════════════════════════════════════════════════════════════",
        f"CONVERGENCE ANALYSIS — {result['label'].upper()}",
        "═══════════════════════════════════════════════════════════════",
        f"Confidence Score: {result['confidence']}/100",
        f"Active Signals: {result['active_signals']}/{result['total_signals']}",
        f"Birth Time Confidence: {result['birth_time_confidence']}",
        f"TIMING MANDATE: {result['timing_rule']}",
        "",
    ]
    for s in result["signals"]:
        flag = "YES" if s["active"] else "NO"
        lines.append(f"  [{flag}] {s['signal'].upper()} (+{s['weight']}): {s['detail']}")
    lines.append("")
    if not result["can_predict_timing"]:
        lines.append(
            "VERDICT: Insufficient convergence for timing prediction. "
            "A master astrologer would discuss themes, not dates."
        )
    elif result["can_narrow_window"]:
        lines.append(
            "VERDICT: Strong convergence — narrow seasonal window permissible "
            "if Dasha + Jupiter/Saturn agree."
        )
    else:
        lines.append(
            "VERDICT: Moderate convergence — broad period only, with conditions named."
        )
    return "\n".join(lines)
