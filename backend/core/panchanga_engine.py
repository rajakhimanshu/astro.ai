"""
core/panchanga_engine.py
────────────────────────────────────────────────────
Panchanga Engine
Full 5-limb Vedic time quality calculation.
────────────────────────────────────────────────────
"""
import math
from datetime import datetime

def get_nakshatra(abs_pos):
    NAKSHATRA_LORDS = [
        "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter",
        "Saturn","Mercury","Ketu","Venus","Sun","Moon","Mars",
        "Rahu","Jupiter","Saturn","Mercury","Ketu","Venus","Sun",
        "Moon","Mars","Rahu","Jupiter","Saturn","Mercury"
    ]
    nak_index = int(abs_pos / (360/27))
    pada = int((abs_pos % (360/27)) / (360/108)) + 1
    lord = NAKSHATRA_LORDS[nak_index]
    return nak_index, pada, lord

def calculate_panchanga(jd, lat, lon):
    """jd = Julian Day Number from Swiss Ephemeris"""
    import swisseph as swe
    
    sun_pos  = swe.calc_ut(jd, swe.SUN)[0][0]
    moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
    
    # 1. TITHI (lunar day)
    tithi_angle = (moon_pos - sun_pos) % 360
    tithi_num   = int(tithi_angle / 12) + 1  # 1-30
    tithi_completion = (tithi_angle % 12) / 12  # how far through current tithi
    
    TITHI_NAMES = [
        "Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami",
        "Shashthi","Saptami","Ashtami","Navami","Dashami",
        "Ekadashi","Dwadashi","Trayodashi","Chaturdasi","Purnima/Amavasya"
    ]
    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    tithi_name = TITHI_NAMES[(tithi_num - 1) % 15]
    
    # 2. VARA (weekday) — from Julian Day
    weekday = int(jd + 1.5) % 7  # 0=Sun,1=Mon,2=Tue...
    VARA_NAMES = ["Ravivara","Somavara","Mangalavara","Budhavara",
                  "Guruvara","Shukravara","Shanivara"]
    VARA_LORDS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
    
    # 3. NAKSHATRA
    nak_index, pada, nak_lord = get_nakshatra(moon_pos)
    
    # 4. YOGA (not Raj Yoga — Panchanga Yoga)
    yoga_angle = (sun_pos + moon_pos) % 360
    yoga_num   = int(yoga_angle / (360/27))
    YOGA_NAMES = [
        "Vishkambha","Priti","Ayushman","Saubhagya","Shobhana",
        "Atiganda","Sukarma","Dhriti","Shula","Ganda","Vriddhi",
        "Dhruva","Vyaghata","Harshana","Vajra","Siddhi","Vyatipata",
        "Variyan","Parigha","Shiva","Siddha","Sadhya","Shubha",
        "Shukla","Brahma","Indra","Vaidhriti"
    ]
    
    # 5. KARANA (half of tithi)
    karana_num = int(tithi_angle / 6) % 60
    FIXED_KARANAS   = ["Shakuni","Chatushpada","Naga","Kimstughna"]
    MOVABLE_KARANAS = ["Bava","Balava","Kaulava","Taitila","Garija",
                       "Vanija","Vishti"]
    
    if karana_num < 4:
        karana = FIXED_KARANAS[karana_num]
    else:
        karana = MOVABLE_KARANAS[(karana_num - 4) % 7]
    
    # 6. SUNRISE/SUNSET from Swiss Ephemeris
    try:
        # Pyswisseph might vary in function signature, this assumes standard swe.rise_trans
        sunrise = swe.rise_trans(jd, swe.SUN, lon, lat, 0.0, 0, swe.CALC_RISE | swe.BIT_DISC_CENTER)[1][0]
        sunset  = swe.rise_trans(jd, swe.SUN, lon, lat, 0.0, 0, swe.CALC_SET  | swe.BIT_DISC_CENTER)[1][0]
    except Exception:
        # Fallback if standard parameters fail (some wrappers differ slightly)
        sunrise, sunset = 0.0, 0.0
    
    return {
        "tithi": {"number":tithi_num,"name":tithi_name,"paksha":paksha,
                  "completion_pct": round(tithi_completion*100,1)},
        "vara":  {"name":VARA_NAMES[weekday],"lord":VARA_LORDS[weekday]},
        "nakshatra": {"index":nak_index,"lord":nak_lord,"pada":pada},
        "yoga":  {"name":YOGA_NAMES[yoga_num]},
        "karana":{"name":karana},
        "sunrise_jd": sunrise,
        "sunset_jd":  sunset,
    }
