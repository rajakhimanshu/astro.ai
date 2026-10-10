"""
core/moon_chart.py — Chandra Lagna (Moon as ascendant) whole-sign houses.
"""

from __future__ import annotations

from typing import Any, Dict

from core.user_profile_engine import SIGN_IDX, SIGNS, SIGN_LORDS


def build_moon_chart(profile: dict) -> Dict[str, Any]:
    """Compute whole-sign houses from Moon sign + planet placements."""
    moon_sign = (
        profile.get("rashi", {}).get("sign")
        or profile.get("planets", {}).get("Moon", {}).get("sign")
    )
    if not moon_sign:
        return {}

    moon_idx = SIGN_IDX[moon_sign]
    lagna_sign = profile.get("lagna", {}).get("sign", "Aries")
    planets = profile.get("planets", {})

    houses: Dict[int, Dict[str, Any]] = {}
    for h in range(1, 13):
        sign_idx = (moon_idx + h - 1) % 12
        sign = SIGNS[sign_idx]
        occupants = [
            name for name, pd in planets.items()
            if name != "ASC" and pd.get("sign") == sign
        ]
        houses[h] = {
            "sign": sign,
            "lord": SIGN_LORDS[sign],
            "occupants": occupants,
        }

    planet_moon_houses = {}
    for name, pd in planets.items():
        if name == "ASC":
            continue
        planet_moon_houses[name] = (SIGN_IDX[pd["sign"]] - moon_idx) % 12 + 1

    return {
        "moon_lagna": moon_sign,
        "natal_lagna": lagna_sign,
        "houses": houses,
        "planet_houses": planet_moon_houses,
        "summary": _format_summary(moon_sign, lagna_sign, planet_moon_houses, planets),
    }


def _format_summary(moon_sign: str, lagna_sign: str, moon_houses: dict, planets: dict) -> str:
    lines = [f"Chandra Lagna: {moon_sign} | Natal Lagna: {lagna_sign}"]
    for pname in ("Moon", "Mercury", "Venus", "Saturn", "Jupiter", "Mars", "Sun"):
        if pname not in planets:
            continue
        natal_h = planets[pname]["house"]
        chandra_h = moon_houses.get(pname, "?")
        lines.append(f"  {pname}: Natal H{natal_h} | Moon-chart H{chandra_h} ({planets[pname]['sign']})")
    return "\n".join(lines)


def format_moon_chart_for_agent(moon_chart: dict) -> str:
    if not moon_chart:
        return "Moon chart not computed."
    return (
        "DUAL PERSPECTIVE — READ BOTH LAGNA AND MOON CHART:\n"
        + moon_chart.get("summary", "")
    )
