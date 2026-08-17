"""
core/kakshya_engine.py
────────────────────────────────────────────────────────────────────────
Ashtakavarga Kakshya (3°45' subdivisions) — fine transit delivery windows.
If BAV bindus are 0 for a house, transit planet struggles to deliver there.
────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime
from core.astro_engine import get_sky_on_date, get_house_from_asc
from core.ashtakavarga import calculate_ashtakavarga
from core.astro_engine import get_natal_chart_from_profile

KAKSHYA_SIZE = 30.0 / 8.0  # 3°45'


def _kakshya_index(deg_in_sign: float) -> int:
    return min(7, int(deg_in_sign / KAKSHYA_SIZE))


def analyze_transit_kakshyas(profile: dict, target_dt=None) -> dict:
    birth = profile["meta"]["birth"]
    dt = target_dt or datetime.now()
    lagna_abs = profile["lagna"]["abs_pos"]
    lagna_idx = profile["lagna"]["sign_idx"]

    try:
        from kerykeion import AstrologicalSubject
        import os
        from dotenv import load_dotenv
        load_dotenv()
        subject = AstrologicalSubject(
            profile["meta"]["name"],
            birth["year"], birth["month"], birth["day"],
            birth["hour"], birth["minute"],
            birth["city"], birth["nation"],
            geonames_username=os.getenv("GEONAMES_USERNAME", "demo_user"),
            zodiac_type="Sidereal", sidereal_mode="LAHIRI", houses_system_identifier="W",
        )
        av = calculate_ashtakavarga(subject)
    except Exception:
        av = profile.get("ashtakavarga", {})
        av = {
            "sarvashtakavarga_lagna": av.get("sarvashtakavarga", {}),
            "bhinnashtakavarga_by_house": {},
        }

    sav_lagna = av.get("sarvashtakavarga_lagna") or {}
    bav = av.get("bhinnashtakavarga_by_house", {})

    sky = get_sky_on_date(
        dt.year, dt.month, dt.day, dt.hour, dt.minute,
        birth["city"], birth["nation"],
    )
    m = sky.model()
    planets = {
        "Jupiter": m.jupiter, "Saturn": m.saturn,
        "Rahu": m.true_north_lunar_node, "Ketu": m.true_south_lunar_node,
        "Mars": m.mars,
    }

    results = []
    for name, p in planets.items():
        abs_pos = float(p.abs_pos)
        deg = abs_pos % 30
        h = get_house_from_asc(abs_pos, lagna_abs)
        k_idx = _kakshya_index(deg)
        sav_h = int(sav_lagna.get(h, sav_lagna.get(str(h), 25)))
        pkey = name.lower()
        bav_h = 0
        if pkey in bav:
            bav_h = int(bav[pkey].get(h, bav[pkey].get(str(h), 0)))

        if bav_h == 0:
            verdict = "BLOCKED — zero BAV bindus; transit unlikely to deliver results"
            favorable = False
        elif sav_h < 25:
            verdict = "WEAK SAV — house cannot support full results"
            favorable = False
        elif bav_h >= 4 and sav_h >= 28:
            verdict = "EXCELLENT — strong BAV + SAV; transit delivers fully"
            favorable = True
        elif bav_h >= 3:
            verdict = "GOOD — transit can manifest with effort"
            favorable = True
        else:
            verdict = "MIXED — partial results only"
            favorable = True

        results.append({
            "planet": name,
            "house": h,
            "kakshya": k_idx + 1,
            "degree_in_sign": round(deg, 2),
            "sav": sav_h,
            "bav": bav_h,
            "favorable": favorable,
            "verdict": verdict,
        })

    return {"as_of": dt.isoformat(), "transits": results}


def format_kakshya_report(profile: dict) -> str:
    data = analyze_transit_kakshyas(profile)
    lines = [
        "=" * 70,
        "KAKSHYA / ASHTAKAVARGA TRANSIT DELIVERY (3°45' precision layer)",
        f"As of: {data['as_of'][:16]}",
        "=" * 70,
    ]
    for t in data["transits"]:
        flag = "GO" if t["favorable"] else "BLOCKED"
        lines.append(
            f"  [{flag}] {t['planet']} H{t['house']} Kakshya {t['kakshya']} "
            f"(deg {t['degree_in_sign']}°) | SAV={t['sav']} BAV={t['bav']} | {t['verdict']}"
        )
    lines.append("")
    lines.append("Rule: Slow planet through 0-BAV house = event delayed or denied.")
    lines.append("=" * 70)
    return "\n".join(lines)
