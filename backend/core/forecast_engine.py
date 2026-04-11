"""
core/forecast_engine.py
────────────────────────────────────────────────────
Auto-generates a 12-month Panchaka-style forecast.
Checks the month-by-month Dasha and Slow Planet
transits (Jupiter, Saturn, Rahu, Ketu, and Sun) 
relative to the user's natal chart.
────────────────────────────────────────────────────
"""

from datetime import datetime, timedelta
from typing import Optional
from core.astro_engine import (
    load_birth_data,
    calculate_vimshottari_dasha
)
from core.user_profile_engine import load_user_profile, get_active_profile
from core.transit_engine import abs_pos_to_house, PLANETS_KEYS

def generate_12_month_forecast(user_id: Optional[str] = None) -> str:
    """
    Generates a month-by-month forecast for the next 12 months.
    It combines active Dasha lords with the transit houses of slow planets.
    """
    import kerykeion

    try:
        profile = load_user_profile(user_id) if user_id else get_active_profile()
    except Exception as e:
        return f"[Forecast Engine Error: User profile could not be loaded - {e}]"

    meta = profile["meta"]
    lagna_sign = profile["lagna"]["sign"]
    
    # Needs LAGNA_SIGN_IDX correctly computed based on user lagna for transit_engine mapping
    from core.user_profile_engine import SIGN_IDX
    lagna_idx = SIGN_IDX.get(lagna_sign, 0)
    
    # We will compute dasha for the upcoming 12 months
    birth = meta["birth"]
    birth_dt = datetime(birth['year'], birth['month'], birth['day'], birth['hour'], birth['minute'])
    moon_lon = profile["planets"]["Moon"]["abs_pos"]
    dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon)
    
    # Determine the current date
    start_date = datetime.now()
    
    forecast_lines = [
        f"📅 12-MONTH FORECAST FOR {meta['name'].upper()}",
        "=" * 70,
        "Here is the month-by-month breakdown of active Dasha periods and major transits.",
        ""
    ]

    for i in range(12):
        # Pick a mid-month date for evaluating transits
        target_date = start_date + timedelta(days=30 * i)
        month_str = target_date.strftime("%B %Y")
        
        # 1. Evaluate Dasha at target_date
        # We find which Dasha period covers target_date
        current_md = ""
        current_ad = ""
        pd_lord = ""
        
        # Basic parsing using upcoming transitions, or we simply rely on a full dasha compute (complex).
        # We will re-run the dasha at the target date for accuracy.
        # Actually calculate_vimshottari_dasha doesn't take target_date, it returns current relative to now.
        # Let's approximate the dasha lords by finding the active transition in 'upcoming_transitions'
        active_md = dasha_info.get("current_mahadasha", {}).get("lord", "")
        active_ad = dasha_info.get("current_antardasha", {}).get("lord", "")
        
        # We'll step through dasha_info['upcoming_transitions'] to see if they shifted
        for trans in dasha_info.get("upcoming_transitions", []):
            if trans["date"] < target_date:
                if trans["type"] == "Mahadasha":
                    active_md = trans["to_lord"]
                elif trans["type"] == "Antardasha":
                    active_ad = trans["to_lord"]

        # 2. Evaluate Transits at target_date using kerykeion
        # Kerykeion doesn't directly compute exact transits simply without geonames,
        # but we can do a simplified AstrologicalSubject at target time.
        try:
            sky = kerykeion.AstrologicalSubject("Sky", target_date.year, target_date.month, target_date.day, 12, 0, "London", "GB")
            m_sky = sky.model()
            
            jup_pos = m_sky.jupiter.abs_pos
            sat_pos = m_sky.saturn.abs_pos
            rah_pos = m_sky.true_north_lunar_node.abs_pos
            sun_pos = m_sky.sun.abs_pos
            
            jup_h = abs_pos_to_house(jup_pos, lagna_idx)
            sat_h = abs_pos_to_house(sat_pos, lagna_idx)
            rah_h = abs_pos_to_house(rah_pos, lagna_idx)
            sun_h = abs_pos_to_house(sun_pos, lagna_idx)
            
            # Format the output for the month
            forecast_lines.append(f"🔵 {month_str}")
            forecast_lines.append(f"   Dasha: {active_md} MD -> {active_ad} AD")
            forecast_lines.append(f"   Transits: Sun in H{sun_h} | Jupiter in H{jup_h} | Saturn in H{sat_h} | Rahu in H{rah_h}")
            
            # Add a punchy insight based on the Sun's transit (Panchaka style)
            if sun_h in [6, 8, 12]:
                forecast_lines.append("   Focus: Low energy period, avoid major risks. Prioritize health.")
            elif sun_h in [1, 5, 9]:
                forecast_lines.append("   Focus: Time for personal growth, travel, and spiritual pursuits.")
            elif sun_h in [10, 11]:
                forecast_lines.append("   Focus: Excellent period for career recognition and financial gains.")
            elif sun_h in [2, 3, 4, 7]:
                forecast_lines.append("   Focus: Attention drawn toward family, communication, or partnerships.")

            forecast_lines.append("")
        except Exception as e:
            forecast_lines.append(f"🔵 {month_str} - [Transit ephemeris unavailable: {str(e)}]")

    return "\n".join(forecast_lines)
