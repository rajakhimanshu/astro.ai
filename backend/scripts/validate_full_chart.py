"""
Full chart validation — John Doe
Compares live engine + stored profile vs AstroSage ground truth (kundali_profile + output.txt + ground_truth.json)
"""
import sys
import os
import re
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_profile_engine import load_user_profile
from core.astro_engine import get_natal_chart_from_profile, get_nakshatra_and_pada, get_house_from_asc
from core.ashtakavarga import calculate_ashtakavarga
from core.shadbala_engine import calculate_shadbala_rupas, calculate_bhava_bala
from core.kundali_profile import KUNDALI_PROFILE

USER_ID = "john_doe"
DEG_TOL = 0.75  # minutes-level tolerance vs PDF rounding

SIGN_MAP = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
    "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
    "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces",
}


def parse_dms(s: str) -> float:
    """Parse '26°20'04"' or '5°00'13"' to decimal degrees in sign."""
    if isinstance(s, (int, float)):
        return float(s)
    m = re.match(r"(\d+)[°\s]+(\d+)['\s]+(\d+)", str(s))
    if m:
        d, mi, se = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return d + mi / 60 + se / 3600
    m2 = re.match(r"([\d.]+)", str(s))
    return float(m2.group(1)) if m2 else 0.0


# Ground truth from VedicReport / AstroSage (kundali_profile.py + output.txt cross-check)
GROUND_TRUTH = {
    "lagna": {"sign": "Virgo", "nakshatra": "Chitra", "pada": 1, "degree": 26.34},
    "Sun": {"sign": "Leo", "house": 12, "nakshatra": "Magha", "pada": 2, "degree": 4.99},
    "Moon": {"sign": "Cancer", "house": 11, "nakshatra": "Ashlesha", "pada": 1, "degree": 17.01},
    "Mercury": {"sign": "Cancer", "house": 11, "nakshatra": "Ashlesha", "pada": 3, "degree": 24.85},
    "Venus": {"sign": "Cancer", "house": 11, "nakshatra": "Ashlesha", "pada": 1, "degree": 17.46},
    "Mars": {"sign": "Leo", "house": 12, "nakshatra": "Purva Phalguni", "pada": 4, "degree": 25.15},
    "Jupiter": {"sign": "Libra", "house": 2, "nakshatra": "Swati", "pada": 4, "degree": 18.12},
    "Saturn": {"sign": "Cancer", "house": 11, "nakshatra": "Ashlesha", "pada": 2, "degree": 22.77},
    "Rahu": {"sign": "Pisces", "house": 7, "nakshatra": "Purva Bhadrapada", "pada": 4, "degree": 1.56, "retrograde": True},
    "Ketu": {"sign": "Virgo", "house": 1, "nakshatra": "Uttara Phalguni", "pada": 2, "degree": 1.56, "retrograde": True},
}


def check_planet(name: str, got: dict, exp: dict) -> list[str]:
    issues = []
    for field in ("sign", "house", "nakshatra", "pada"):
        g, e = got.get(field), exp.get(field)
        if g != e:
            issues.append(f"{field}: got={g} exp={e}")
    gd = got.get("degree", 0)
    ed = exp.get("degree", 0)
    if abs(gd - ed) > DEG_TOL:
        issues.append(f"degree: got={gd:.2f}° exp={ed:.2f}° (Δ{abs(gd-ed):.2f}°)")
    if "retrograde" in exp and bool(got.get("retrograde")) != exp["retrograde"]:
        issues.append(f"retrograde: got={got.get('retrograde')} exp={exp['retrograde']}")
    return issues


def main():
    print("=" * 72)
    print("  JYOTISH AI — FULL CHART VALIDATION (John Doe)")
    print("  Reference: VedicReport / kundali_profile / ground_truth.json")
    print("=" * 72)

    profile = load_user_profile(USER_ID)
    birth = profile["meta"]["birth"]
    print(f"\nBirth: {birth['day']:02d}/{birth['month']:02d}/{birth['year']} "
          f"{birth['hour']:02d}:{birth['minute']:02d} | {birth['city']}, {birth['nation']}")
    print(f"Timezone in profile: {birth.get('timezone', '?')} | lat={birth.get('lat')} lon={birth.get('lon')}")

    # ── Lagna ─────────────────────────────────────────────────────────────
    print("\n--- LAGNA ---")
    lagna = profile["lagna"]
    exp_l = GROUND_TRUTH["lagna"]
    lagna_issues = []
    if lagna["sign"] != exp_l["sign"]:
        lagna_issues.append(f"sign {lagna['sign']} != {exp_l['sign']}")
    if lagna["nakshatra"] != exp_l["nakshatra"]:
        lagna_issues.append(f"nakshatra {lagna['nakshatra']} != {exp_l['nakshatra']}")
    if lagna["pada"] != exp_l["pada"]:
        lagna_issues.append(f"pada {lagna['pada']} != {exp_l['pada']}")
    if abs(lagna["degree"] - exp_l["degree"]) > DEG_TOL:
        lagna_issues.append(f"degree {lagna['degree']:.2f} vs {exp_l['degree']:.2f}")
    status = "PASS" if not lagna_issues else "FAIL"
    print(f"  {status}: Virgo Lagna {lagna['degree']:.2f}° | {lagna['nakshatra']} P{lagna['pada']}")
    if lagna_issues:
        for i in lagna_issues:
            print(f"    ! {i}")

    # ── Planets (stored profile) ──────────────────────────────────────────
    print("\n--- PLANETS (profile.json vs ground truth) ---")
    print(f"{'Planet':<10} {'Sign':<8} {'H':<3} {'Deg':<7} {'Nakshatra':<18} {'P':<2} {'Status'}")
    print("-" * 72)
    planet_pass = 0
    planet_total = 0
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        got = profile["planets"][pname]
        exp = GROUND_TRUTH[pname]
        issues = check_planet(pname, got, exp)
        planet_total += 1
        ok = not issues
        if ok:
            planet_pass += 1
        tag = "OK" if ok else "DIFF"
        print(f"{pname:<10} {got['sign']:<8} {got['house']:<3} {got['degree']:<7.2f} "
              f"{got['nakshatra']:<18} {got['pada']:<2} [{tag}]")
        for iss in issues:
            print(f"           -> {iss}")

    # ── Live kerykeion recompute ──────────────────────────────────────────
    print("\n--- LIVE ENGINE (kerykeion fresh compute) ---")
    subject = get_natal_chart_from_profile(profile)
    m = subject.model()
    lagna_abs = m.ascendant.abs_pos
    live_ok = 0
    live_total = 0
    planet_keys = {
        "Sun": "sun", "Moon": "moon", "Mars": "mars", "Mercury": "mercury",
        "Jupiter": "jupiter", "Venus": "venus", "Saturn": "saturn",
        "Rahu": "true_north_lunar_node", "Ketu": "true_south_lunar_node",
    }
    for pname, key in planet_keys.items():
        p = getattr(m, key)
        sign = SIGN_MAP.get(p.sign, p.sign)
        deg = p.position if hasattr(p, "position") else (p.abs_pos % 30)
        house = get_house_from_asc(p.abs_pos, lagna_abs)
        nak, pada = get_nakshatra_and_pada(p.abs_pos)
        exp = GROUND_TRUTH[pname]
        live_total += 1
        match = (sign == exp["sign"] and house == exp["house"] and nak == exp["nakshatra"] and pada == exp["pada"])
        if match:
            live_ok += 1
        print(f"  {pname}: {sign} H{house} {deg:.2f}° {nak} P{pada} [{'OK' if match else 'CHECK'}]")

    # ── Ashtakavarga (ground_truth.json) ──────────────────────────────────
    print("\n--- ASHTAKAVARGA SAV ---")
    gt_path = os.path.join("data", "users", USER_ID, "ground_truth.json")
    av_pass = 0
    if os.path.exists(gt_path):
        with open(gt_path, encoding="utf-8") as f:
            gt = json.load(f)
        expected_sav = {int(k): v for k, v in gt["ashtakavarga"]["sarvashtakavarga"].items()}
        natal = get_natal_chart_from_profile(profile)
        av = calculate_ashtakavarga(natal)
        sav = av["sarvashtakavarga"]
        for h in range(1, 13):
            g, e = sav[h], expected_sav[h]
            ok = g == e
            if ok:
                av_pass += 1
            print(f"  H{h:2d}: got={g:2d} exp={e:2d} [{'OK' if ok else 'WRONG'}]")
        print(f"  SAV score: {av_pass}/12 houses exact match | Grand total: {av['grand_total']}")

    # ── Shadbala (approximate) ────────────────────────────────────────────
    print("\n--- SHADBALA RUPAS (vs ground_truth.json) ---")
    if os.path.exists(gt_path):
        exp_shad = gt["shadbala"]["shadbala_full"]
        shad = calculate_shadbala_rupas(natal)
        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            got = shad.get(p, {}).get("rupas", 0)
            exp = exp_shad[p]["rupas"]
            ratio = got / exp if exp else 0
            tag = "CLOSE" if 0.75 <= ratio <= 1.25 else "OFF"
            print(f"  {p}: got={got:.2f} exp={exp:.2f} ratio={ratio:.2f} [{tag}]")

    # ── kundali_profile static reference ────────────────────────────────────
    print("\n--- KUNDALI_PROFILE static module (sign/house match) ---")
    kp = KUNDALI_PROFILE["planets"]
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        k = kp[pname]
        p = profile["planets"][pname]
        ks = k["sign"]
        kh = k["house"]
        match = p["sign"] == ks and p["house"] == kh
        print(f"  {pname}: profile vs KUNDALI_PROFILE sign/house [{'OK' if match else 'DIFF'}]")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print(f"  SUMMARY")
    print(f"  Planets (profile):     {planet_pass}/{planet_total} exact match")
    print(f"  Planets (live engine): {live_ok}/{live_total} sign+house+nak+pada match")
    print(f"  Ashtakavarga SAV:      {av_pass}/12 exact (reference: ground_truth.json)")
    print("=" * 72)
    if birth.get("timezone") == "UTC":
        print("\n  NOTE: profile timezone is UTC — should be Asia/Kolkata (metadata fix recommended)")
    return 0 if planet_pass == planet_total and live_ok == live_total else 1


if __name__ == "__main__":
    sys.exit(main())
