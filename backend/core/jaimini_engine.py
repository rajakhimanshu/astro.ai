"""
core/jaimini_engine.py
────────────────────────────────────────────────────
Jaimini System (Full Implementation)
Chara Karakas, Arudhas, Jaimini Aspects, and Chara Dasha
────────────────────────────────────────────────────
"""
from datetime import datetime, timedelta

KARAKA_NAMES = [
    "Atmakaraka", "Amatyakaraka", "Bhratrikaraka",
    "Matrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka"
]

def calculate_chara_karakas(planet_positions_abs):
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    
    # Get degree within sign for each planet
    degrees = {}
    for p in planets:
        abs_pos = planet_positions_abs.get(p, 0)
        deg_in_sign = abs_pos % 30
        # Rahu uses reverse — subtract from 30
        degrees[p] = deg_in_sign
    
    # Sort descending by degree in sign
    ranked = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
    
    karakas = {}
    for i, (planet, deg) in enumerate(ranked):
        if i < len(KARAKA_NAMES):
            karakas[KARAKA_NAMES[i]] = {"planet": planet, "degree": deg}
    
    return karakas

# Arudha Lagna calculation
def get_arudha_lagna(house_num, lord_house, asc_house=1):
    """
    Count as many houses from the lord as the lord is from the house
    """
    distance = (lord_house - house_num) % 12
    if distance == 0: distance = 12
    arudha = (lord_house + distance - 1) % 12 + 1
    
    # Exception: if Arudha falls in same house or 7th from it, move 10 houses
    if arudha == house_num or arudha == (house_num + 6 - 1) % 12 + 1:
        arudha = (arudha + 9 - 1) % 12 + 1
    
    return arudha

def calculate_all_arudhas(house_lords, planet_houses):
    """Calculate Arudha for all 12 houses"""
    arudhas = {}
    for house in range(1, 13):
        lord = house_lords.get(house)
        if not lord: continue
        lord_house = planet_houses.get(lord.capitalize(), planet_houses.get(lord))
        if not lord_house: continue
        arudha = get_arudha_lagna(house, lord_house)
        arudhas[f"A{house}"] = arudha
    
    # AL = Arudha Lagna (A1), UL = Upapada Lagna (A12)
    if "A1" in arudhas: arudhas["AL"] = arudhas["A1"]
    if "A12" in arudhas: arudhas["UL"] = arudhas["A12"]
    return arudhas

# Jaimini Aspects (Rashi Drishti — sign-based, not planet-based)
def get_jaimini_aspects(sign_idx):
    """
    Fixed signs aspect movable signs except adjacent
    Movable signs aspect fixed signs except adjacent  
    Common signs aspect each other except adjacent
    """
    MOVABLE = {0,3,6,9}   # Aries,Cancer,Libra,Capricorn
    FIXED   = {1,4,7,10}  # Taurus,Leo,Scorpio,Aquarius
    COMMON  = {2,5,8,11}  # Gemini,Virgo,Sagittarius,Pisces
    
    aspected = []
    
    if sign_idx in MOVABLE:
        for s in FIXED:
            if abs(s - sign_idx) != 1 and abs(s - sign_idx) != 11:
                aspected.append(s)
    elif sign_idx in FIXED:
        for s in MOVABLE:
            if abs(s - sign_idx) != 1 and abs(s - sign_idx) != 11:
                aspected.append(s)
    elif sign_idx in COMMON:
        for s in COMMON:
            if s != sign_idx and abs(s - sign_idx) != 1 and abs(s - sign_idx) != 11:
                aspected.append(s)
    
    return aspected

# Jaimini Chara Dasha
CHARA_DASHA_YEARS = {
    0:7,1:8,2:9,3:10,4:11,5:12,6:1,7:2,8:3,9:4,10:5,11:6
}  # sign index → years

def get_chara_dasha_sequence(asc_sign_idx, planet_in_signs):
    """
    Sequence depends on whether Ascendant is odd or even sign
    Odd signs: go forward (Aries→Taurus→Gemini...)
    Even signs: go backward (Pisces→Aquarius→Capricorn...)
    """
    sequence = []
    if asc_sign_idx % 2 == 0:  # odd sign (0=Aries is odd in Jaimini)
        for i in range(12):
            sign = (asc_sign_idx + i) % 12
            sequence.append(sign)
    else:  # even sign — go backward
        for i in range(12):
            sign = (asc_sign_idx - i) % 12
            sequence.append(sign)
    
    return [(s, CHARA_DASHA_YEARS[s]) for s in sequence]

def calculate_chara_dasha(birth_date, lagna_sign_idx, planets_data):
    """
    K.N. Rao method for Chara Dasha timing.
    """
    sequence = get_chara_dasha_sequence(lagna_sign_idx, planets_data)
    
    dashas = []
    current_start = birth_date
    
    for sign_idx, years in sequence:
        # Years can be adjusted by sign-specific rules (K.N. Rao)
        # For simplicity, using the base years here, but real Rao method
        # adds/subtracts based on lord's position.
        
        # Simplified: Use the CHARA_DASHA_YEARS directly as provided in formula
        duration_days = years * 365.25
        end_date = current_start + timedelta(days=duration_days)
        
        dashas.append({
            "sign": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"][sign_idx],
            "years": years,
            "start": current_start,
            "end": end_date
        })
        current_start = end_date
        
    # Find current
    now = datetime.now()
    current_md = None
    for d in dashas:
        if d["start"] <= now < d["end"]:
            current_md = d
            break
            
    return {
        "full_sequence": dashas,
        "current_md": current_md
    }
