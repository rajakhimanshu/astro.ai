"""
core/gemstone_engine.py
Full-chart gemstone suitability — Lagna + Moon chart, drishti, dasha, shadbala.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.user_profile_engine import PLANET_REMEDIES, SIGN_LORDS, SIGN_IDX, SIGNS

GEMSTONE_ALIASES = {
    "blue sapphire": "Saturn",
    "neelam": "Saturn",
    "nilam": "Saturn",
    "emerald": "Mercury",
    "panna": "Mercury",
    "yellow sapphire": "Jupiter",
    "pukhraj": "Jupiter",
    "ruby": "Sun",
    "manik": "Sun",
    "pearl": "Moon",
    "moti": "Moon",
    "red coral": "Mars",
    "moonga": "Mars",
    "diamond": "Venus",
    "white sapphire": "Venus",
    "hessonite": "Rahu",
    "gomed": "Rahu",
    "cat's eye": "Ketu",
    "cats eye": "Ketu",
    "lehsuniya": "Ketu",
}

# Functional benefics by lagna (simplified Parashari)
FUNCTIONAL_BENEFICS = {
    "Aries": {"Jupiter", "Sun", "Mars"},
    "Taurus": {"Saturn", "Mercury", "Venus"},
    "Gemini": {"Venus", "Saturn", "Mercury"},
    "Cancer": {"Mars", "Jupiter", "Moon"},
    "Leo": {"Mars", "Sun", "Jupiter"},
    "Virgo": {"Venus", "Mercury", "Saturn"},
    "Libra": {"Saturn", "Mercury", "Venus"},
    "Scorpio": {"Moon", "Sun", "Jupiter"},
    "Sagittarius": {"Sun", "Mars", "Jupiter"},
    "Capricorn": {"Venus", "Mercury", "Saturn"},
    "Aquarius": {"Venus", "Saturn", "Mercury"},
    "Pisces": {"Mars", "Moon", "Jupiter"},
}

FUNCTIONAL_MALEFICS = {
    "Aries": {"Mercury", "Venus", "Saturn"},
    "Taurus": {"Mars", "Jupiter", "Moon"},
    "Gemini": {"Mars", "Jupiter", "Moon"},
    "Cancer": {"Venus", "Mercury", "Saturn"},
    "Leo": {"Moon", "Mercury", "Venus"},
    "Virgo": {"Mars", "Jupiter", "Moon"},
    "Libra": {"Sun", "Jupiter", "Mars"},
    "Scorpio": {"Mercury", "Venus", "Saturn"},
    "Sagittarius": {"Mercury", "Venus", "Saturn"},
    "Capricorn": {"Mars", "Jupiter", "Moon"},
    "Aquarius": {"Sun", "Mars", "Jupiter"},
    "Pisces": {"Mercury", "Venus", "Saturn"},
}


def detect_gemstone_query(question: str) -> Optional[str]:
    q = question.lower()
    if not any(k in q for k in ("gem", "stone", "sapphire", "emerald", "ruby", "pearl", "coral", "neelam", "panna", "pukhraj", "gomed", "lehsuniya", "wear")):
        return None
    for alias, planet in GEMSTONE_ALIASES.items():
        if alias in q:
            return planet
    return None


def _house_lords_from_lagna(lagna_sign: str) -> Dict[int, str]:
    li = SIGN_IDX[lagna_sign]
    return {h: SIGN_LORDS[SIGNS[(li + h - 1) % 12]] for h in range(1, 13)}


def _planet_house_from_lagna(planet_sign: str, lagna_sign: str) -> int:
    return (SIGN_IDX[planet_sign] - SIGN_IDX[lagna_sign]) % 12 + 1


def _aspects_on_planet(profile: dict, target: str) -> List[str]:
    hits = []
    planets = profile.get("planets", {})
    if target not in planets:
        return hits
    th = planets[target]["house"]
    for asp in profile.get("aspects", []):
        if asp.get("target_house") == th and asp.get("planet") != target:
            hits.append(f"{asp['planet']} {asp['type']} drishti on H{th}")
    return hits[:4]


def analyze_gemstone(profile: dict, planet: str) -> Dict[str, Any]:
    """Full-chart suitability for a planet's gemstone."""
    lagna = profile.get("lagna", {}).get("sign", "Aries")
    moon_sign = profile.get("rashi", {}).get("sign") or profile.get("planets", {}).get("Moon", {}).get("sign", "Aries")
    planets = profile.get("planets", {})
    dasha = profile.get("dasha", {})
    shadbala = profile.get("shadbala_full") or profile.get("shadbala", {})

    if planet not in planets:
        return {"planet": planet, "verdict": "unknown", "summary": "Planet not in chart."}

    pd = planets[planet]
    lagna_h = pd["house"]
    moon_h = _planet_house_from_lagna(pd["sign"], moon_sign)
    rupas = shadbala.get(planet, {})
    if isinstance(rupas, dict):
        rupas = rupas.get("rupas", 5.5)
    elif not isinstance(rupas, (int, float)):
        rupas = 5.5

    lagna_benefic = planet in FUNCTIONAL_BENEFICS.get(lagna, set())
    lagna_malefic = planet in FUNCTIONAL_MALEFICS.get(lagna, set())
    moon_benefic = planet in FUNCTIONAL_BENEFICS.get(moon_sign, set())
    moon_malefic = planet in FUNCTIONAL_MALEFICS.get(moon_sign, set())

    lords_lagna = _house_lords_from_lagna(lagna)
    lords_moon = _house_lords_from_lagna(moon_sign)
    rules_lagna = [h for h, lord in lords_lagna.items() if lord == planet]
    rules_moon = [h for h, lord in lords_moon.items() if lord == planet]

    is_lagna_lord = lords_lagna.get(1) == planet
    is_moon_lord = lords_moon.get(1) == planet
    in_dusthana = lagna_h in (6, 8, 12) or moon_h in (6, 8, 12)
    aspects = _aspects_on_planet(profile, planet)
    remedy = PLANET_REMEDIES.get(planet, {})
    gem_name = remedy.get("gemstone", planet)

    score = 50
    reasons: List[str] = []
    cautions: List[str] = []

    if lagna_benefic:
        score += 15
        reasons.append(f"Functional benefic for {lagna} Lagna")
    if moon_benefic:
        score += 10
        reasons.append(f"Functional benefic for {moon_sign} Moon chart")
    if lagna_malefic:
        score -= 20
        cautions.append(f"Functional malefic for {lagna} Lagna — wear only after trial")
    if moon_malefic:
        score -= 10
        cautions.append(f"Functional malefic for {moon_sign} Moon chart")
    if is_lagna_lord:
        score += 10
        reasons.append(f"Lagna lord ({lagna}) — primary life-force planet")
    if is_moon_lord:
        score += 8
        reasons.append(f"Moon-chart ascendant lord ({moon_sign})")
    if in_dusthana:
        score -= 15
        cautions.append(f"Planet in dusthana (Lagna H{lagna_h}, Moon H{moon_h})")
    if rupas < 5.0:
        score += 5
        reasons.append(f"Weak Shadbala ({rupas:.1f} rupas) — remedy may help")
    elif rupas > 7.0:
        score += 5
        reasons.append(f"Strong Shadbala ({rupas:.1f} rupas)")
    if planet in (dasha.get("current_md"), dasha.get("current_ad"), dasha.get("current_pd")):
        score += 5
        reasons.append(f"Active in current dasha ({dasha.get('summary', '')[:60]})")
    if planet in ("Saturn", "Rahu", "Ketu", "Mars"):
        cautions.append("High-intensity gem — 3-day trial on body before committing")
    if aspects:
        reasons.append(f"Drishti: {'; '.join(aspects)}")

    score = max(0, min(100, score))
    if score >= 70:
        verdict = "suitable_with_trial"
        summary = f"{gem_name} is generally suitable — trial first, then wear on correct day."
    elif score >= 45:
        verdict = "conditional"
        summary = f"{gem_name} is conditional — only after reading full chart + trial period."
    else:
        verdict = "not_recommended"
        summary = f"{gem_name} is not recommended without expert supervision."

    return {
        "planet": planet,
        "gemstone": gem_name,
        "verdict": verdict,
        "score": score,
        "summary": summary,
        "reasons": reasons,
        "cautions": cautions,
        "placement": {
            "lagna_chart": f"H{lagna_h} {pd['sign']} (from {lagna} Lagna)",
            "moon_chart": f"H{moon_h} (from {moon_sign} Moon Lagna)",
            "rules_houses_lagna": rules_lagna,
            "rules_houses_moon": rules_moon,
        },
        "shadbala_rupas": round(float(rupas), 1),
        "mantra": remedy.get("mantra", ""),
        "charity": remedy.get("charity", ""),
    }


def format_gemstone_report(analysis: dict) -> str:
    if not analysis:
        return ""
    lines = [
        f"GEMSTONE ANALYSIS — {analysis.get('gemstone', '?')} ({analysis.get('planet', '?')})",
        f"Verdict: {analysis.get('verdict', '?').upper()} ({analysis.get('score', 0)}/100)",
        f"{analysis.get('summary', '')}",
        f"Lagna chart: {analysis.get('placement', {}).get('lagna_chart', '?')}",
        f"Moon chart: {analysis.get('placement', {}).get('moon_chart', '?')}",
    ]
    for r in analysis.get("reasons", []):
        lines.append(f"  + {r}")
    for c in analysis.get("cautions", []):
        lines.append(f"  ! {c}")
    return "\n".join(lines)
