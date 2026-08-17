"""
core/nakshatra_gochara_engine.py
────────────────────────────────────────────────────────────────────────
Nakshatra-level Gochara (transit) engine — the layer master astrologers use
when they say things like "Ketu in Magha activates your lagna + Sun in Magha".

This is deterministic classical logic, NOT LLM improvisation.
────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime, timedelta
from typing import Optional

from core.astro_engine import (
    get_sky_on_date,
    get_nakshatra_and_pada,
    get_house_from_asc,
    SIGNS,
)
from core.user_profile_engine import SIGN_LORDS, SIGN_IDX, NAKSHATRA_LORDS

SLOW_TRANSITORS = ["Saturn", "Jupiter", "Rahu", "Ketu", "Mars"]
MEDIUM_TRANSITORS = ["Sun", "Venus", "Mercury"]

# Classical life-domain keywords per anchor (for material predictions)
ANCHOR_DOMAINS = {
    "Lagna": "identity, physical environment, how you show up in the world",
    "Sun": "status, authority, recognition, father, throne/seat of power",
    "Moon": "mind, comfort, mother, emotional home",
    "Lagna Lord": "overall life direction and vitality of the chart",
    "7th Lord": "partnerships, marriage, business contracts, public deals",
    "Venus": "relationships, luxury, comfort items, aesthetics, pleasure",
    "Jupiter": "growth, mentors, wisdom, expansion, fortune",
    "Mercury": "business launches, communication, tech, trade",
    "Saturn": "structure, furniture, long-term assets, discipline",
    "Mars": "energy, competition, new ventures, physical upgrades",
}

# Per-nakshatra activation themes (BPHS / tradition condensed)
NAKSHATRA_THEMES = {
    "Ashwini": "speed, healing, new starts, vehicles, quick upgrades",
    "Bharani": "transformation, restraint, birth-death cycles, intense change",
    "Krittika": "cutting away, purification, sharp decisions, fire",
    "Rohini": "growth, beauty, material increase, comfort, acquisition",
    "Mrigashira": "searching, curiosity, travel, restless change",
    "Ardra": "storm, emotional purge, technical disruption",
    "Punarvasu": "return, renewal, second chances, home restoration",
    "Pushya": "nourishment, support, auspicious beginnings, mentors",
    "Ashlesha": "intensity, binding, hidden deals, psychological depth",
    "Magha": "throne, seat, lineage, authority, ancestors, royal upgrade, chair/setup/status symbols",
    "Purva Phalguni": "pleasure, romance, creativity, celebration, relationship spark",
    "Uttara Phalguni": "contracts, marriage, patronage, lasting partnership",
    "Hasta": "skill, hands-on work, craft, launching practical projects",
    "Chitra": "design, building, architecture, visible creation",
    "Swati": "independence, trade, wind of change, business independence",
    "Vishakha": "goal pursuit, partnership for ambition, determined growth",
    "Anuradha": "devotion, friendship, group success, foreign ties",
    "Jyeshtha": "seniority, protection, rivalry, earning respect",
    "Mula": "uprooting, core truth, radical reset",
    "Purva Ashadha": "victory, conviction, public declaration",
    "Uttara Ashadha": "lasting victory, leadership cemented, permanent gains",
    "Shravana": "listening, learning, reputation, media, advice",
    "Dhanishtha": "wealth rhythm, assets, music, shared resources",
    "Dhanishta": "wealth rhythm, assets, music, shared resources",
    "Shatabhisha": "secrets, research, isolation, unconventional healing",
    "Purva Bhadrapada": "ideology, sacrifice, intense spiritual or financial pivot",
    "Uttara Bhadrapada": "depth, stability, karmic completion, mature union",
    "Revati": "completion, journey's end, safe travel, nurturing finish",
}

TRANSIT_PLANET_EFFECT = {
    "Ketu": "detachment then sudden realignment; past karma ripens; upgrades through release of old",
    "Rahu": "obsessive push, foreign or unconventional openings, amplification",
    "Jupiter": "expansion, blessing, partnership/growth window opens",
    "Saturn": "delay then permanent result; furniture, structure, responsibility",
    "Mars": "action, purchase, conflict, physical upgrade pushed through",
    "Sun": "visibility spike, authority, recognition",
    "Venus": "relationship, comfort purchase, aesthetic upgrade",
    "Mercury": "launch, contract, communication deal",
    "Moon": "short emotional window (days), not months",
}


def _nak_idx(abs_pos: float) -> int:
    return int(abs_pos / (360 / 27)) % 27


def _same_nakshatra(abs1: float, abs2: float) -> bool:
    return _nak_idx(abs1) == _nak_idx(abs2)


def _pada(abs_pos: float) -> int:
    nak, pada = get_nakshatra_and_pada(abs_pos)
    return pada


def _get_transit_positions(city: str, nation: str, dt: datetime) -> dict:
    sky = get_sky_on_date(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, city, nation,
    )
    m = sky.model()
    keys = {
        "Sun": m.sun, "Moon": m.moon, "Mars": m.mars, "Mercury": m.mercury,
        "Jupiter": m.jupiter, "Venus": m.venus, "Saturn": m.saturn,
        "Rahu": m.true_north_lunar_node, "Ketu": m.true_south_lunar_node,
    }
    out = {}
    for name, p in keys.items():
        nak, pada = get_nakshatra_and_pada(float(p.abs_pos))
        out[name] = {
            "abs_pos": float(p.abs_pos),
            "sign": p.sign,
            "nakshatra": nak,
            "pada": pada,
            "nakshatra_lord": NAKSHATRA_LORDS.get(nak, "?"),
            "retrograde": bool(getattr(p, "retrograde", False)),
        }
    return out


def _natal_anchors(profile: dict) -> list[dict]:
    lagna = profile["lagna"]
    planets = profile["planets"]
    lagna_sign = lagna["sign"]
    h7_lord = SIGN_LORDS[SIGNS[(SIGN_IDX[lagna_sign] + 6) % 12]]
    lagna_lord = lagna.get("lord") or SIGN_LORDS.get(lagna_sign, "?")

    anchors = [
        {
            "label": "Lagna",
            "nakshatra": lagna.get("nakshatra"),
            "pada": lagna.get("pada"),
            "abs_pos": lagna.get("abs_pos"),
            "house": 1,
            "planet_key": "ASC",
        },
    ]
    for pname in ["Sun", "Moon", "Venus", "Jupiter", "Mercury", "Mars", "Saturn"]:
        if pname in planets and planets[pname].get("nakshatra"):
            anchors.append({
                "label": pname,
                "nakshatra": planets[pname]["nakshatra"],
                "pada": planets[pname].get("pada"),
                "abs_pos": planets[pname].get("abs_pos"),
                "house": planets[pname].get("house"),
                "planet_key": pname,
            })
    if lagna_lord in planets:
        anchors.append({
            "label": "Lagna Lord",
            "nakshatra": planets[lagna_lord].get("nakshatra"),
            "pada": planets[lagna_lord].get("pada"),
            "abs_pos": planets[lagna_lord].get("abs_pos"),
            "house": planets[lagna_lord].get("house"),
            "planet_key": lagna_lord,
        })
    if h7_lord in planets:
        anchors.append({
            "label": "7th Lord",
            "nakshatra": planets[h7_lord].get("nakshatra"),
            "pada": planets[h7_lord].get("pada"),
            "abs_pos": planets[h7_lord].get("abs_pos"),
            "house": planets[h7_lord].get("house"),
            "planet_key": h7_lord,
        })
    return [a for a in anchors if a.get("nakshatra")]


def analyze_nakshatra_activations(profile: dict, target_dt: Optional[datetime] = None) -> dict:
    """
    Core gochara-nakshatra analysis: finds when transiting planets
    hit natal nakshatra anchors (the Magha/Ketu/lagna pattern).
    """
    birth = profile["meta"]["birth"]
    dt = target_dt or datetime.now()
    lagna_abs = profile["lagna"]["abs_pos"]
    transits = _get_transit_positions(birth["city"], birth["nation"], dt)
    anchors = _natal_anchors(profile)
    activations = []

    for t_name in SLOW_TRANSITORS + MEDIUM_TRANSITORS:
        if t_name not in transits:
            continue
        t = transits[t_name]
        t_house = get_house_from_asc(t["abs_pos"], lagna_abs)

        for anchor in anchors:
            if not anchor.get("abs_pos"):
                continue
            same_nak = t["nakshatra"] == anchor["nakshatra"]
            same_pada = same_nak and t["pada"] == anchor.get("pada")
            degree_hit = False
            if anchor["abs_pos"]:
                diff = abs(t["abs_pos"] - anchor["abs_pos"]) % 360
                if diff > 180:
                    diff = 360 - diff
                degree_hit = diff <= 3.5

            if not (same_nak or degree_hit):
                continue

            nak_theme = NAKSHATRA_THEMES.get(anchor["nakshatra"], "karmic activation")
            domain = ANCHOR_DOMAINS.get(anchor["label"], "life themes")
            t_effect = TRANSIT_PLANET_EFFECT.get(t_name, "activation")

            # Material prediction mapping (classical house + nakshatra)
            material = []
            if anchor["nakshatra"] == "Magha" or "Magha" in (t["nakshatra"], anchor["nakshatra"]):
                material.append("status symbol upgrade (seat/chair/throne), ancestral pride, visible setup improvement")
            if anchor["label"] in ("7th Lord", "Venus") or t_house == 7:
                material.append("partnership, relationship, or business alliance window")
            if t_house in (4, 10) or anchor["label"] == "Saturn":
                material.append("home/office setup, furniture, structural upgrade")
            if t_house in (10, 11) or anchor["label"] in ("Sun", "Mercury", "Jupiter"):
                material.append("career launch, public recognition, project go-live")
            if t_house == 5:
                material.append("romance, creativity, speculative venture")

            strength = "MAJOR"
            if same_pada or degree_hit:
                strength = "EXACT"
            elif t_name in ("Moon", "Mercury", "Venus", "Sun"):
                strength = "SHORT"

            activations.append({
                "strength": strength,
                "transit_planet": t_name,
                "transit_nakshatra": t["nakshatra"],
                "transit_pada": t["pada"],
                "transit_house": t_house,
                "transit_retrograde": t["retrograde"],
                "natal_anchor": anchor["label"],
                "natal_nakshatra": anchor["nakshatra"],
                "natal_pada": anchor.get("pada"),
                "natal_house": anchor.get("house"),
                "nakshatra_lord": NAKSHATRA_LORDS.get(anchor["nakshatra"], "?"),
                "match_type": "EXACT_DEGREE" if degree_hit else ("SAME_PADA" if same_pada else "SAME_NAKSHATRA"),
                "domain": domain,
                "nakshatra_theme": nak_theme,
                "transit_effect": t_effect,
                "material_predictions": material,
                "narrative": (
                    f"{t_name} transiting {t['nakshatra']} (Pada {t['pada']}, H{t_house}) "
                    f"activates natal {anchor['label']} in {anchor['nakshatra']} — "
                    f"{t_effect}. Themes: {nak_theme}. Domains: {domain}."
                ),
            })

    # Nakshatra-lord resonance (e.g. Ketu transiting Ketu-ruled Magha while natal Sun in Magha)
    for act in list(activations):
        t_lord = NAKSHATRA_LORDS.get(act["transit_nakshatra"], "")
        if t_lord and act["transit_planet"] == t_lord:
            act["nakshatra_lord_resonance"] = True
            act["narrative"] += (
                f" RESONANCE: {act['transit_planet']} is also the nakshatra lord of "
                f"{act['transit_nakshatra']} — double activation (classic Jyotish trigger)."
            )

    activations.sort(key=lambda x: (0 if x["strength"] == "EXACT" else 1, x["transit_planet"] in SLOW_TRANSITORS))
    return {
        "as_of": dt.isoformat(),
        "activations": activations,
        "active_count": len(activations),
        "major_count": sum(1 for a in activations if a["strength"] in ("MAJOR", "EXACT")),
    }


def scan_upcoming_windows(
    profile: dict,
    days_ahead: int = 120,
    step_days: int = 3,
) -> list[dict]:
    """Scan forward for nakshatra activation peaks (for launch/partnership timing)."""
    birth = profile["meta"]["birth"]
    start = datetime.now()
    windows = []

    for i in range(0, days_ahead, step_days):
        dt = start + timedelta(days=i)
        result = analyze_nakshatra_activations(profile, dt)
        if result["major_count"] >= 1:
            windows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "major_activations": result["major_count"],
                "highlights": [a["narrative"][:120] for a in result["activations"][:3]],
            })
    return windows[:15]


def format_gochara_report(profile: dict, question: str = "") -> str:
    """Human + LLM readable nakshatra gochara report."""
    analysis = analyze_nakshatra_activations(profile)
    q = question.lower()
    lines = [
        "=" * 70,
        "NAKSHATRA GOCHARA ENGINE — Master-Astrologer Transit Layer",
        f"As of: {datetime.now().strftime('%d %B %Y %H:%M')}",
        "=" * 70,
        "",
        "This is the layer used when astrologers say e.g. 'Ketu in Magha hits your",
        "lagna nakshatra and Sun in Magha — expect status/setup upgrade or lineage karma.'",
        "",
    ]

    if not analysis["activations"]:
        lines.append("No major nakshatra-to-natal activations at this exact moment.")
        lines.append("Slow planets may still affect houses — see house transit section.")
    else:
        lines.append(f"ACTIVE NAKSHATRA HITS: {analysis['active_count']} "
                     f"({analysis['major_count']} major/exact)")
        lines.append("")
        for i, act in enumerate(analysis["activations"][:8], 1):
            lines.append(f"[{i}] {act['strength']} — {act['match_type']}")
            lines.append(f"    {act['narrative']}")
            if act.get("nakshatra_lord_resonance"):
                lines.append("    *** Nakshatra-lord resonance (double trigger) ***")
            if act["material_predictions"]:
                lines.append(f"    Likely manifestations: {'; '.join(act['material_predictions'])}")
            lines.append("")

    # Question-specific guidance
    if any(k in q for k in ["launch", "project", "business", "startup"]):
        lines.append("--- LAUNCH / PROJECT GUIDANCE ---")
        launch_hits = [a for a in analysis["activations"]
                       if a["transit_house"] in (10, 11, 3) or a["natal_anchor"] in ("Mercury", "Jupiter", "Sun")]
        if launch_hits:
            for a in launch_hits[:3]:
                lines.append(f"  GO: {a['transit_planet']} activates {a['natal_anchor']} — favorable for launch energy")
        else:
            lines.append("  WAIT: No strong nakshatra launch signature now — check dasha + muhurta.")
        upcoming = scan_upcoming_windows(profile, 90, 5)
        if upcoming:
            lines.append("  Upcoming nakshatra windows:")
            for w in upcoming[:5]:
                lines.append(f"    {w['date']}: {w['major_activations']} major hit(s)")

    if any(k in q for k in ["partner", "relationship", "marriage", "love"]):
        lines.append("--- PARTNERSHIP / RELATIONSHIP GUIDANCE ---")
        rel_hits = [a for a in analysis["activations"]
                    if a["natal_anchor"] in ("7th Lord", "Venus") or a["transit_house"] == 7
                    or "partnership" in " ".join(a.get("material_predictions", []))]
        if rel_hits:
            for a in rel_hits[:3]:
                lines.append(f"  ACTIVE: {a['narrative'][:150]}")
        else:
            lines.append("  Theme may build later — no exact 7H/Venus nakshatra hit today.")

    lines.append("")
    lines.append("ACCURACY NOTE: Nakshatra hits show WHEN energy peaks. Outcome still needs")
    lines.append("dasha agreement + house promise. Never treat as 100% certainty.")
    lines.append("=" * 70)
    return "\n".join(lines)
