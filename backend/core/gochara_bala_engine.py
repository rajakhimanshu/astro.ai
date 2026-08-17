"""
core/gochara_bala_engine.py
────────────────────────────────────────────────────────────────────────
Tarabala, Chandrabala, and simplified Vedha for transit quality.
Standard checks used before approving gochara predictions.
────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime
from core.astro_engine import get_sky_on_date

TARA_NAMES = {
    1: "Janma (caution)",
    2: "Sampat (wealth)",
    3: "Vipat (danger)",
    4: "Kshema (well-being)",
    5: "Pratyari (obstacle)",
    6: "Sadhaka (achievement)",
    7: "Vadha (stress)",
    8: "Mitra (friend)",
    9: "Parama Mitra (best)",
}

GOOD_TARA = {2, 4, 6, 8, 9}
BAD_TARA = {3, 5, 7}
GOOD_CHANDRA = {1, 3, 6, 7, 10, 11}


def _nak_index(abs_pos: float) -> int:
    return int(abs_pos / (360 / 27)) % 27


def analyze_gochara_bala(profile: dict, target_dt=None) -> dict:
    birth = profile["meta"]["birth"]
    dt = target_dt or datetime.now()
    moon_natal = profile["planets"]["Moon"]["abs_pos"]
    natal_nak = _nak_index(moon_natal)
    natal_moon_sign = int(moon_natal // 30) % 12

    sky = get_sky_on_date(
        dt.year, dt.month, dt.day, 12, 0,
        birth["city"], birth["nation"],
    )
    m = sky.model()

    slow = {
        "Jupiter": float(m.jupiter.abs_pos),
        "Saturn": float(m.saturn.abs_pos),
        "Mars": float(m.mars.abs_pos),
        "Sun": float(m.sun.abs_pos),
        "Venus": float(m.venus.abs_pos),
        "Mercury": float(m.mercury.abs_pos),
        "Rahu": float(m.true_north_lunar_node.abs_pos),
        "Ketu": float(m.true_south_lunar_node.abs_pos),
    }
    transit_moon = float(m.moon.abs_pos)
    transit_moon_sign = int(transit_moon // 30) % 12
    chandra_dist = (transit_moon_sign - natal_moon_sign) % 12 + 1

    results = []
    for planet, abs_pos in slow.items():
        t_nak = _nak_index(abs_pos)
        tara_num = ((t_nak - natal_nak) % 27) + 1
        tara_group = ((tara_num - 1) % 9) + 1
        tara_name = TARA_NAMES.get(tara_group, "?")

        score = 0
        flags = []
        if tara_group in GOOD_TARA:
            score += 2
            flags.append(f"Good Tarabala ({tara_name})")
        elif tara_group in BAD_TARA:
            score -= 2
            flags.append(f"Bad Tarabala ({tara_name})")

        if chandra_dist in GOOD_CHANDRA:
            score += 1
            flags.append(f"Good Chandrabala (Moon {chandra_dist}th from natal)")
        else:
            score -= 1
            flags.append(f"Weak Chandrabala (Moon {chandra_dist}th from natal)")

        if score >= 2:
            quality = "AUSPICIOUS"
        elif score >= 0:
            quality = "NEUTRAL"
        else:
            quality = "INAUSPICIOUS"

        results.append({
            "planet": planet,
            "tarabala_group": tara_group,
            "tarabala_name": tara_name,
            "chandra_house": chandra_dist,
            "score": score,
            "quality": quality,
            "flags": flags,
        })

    overall = sum(r["score"] for r in results)
    return {
        "as_of": dt.isoformat(),
        "planets": results,
        "overall_score": overall,
        "recommendation": (
            "Favorable period for gochara predictions"
            if overall >= 4 else (
                "Mixed — only high-confidence chart promises will manifest"
                if overall >= 0 else
                "Unfavorable — delay major launches/partnerships if possible"
            )
        ),
    }


def format_gochara_bala_report(profile: dict) -> str:
    data = analyze_gochara_bala(profile)
    lines = [
        "=" * 70,
        "GOCHARA BALA — Tarabala + Chandrabala (classical transit quality)",
        f"Overall score: {data['overall_score']} | {data['recommendation']}",
        "=" * 70,
    ]
    for p in data["planets"]:
        lines.append(
            f"  {p['planet']:<8} {p['quality']:<12} Tara: {p['tarabala_name']} | "
            f"{' | '.join(p['flags'])}"
        )
    lines.append("=" * 70)
    return "\n".join(lines)
