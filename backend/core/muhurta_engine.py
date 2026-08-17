"""
core/muhurta_engine.py
────────────────────────────────────────────────────
Muhurta Engine (Auspicious Timing)
Calculates Muhurta score for specific events.
────────────────────────────────────────────────────
"""
import swisseph as swe
from core.panchanga_engine import calculate_panchanga

def calculate_muhurta_score(target_jd, natal_chart, purpose="general"):
    """
    Score a moment for auspiciousness — higher = better muhurta
    """
    panchanga = calculate_panchanga(target_jd, natal_chart["lat"], natal_chart["lon"])
    score = 0
    flags = []
    
    # GOOD TITHIS by purpose
    GOOD_TITHI = {
        "business":   [2,3,5,7,10,11,13],
        "marriage":   [2,3,5,7,10,11],
        "travel":     [2,3,5,7,10,11,12],
        "investment": [2,3,6,10,11],
        "general":    [2,3,5,6,7,10,11,12,13],
    }
    BAD_TITHI = [4,8,9,14,15,30]
    
    tithi = panchanga["tithi"]["number"]
    if tithi in GOOD_TITHI.get(purpose, GOOD_TITHI["general"]):
        score += 2; flags.append("Good Tithi")
    if tithi in BAD_TITHI:
        score -= 3; flags.append("Bad Tithi")
    
    # GOOD VARAS
    GOOD_VARA = {
        "business":   ["Mercury","Jupiter","Venus"],
        "investment": ["Mercury","Jupiter","Venus","Moon"],
        "general":    ["Sun","Moon","Mercury","Jupiter","Venus"],
    }
    vara_lord = panchanga["vara"]["lord"]
    if vara_lord in GOOD_VARA.get(purpose, GOOD_VARA["general"]):
        score += 2; flags.append(f"Good Vara ({vara_lord})")
    if vara_lord in ["Saturn","Mars"]:
        score -= 1; flags.append(f"Difficult Vara ({vara_lord})")
    
    # GOOD NAKSHATRAS
    GOOD_NAK = {
        "business":   [1,4,6,7,8,10,11,12,13,16,17,20,22,24,25,26],
        "general":    [1,3,5,7,8,10,12,13,16,17,20,22,24,25,26,27],
    }
    BAD_NAK = [6,9,10,13,14,17,18,19]  # Ardra,Ashlesha,Magha,Jyeshtha,Mula,Vyatipata,Parigha
    
    nak = panchanga["nakshatra"]["index"]
    if nak in GOOD_NAK.get(purpose, GOOD_NAK["general"]):
        score += 2; flags.append("Good Nakshatra")
    if nak in BAD_NAK:
        score -= 2; flags.append("Bad Nakshatra")
    
    # AVOID RAHU KAAL
    try:
        vara_index = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"].index(vara_lord)
        RAHU_KAAL_ORDER = [8,2,7,5,6,4,3]  # segments: 1=1st 1.5hr, 2=2nd etc
        rahu_segment = RAHU_KAAL_ORDER[vara_index]
        # Convert target_jd to local time and check if in Rahu Kaal window
        # Each day = 8 segments of 1.5 hours from sunrise
        # ... time comparison left abstract per system limits
    except Exception:
        pass
    
    # CHANDRA BALA (Moon's transit from natal Moon)
    natal_moon_sign = int(natal_chart.get("moon_abs", 0) // 30)
    transit_moon_pos = swe.calc_ut(target_jd, swe.MOON)[0][0]
    transit_moon_sign = int(transit_moon_pos // 30)
    moon_distance = (transit_moon_sign - natal_moon_sign) % 12 + 1
    
    GOOD_CHANDRA = [1,3,6,7,10,11]
    if moon_distance in GOOD_CHANDRA:
        score += 2; flags.append(f"Good Chandra Bala (Moon in {moon_distance}th)")
    
    # TARABALA (Nakshatra from natal birth star)
    natal_nak = int(natal_chart.get("moon_abs", 0) / (360/27))
    transit_nak = int(transit_moon_pos / (360/27))
    tara = ((transit_nak - natal_nak) % 27) + 1
    tara_group = ((tara - 1) % 9) + 1
    
    GOOD_TARA = [1,3,5,7]  # Janma,Vipat,Kshema,Sadhana... 
    GOOD_TARA_GROUPS = {1:"Janma(caution)",2:"Sampat(wealth)",3:"Vipat(danger)",
                        4:"Kshema(well-being)",5:"Pratyari(obstacle)",
                        6:"Sadhaka(achievement)",7:"Vadha(death-like)",
                        8:"Mitra(friend)",9:"Parama Mitra(best friend)"}
    GOOD_TARA_NUMS = [2,4,6,8,9]
    if tara_group in GOOD_TARA_NUMS:
        score += 1; flags.append(f"Good Tarabala ({GOOD_TARA_GROUPS.get(tara_group, '')})")
    
    if score >= 5:   quality = "Excellent Muhurta"
    elif score >= 3: quality = "Good Muhurta"
    elif score >= 1: quality = "Acceptable"
    elif score >= 0: quality = "Neutral"
    else:            quality = "Avoid"
    
    return {"score":score, "quality":quality, "flags":flags}
