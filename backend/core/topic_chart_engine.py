"""
core/topic_chart_engine.py
────────────────────────────────────────────────────────────────────────
Topic-specific deep chart analysis from the computed profile.
Used by consultation_engine to replace generic dasha-only answers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.convergence_scorer import TOPIC_MAP, SIGN_IDX, SIGN_LORDS, SIGNS

VARGA_BY_TOPIC = {
    "career": ("10", "D10 Dasamsa"),
    "marriage": ("9", "D9 Navamsa"),
    "wealth": ("2", "D2 Hora"),
    "education": ("24", "D24 Chaturvimsamsa"),
    "health": ("6", "D6 Shashthamsa"),
    "children": ("7", "D7 Saptamsa"),
    "spiritual": ("20", "D20 Vimsamsa"),
    "forecast": ("9", "D9 Navamsa"),
    "general": ("9", "D9 Navamsa"),
}

CHARA_KARAKA_HINTS = {
    "career": ["Amatyakaraka", "Bhratrikaraka"],
    "marriage": ["Darakaraka", "Putrakaraka"],
    "wealth": ["Matrikaraka", "Putrakaraka"],
    "education": ["Putrakaraka", "Amatyakaraka"],
    "children": ["Putrakaraka"],
    "health": ["Atmakaraka", "Gnatikaraka"],
    "spiritual": ["Atmakaraka"],
}

TOPIC_YOGA_KEYWORDS = {
    "career": ("career", "raja", "dhana", "karma", "artha", "profession", "authority"),
    "marriage": ("marriage", "kalatra", "venus", "spouse", "partner", "love"),
    "wealth": ("dhana", "wealth", "lakshmi", "income", "artha"),
    "education": ("saraswati", "vidya", "education", "learning", "buddhi"),
    "health": ("health", "ayur", "longevity", "vitality"),
    "children": ("putra", "santa", "child"),
    "spiritual": ("moksha", "spiritual", "dharma", "tapas"),
}


def _hkey(h: int) -> str:
    return str(h)


def _lord_of_house(lagna_sign: str, house: int) -> str:
    sign = SIGNS[(SIGN_IDX[lagna_sign] + house - 1) % 12]
    return SIGN_LORDS[sign]


def _house_block(profile: dict, house: int, label: str = "") -> str:
    houses = profile.get("houses", {})
    hdata = houses.get(_hkey(house)) or houses.get(house) or {}
    if not hdata:
        return f"H{house}: data unavailable"
    sign = hdata.get("sign", "?")
    lord = hdata.get("lord", "?")
    occ = hdata.get("occupants") or []
    lord_h = hdata.get("lord_house", "?")
    htype = hdata.get("house_type", "")
    sav = profile.get("ashtakavarga", {}).get("sarvashtakavarga", {})
    sav_score = sav.get(house, sav.get(str(house), "?"))
    bb = profile.get("bhava_bala", {}).get(str(house)) or profile.get("bhava_bala", {}).get(house)
    bb_rupas = f"{bb['rupas']:.1f} rupas" if isinstance(bb, dict) else "?"
    occ_s = ", ".join(occ) if occ else "empty"
    prefix = f"{label} " if label else ""
    return (
        f"{prefix}H{house} {sign} ({htype or 'house'}) — lord {lord} in H{lord_h}, "
        f"occupants: {occ_s}; SAV {sav_score}; Bhava Bala {bb_rupas}"
    )


def _aspects_on_house(profile: dict, house: int) -> List[str]:
    lines = []
    for asp in profile.get("aspects", []):
        if asp.get("target_house") == house:
            lines.append(f"{asp['planet']} {asp['type']} drishti -> H{house}")
    return lines


def _planet_line(profile: dict, planet: str) -> str:
    pd = profile.get("planets", {}).get(planet, {})
    if not pd:
        return f"{planet}: not in chart"
    shad = profile.get("shadbala", {}).get(planet, 0)
    retro = " retrograde" if pd.get("retrograde") else ""
    conv = pd.get("convergence", {})
    conv_s = ""
    if conv.get("narrative"):
        conv_s = f" | {conv['narrative'][:80]}"
    return (
        f"{planet}: H{pd.get('house')} {pd.get('sign')} {pd.get('nakshatra', '')} "
        f"({pd.get('dignity', '?')}), Shadbala {shad:.1f}{retro}{conv_s}"
    )


def _varga_topic_lines(profile: dict, varga_key: str, varga_name: str, topic_houses: List[int]) -> List[str]:
    div = profile.get("divisional_charts", {}).get(varga_key, {})
    if not div:
        return [f"{varga_name}: not computed in profile"]
    lines = []
    asc = div.get("ASC", {})
    if asc:
        lines.append(f"{varga_name} Lagna: {asc.get('sign')} (H{asc.get('house')})")
    for h in topic_houses[:3]:
        # Find sign on this house in varga from D1 mapping — use planets in that house
        in_h = [p for p, pos in div.items() if p != "ASC" and pos.get("house") == h]
        if in_h:
            parts = [f"{p} in {div[p].get('sign')}" for p in in_h[:4]]
            lines.append(f"{varga_name} H{h}: {', '.join(parts)}")
    for p in ("Sun", "Saturn", "Mercury", "Venus", "Jupiter", "Moon", "Mars"):
        if p in div and div[p].get("house") in topic_houses:
            pos = div[p]
            lines.append(f"{varga_name} {p}: H{pos.get('house')} {pos.get('sign')}")
    return lines[:8]


def _moon_chart_houses(profile: dict, topic_houses: List[int]) -> List[str]:
    mc = profile.get("moon_chart", {})
    if not mc:
        return []
    lines = [f"Moon Lagna: {mc.get('moon_lagna')} (natal {mc.get('natal_lagna')})"]
    ph = mc.get("planet_houses", {})
    for h in topic_houses[:3]:
        occ = [p for p, mh in ph.items() if mh == h]
        if occ:
            lines.append(f"From Moon chart H{h}: {', '.join(occ)}")
    return lines[:5]


def _chara_karakas(profile: dict, topic: str) -> List[str]:
    hints = CHARA_KARAKA_HINTS.get(topic, ["Atmakaraka"])
    chara = profile.get("karakas", {}).get("chara", [])
    lines = []
    for k in chara:
        label = k.get("label", "")
        if any(h in label for h in hints):
            planet = k.get("planet", "?")
            lines.append(f"{label}: {planet} — {_planet_line(profile, planet)[:100]}")
    return lines[:4]


def _yogas_for_topic(profile: dict, topic: str) -> List[str]:
    keys = TOPIC_YOGA_KEYWORDS.get(topic, ())
    out = []
    for y in profile.get("yogas", []):
        name = (y.get("name") or "").lower()
        effect = y.get("effect") or ""
        if any(k in name or k in effect.lower() for k in keys):
            out.append(f"{y['name']}: {effect[:100]}")
    return out[:4]


def _dasha_layers(profile: dict, topic_cfg: dict) -> List[str]:
    dasha = profile.get("dasha", {})
    houses = topic_cfg["houses"]
    lagna = profile["lagna"]["sign"]
    lines = []
    md, ad, pd = dasha.get("current_md"), dasha.get("current_ad"), dasha.get("current_pd")
    for lord, label in [(md, "Mahadasha"), (ad, "Antardasha"), (pd, "Pratyantardasha")]:
        if not lord:
            continue
        pd_data = profile.get("planets", {}).get(lord, {})
        lh = pd_data.get("house", "?")
        rules = [h for h in houses if _lord_of_house(lagna, h) == lord]
        roles = []
        if lh in houses:
            roles.append(f"sits in topic H{lh}")
        if rules:
            roles.append(f"rules H{','.join(str(r) for r in rules)}")
        if lord in topic_cfg.get("karakas", []):
            roles.append("topic karaka")
        role_s = "; ".join(roles) if roles else "not directly on topic houses"
        lines.append(f"{label} {lord} (H{lh}): {role_s}")
    pd_end = dasha.get("pd_end_display") or dasha.get("pd_end", "")
    ad_end = dasha.get("ad_end_display") or dasha.get("ad_end", "")
    if pd_end:
        lines.append(f"PD {pd} active until {str(pd_end)[:10]}; AD {ad} until {str(ad_end)[:10]}")
    return lines


def _chara_dasha_line(profile: dict, topic_houses: List[int]) -> str:
    chara = profile.get("chara_dasha", {})
    cmd = chara.get("current_md", {})
    if not cmd or not cmd.get("sign"):
        return ""
    sign = cmd["sign"]
    lagna = profile["lagna"]["sign"]
    try:
        h_from_lagna = (SIGN_IDX[sign] - SIGN_IDX[lagna]) % 12 + 1
    except Exception:
        h_from_lagna = "?"
    hit = "TOPIC-ACTIVE" if h_from_lagna in topic_houses else "background"
    return f"Jaimini Chara MD: {sign} (H{h_from_lagna} from lagna) — {hit}"


def _timing_verdict(profile: dict, topic: str, conv: dict, question: str) -> str:
    """Timing from convergence + dasha-topic link — not a fixed Venus MD deferral."""
    conf = conv.get("confidence", 0)
    dasha = profile.get("dasha", {})
    ad_end = str(dasha.get("ad_end_display") or dasha.get("ad_end", ""))[:10]
    pd = dasha.get("current_pd", "?")
    pd_end = str(dasha.get("pd_end_display") or dasha.get("pd_end", ""))[:10]

    active = [s for s in conv.get("signals", []) if s.get("active")]
    dasha_hit = any(s.get("signal") == "vimshottari" and s.get("active") for s in active)
    transit_hit = any(s.get("signal") in ("slow_transits", "nakshatra_gochara") and s.get("active") for s in active)

    if conf >= 65 and dasha_hit and transit_hit:
        lean = "favourable window in the next 3–6 months"
    elif conf >= 45 and (dasha_hit or transit_hit):
        lean = "mixed but workable — conditions must align"
    elif conf >= 45:
        lean = "theme is building; timing is broad, not exact"
    else:
        lean = "weak convergence — speak themes only, no date promises"

    q = question.lower()
    if any(k in q for k in ("when", "will i", "timing", "future")):
        return (
            f"Timing read ({conf}/100): {lean}. "
            f"Current PD {pd} until {pd_end}; AD until {ad_end}. "
            f"{conv.get('timing_rule', '')}"
        )
    return f"Strength for this topic: {conf}/100 — {lean}."


PRIMARY_HOUSE = {
    "career": 10,
    "marriage": 7,
    "wealth": 2,
    "education": 9,
    "health": 1,
    "children": 5,
    "spiritual": 9,
    "forecast": 10,
    "general": 1,
}


def build_topic_chart_analysis(
    profile: dict,
    topic: str,
    conv: Optional[dict] = None,
    question: str = "",
) -> Dict[str, Any]:
    """Deep chart facts for one consultation topic."""
    conv = conv or {}
    cfg = TOPIC_MAP.get(topic, TOPIC_MAP["general"])
    houses = cfg["houses"]
    primary_h = PRIMARY_HOUSE.get(topic, houses[0] if houses else 1)
    lagna = profile.get("lagna", {}).get("sign", "?")
    varga_key, varga_name = VARGA_BY_TOPIC.get(topic, ("9", "D9 Navamsa"))

    house_lines = [_house_block(profile, h, "PRIMARY" if h == primary_h else "") for h in houses]
    aspect_lines = []
    for h in houses:
        aspect_lines.extend(_aspects_on_house(profile, h))
    aspect_lines = list(dict.fromkeys(aspect_lines))[:6]

    karaka_lines = [_planet_line(profile, k) for k in cfg.get("karakas", [])]
    karaka_lines.extend(_chara_karakas(profile, topic))

    analysis = {
        "topic": topic,
        "label": cfg["label"],
        "primary_house": primary_h,
        "lagna": lagna,
        "house_lines": house_lines,
        "aspect_lines": aspect_lines,
        "karaka_lines": karaka_lines[:8],
        "varga_lines": _varga_topic_lines(profile, varga_key, varga_name, houses),
        "moon_lines": _moon_chart_houses(profile, houses),
        "dasha_lines": _dasha_layers(profile, cfg),
        "chara_line": _chara_dasha_line(profile, houses),
        "yoga_lines": _yogas_for_topic(profile, topic),
        "convergence_lines": [
            f"{s['signal']} (+{s['weight']}): {s['detail'][:140]}"
            for s in conv.get("signals", [])
            if s.get("active")
        ][:6],
        "timing_verdict": _timing_verdict(profile, topic, conv, question),
        "confidence": conv.get("confidence", 0),
    }
    return analysis


def format_topic_chart_analysis(analysis: dict) -> str:
    lines = [
        f"═══ TOPIC CHART ANALYSIS — {analysis.get('label', 'General')} "
        f"(confidence {analysis.get('confidence', 0)}/100) ═══",
        f"Lagna: {analysis.get('lagna')} | Primary house: H{analysis.get('primary_house')}",
        "",
        "D1 HOUSES (topic-relevant):",
    ]
    for h in analysis.get("house_lines", []):
        lines.append(f"  • {h}")

    if analysis.get("aspect_lines"):
        lines.append("")
        lines.append("DRISHTI ON TOPIC HOUSES:")
        for a in analysis["aspect_lines"]:
            lines.append(f"  • {a}")

    if analysis.get("karaka_lines"):
        lines.append("")
        lines.append("KARAKAS & KEY PLANETS:")
        for k in analysis["karaka_lines"]:
            lines.append(f"  • {k}")

    if analysis.get("varga_lines"):
        lines.append("")
        lines.append("DIVISIONAL CHART:")
        for v in analysis["varga_lines"]:
            lines.append(f"  • {v}")

    if analysis.get("moon_lines"):
        lines.append("")
        lines.append("MOON (CHANDRA) CHART:")
        for m in analysis["moon_lines"]:
            lines.append(f"  • {m}")

    if analysis.get("yoga_lines"):
        lines.append("")
        lines.append("RELEVANT YOGAS:")
        for y in analysis["yoga_lines"]:
            lines.append(f"  • {y}")

    lines.append("")
    lines.append("VIMSHOTTARI LAYERS:")
    for d in analysis.get("dasha_lines", []):
        lines.append(f"  • {d}")
    if analysis.get("chara_line"):
        lines.append(f"  • {analysis['chara_line']}")

    if analysis.get("convergence_lines"):
        lines.append("")
        lines.append("CONVERGENCE SIGNALS (agreeing):")
        for c in analysis["convergence_lines"]:
            lines.append(f"  • {c}")

    lines.append("")
    lines.append(f"TIMING: {analysis.get('timing_verdict', '')}")
    return "\n".join(lines)


def build_topic_direct_answer(
    profile: dict,
    topic: str,
    question: str,
    conv: dict,
    lived: Optional[dict] = None,
) -> str:
    """
    Chart-grounded DIRECT ANSWER — uses real houses, varga, aspects, dasha layers.
    """
    lived = lived or {}
    analysis = build_topic_chart_analysis(profile, topic, conv, question)
    conf = analysis.get("confidence", 0)
    q = question.lower()

    # Pull the most important facts for plain-English lead
    house_facts = analysis.get("house_lines", [])
    primary_fact = next(
        (h for h in house_facts if h.startswith("PRIMARY")),
        next((h for h in house_facts if f"H{analysis.get('primary_house')}" in h), house_facts[0] if house_facts else ""),
    )
    dasha_facts = analysis.get("dasha_lines", [])
    varga_facts = analysis.get("varga_lines", [])
    aspect_facts = analysis.get("aspect_lines", [])
    timing = analysis.get("timing_verdict", "")

    parts = ["DIRECT ANSWER:"]

    if topic == "career" or any(k in q for k in ("job", "career", "business", "intern", "internship", "startup", "platform")):
        parts.append(
            "Read career from the 10th house and its lord, not from a single Mahadasha label."
        )
        if primary_fact:
            parts.append(primary_fact.replace("PRIMARY ", ""))
        if aspect_facts:
            parts.append(f"Support: {aspect_facts[0]}.")
        if varga_facts:
            parts.append(varga_facts[0] + (f" {varga_facts[1]}" if len(varga_facts) > 1 else ""))
        for d in dasha_facts[:2]:
            parts.append(d + ".")
        if lived.get("profession"):
            parts.append(f"Your context: {str(lived['profession'])[:180]}.")
        parts.append(timing)

    elif topic == "marriage" or any(k in q for k in ("girl", "love", "propose", "rejected", "relationship", "marriage")):
        parts.append("Read love/marriage from 5th and 7th houses, Venus, Jupiter, and D9 — not generic deferrals.")
        for h in house_facts[:2]:
            parts.append(h.replace("PRIMARY ", ""))
        if lived.get("relationships"):
            parts.append(f"Life context: {str(lived['relationships'])[:200]}.")
        if any(k in q for k in ("reject", "no feeling")):
            parts.append("A clear rejection in real life is a completed 5th-house story, not a hidden 7th-house promise.")
        for d in dasha_facts[:2]:
            parts.append(d + ".")
        parts.append(timing)

    elif topic == "education" or any(k in q for k in ("exam", "backlog", "sem", "pass", "college", "paper")):
        parts.append("Read education from 4th/5th/9th houses, Mercury, Jupiter, and D24.")
        for h in house_facts[:2]:
            parts.append(h.replace("PRIMARY ", ""))
        for d in dasha_facts[:2]:
            parts.append(d + ".")
        lean = "lean toward clearing" if conf >= 50 else "mixed — effort still decisive"
        parts.append(f"Exam outcome lean: {lean} ({conf}/100). {timing}")

    else:
        parts.append(f"Answer using the chart facts below for {analysis.get('label')}.")
        if primary_fact:
            parts.append(primary_fact.replace("PRIMARY ", ""))
        for d in dasha_facts[:2]:
            parts.append(d + ".")
        parts.append(timing)

    return " ".join(parts)
