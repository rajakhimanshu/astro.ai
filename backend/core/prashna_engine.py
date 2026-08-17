"""
core/prashna_engine.py
────────────────────────────────────────────────────
Prashna Engine (Horary Astrology) — Lahiri sidereal, whole-sign.
────────────────────────────────────────────────────
"""
import swisseph as swe
from datetime import datetime

from core.astro_engine import get_house_from_asc
from core.user_profile_engine import SIGN_LORDS, SIGNS

swe.set_sid_mode(swe.SIDM_LAHIRI)

PLANET_MAP = {
    swe.SUN: "Sun", swe.MOON: "Moon", swe.MARS: "Mars",
    swe.MERCURY: "Mercury", swe.JUPITER: "Jupiter",
    swe.VENUS: "Venus", swe.SATURN: "Saturn",
    swe.TRUE_NODE: "Rahu",
}

QUESTION_HOUSE = {
    "finance": [2, 11], "wealth": [2, 11],
    "career": [10, 6], "marriage": [7], "health": [1, 6],
    "travel": [3, 9, 12], "legal": [7, 6], "property": [4],
    "general": [1],
}


def datetime_to_jd(dt):
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, hour)


def _get_dignity(planet: str, sign_idx: int) -> str:
    exalt = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
    deb = {k: (v + 6) % 12 for k, v in exalt.items()}
    name = planet.capitalize()
    if sign_idx == deb.get(name, -1):
        return "debilitated"
    if sign_idx == exalt.get(name, -1):
        return "exalted"
    return "neutral"


def cast_prashna_chart(question_dt, lat, lon, question_type):
    jd = datetime_to_jd(question_dt)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    prashna_planets = {}
    for planet_id, name in PLANET_MAP.items():
        pos = swe.calc_ut(jd, planet_id, flags)[0][0]
        prashna_planets[name] = pos
        if name == "Rahu":
            prashna_planets["Ketu"] = (pos + 180) % 360

    prashna_asc = swe.houses_ex(jd, lat, lon, b'W', flags)[1][0]
    asc_sign_idx = int(prashna_asc // 30) % 12
    target_houses = QUESTION_HOUSE.get(question_type, QUESTION_HOUSE["general"])
    results = {}

    for h in target_houses:
        sign = SIGNS[(asc_sign_idx + h - 1) % 12]
        lord_name = SIGN_LORDS[sign]
        lord_pos = prashna_planets.get(lord_name, 0)
        lord_house = get_house_from_asc(lord_pos, prashna_asc)
        lord_dignity = _get_dignity(lord_name, int(lord_pos // 30) % 12)
        results[h] = {
            "lord": lord_name,
            "lord_house": lord_house,
            "lord_dignity": lord_dignity,
            "favorable": lord_house in [1, 2, 3, 5, 6, 9, 10, 11],
        }

    moon_pos = prashna_planets["Moon"]
    moon_house = get_house_from_asc(moon_pos, prashna_asc)
    moon_dignity = _get_dignity("Moon", int(moon_pos // 30) % 12)
    results["moon"] = {
        "house": moon_house,
        "dignity": moon_dignity,
        "favorable": moon_house in [1, 2, 3, 5, 6, 9, 10, 11],
    }
    results["asc_sign"] = SIGNS[asc_sign_idx]
    return results


def run_prashna_analysis(question_type: str, lat: float, lon: float, question_dt=None) -> dict:
    dt = question_dt or datetime.now()
    return cast_prashna_chart(dt, lat, lon, question_type)


def format_prashna_report(results: dict, question_type: str) -> str:
    if not results:
        return "PRASHNA: Chart unavailable."
    lines = [
        f"PRASHNA CHART ({question_type.upper()}) — Asc {results.get('asc_sign', '?')}",
        "",
    ]
    moon = results.get("moon", {})
    lines.append(
        f"Moon H{moon.get('house')} ({moon.get('dignity')}) — "
        f"{'favourable' if moon.get('favorable') else 'caution'}"
    )
    for h, data in results.items():
        if h in ("moon", "asc_sign"):
            continue
        lines.append(
            f"H{h} lord {data['lord']}: H{data['lord_house']}, {data['lord_dignity']} — "
            f"{'GO' if data['favorable'] else 'WAIT'}"
        )
    return "\n".join(lines)

