"""Validate Vimshottari dasha against kundali_profile reference dates."""
import sys
import os
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.user_profile_engine import load_user_profile
from core.astro_engine import calculate_vimshottari_dasha

# Reference from kundali_profile.py / AstroSage-style reports
REFERENCE = {
    "ketu_md_start": datetime(2023, 3, 17),
    "mars_ad_start": datetime(2025, 9, 20),
    "mars_ad_end": datetime(2026, 2, 17),
    "rahu_ad_start": datetime(2026, 2, 17),
    "rahu_ad_end": datetime(2027, 3, 5),
}

TOL_DAYS = 5


def _days_diff(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds()) / 86400


def main():
    profile = load_user_profile("john_doe")
    birth = profile["meta"]["birth"]
    birth_dt = datetime(birth["year"], birth["month"], birth["day"], birth["hour"], birth["minute"])
    moon = profile["planets"]["Moon"]["abs_pos"]
    now = datetime(2026, 6, 22, 12, 0)

    d = calculate_vimshottari_dasha(birth_dt, moon, target_dt=now)
    print("=" * 60)
    print("DASHA VALIDATION — John Doe")
    print("=" * 60)
    print(f"\nAs of {now.date()}:")
    print(f"  MD: {d['current_mahadasha']['lord']} until {d['current_mahadasha'].get('end_inclusive')}")
    print(f"  AD: {d['current_antardasha']['lord']} until {d['current_antardasha'].get('end_inclusive')}")
    print(f"  PD: {d['current_pratyantardasha']['lord']} until {d['current_pratyantardasha'].get('end_inclusive')}")
    print(f"\n{d['summary']}")

    # Ketu MD antardashas from full timeline
    ketu = next(x for x in d["full_timeline"] if x["lord"] == "Ketu")
    mars_ad = next(a for a in ketu["antardashas"] if a["lord"] == "Mars")
    rahu_ad = next(a for a in ketu["antardashas"] if a["lord"] == "Rahu")

    checks = [
        ("Ketu MD start", datetime.fromisoformat(ketu["start"]), REFERENCE["ketu_md_start"]),
        ("Mars AD start", datetime.fromisoformat(mars_ad["start"]), REFERENCE["mars_ad_start"]),
        ("Mars AD end", datetime.fromisoformat(mars_ad["end"]), REFERENCE["mars_ad_end"]),
        ("Rahu AD start", datetime.fromisoformat(rahu_ad["start"]), REFERENCE["rahu_ad_start"]),
        ("Rahu AD end", datetime.fromisoformat(rahu_ad["end"]), REFERENCE["rahu_ad_end"]),
    ]
    print("\n--- vs kundali_profile reference ---")
    ok = 0
    for name, got, exp in checks:
        diff = _days_diff(got, exp)
        tag = "OK" if diff <= TOL_DAYS else "OFF"
        if tag == "OK":
            ok += 1
        print(f"  {name}: got={got.date()} ref={exp.date()} Δ{diff:.1f}d [{tag}]")

    print("\n--- Ketu-Rahu Pratyantardashas ---")
    for pd in rahu_ad.get("pratyantardashas", []):
        mark = " <<" if pd["lord"] == d["current_pratyantardasha"]["lord"] else ""
        print(f"  {pd['lord']:8s} {pd['start']} -> {pd['end']}{mark}")

    print(f"\nResult: {ok}/{len(checks)} within {TOL_DAYS} days of reference")
    return 0 if ok >= len(checks) - 1 else 1


if __name__ == "__main__":
    sys.exit(main())
