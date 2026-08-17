"""
core/forecast_engine.py — 12-month forecast using user location and accurate dasha.
"""

from datetime import datetime, timedelta
from typing import Optional

from core.astro_engine import calculate_vimshottari_dasha, get_sky_on_date
from core.user_profile_engine import load_user_profile, get_active_profile, SIGN_IDX
from core.transit_engine import abs_pos_to_house


def generate_12_month_forecast(user_id: Optional[str] = None) -> str:
    try:
        profile = load_user_profile(user_id) if user_id else get_active_profile()
    except Exception as e:
        return f"[Forecast Engine Error: User profile could not be loaded - {e}]"

    meta = profile["meta"]
    birth = meta["birth"]
    lagna_sign = profile["lagna"]["sign"]
    lagna_idx = SIGN_IDX.get(lagna_sign, 0)

    birth_dt = datetime(
        birth["year"], birth["month"], birth["day"],
        birth["hour"], birth["minute"],
    )
    moon_lon = profile["planets"]["Moon"]["abs_pos"]
    city = birth.get("city", "Delhi")
    nation = birth.get("nation", "IN")

    start_date = datetime.now()
    forecast_lines = [
        f"12-MONTH FORECAST FOR {meta['name'].upper()}",
        "=" * 70,
        "Month-by-month Dasha lords + slow-planet transits (user birth location).",
        "",
    ]

    for i in range(12):
        target_date = start_date + timedelta(days=30 * i + 15)
        month_str = target_date.strftime("%B %Y")

        dasha_at = calculate_vimshottari_dasha(birth_dt, moon_lon, target_dt=target_date)
        if "error" in dasha_at:
            forecast_lines.append(f"{month_str}: Dasha data unavailable")
            continue

        active_md = dasha_at["current_mahadasha"]["lord"]
        active_ad = dasha_at["current_antardasha"]["lord"]
        active_pd = dasha_at["current_pratyantardasha"]["lord"]

        try:
            sky = get_sky_on_date(
                target_date.year, target_date.month, target_date.day,
                12, 0, city, nation,
            )
            m_sky = sky.model()

            jup_h = abs_pos_to_house(m_sky.jupiter.abs_pos, lagna_idx)
            sat_h = abs_pos_to_house(m_sky.saturn.abs_pos, lagna_idx)
            rah_h = abs_pos_to_house(m_sky.true_north_lunar_node.abs_pos, lagna_idx)
            sun_h = abs_pos_to_house(m_sky.sun.abs_pos, lagna_idx)

            sav = profile.get("ashtakavarga", {}).get("sarvashtakavarga", {})
            jup_sav = int(sav.get(jup_h, sav.get(str(jup_h), 25)))
            sat_sav = int(sav.get(sat_h, sav.get(str(sat_h), 25)))

            forecast_lines.append(f"{month_str}")
            forecast_lines.append(
                f"  Dasha: {active_md} MD / {active_ad} AD / {active_pd} PD"
            )
            forecast_lines.append(
                f"  Transits: Sun H{sun_h} | Jupiter H{jup_h} (SAV {jup_sav}) | "
                f"Saturn H{sat_h} (SAV {sat_sav}) | Rahu H{rah_h}"
            )

            if jup_h in (1, 5, 9, 10, 11) and jup_sav >= 28:
                forecast_lines.append("  Signal: Jupiter supports growth this month.")
            if sat_h in (6, 8, 12) and sat_sav < 25:
                forecast_lines.append("  Signal: Saturn tests patience — avoid rash decisions.")
            if sun_h in (10, 11):
                forecast_lines.append("  Signal: Solar focus on career and gains.")

            forecast_lines.append("")
        except Exception as e:
            forecast_lines.append(f"{month_str} — transit unavailable: {e}\n")

    return "\n".join(forecast_lines)
