"""
core/dosha_engine.py
────────────────────────────────────────────────────
Dosha Engine
Calculates various doshas and their cancellations.
────────────────────────────────────────────────────
"""

# Import or define house signs array, placeholder logic
# HOUSE_SIGNS would normally be calculated based on ascendant
# e.g., if asc is Aries (0), house 1 is 0, house 2 is 1...

def get_aspected_houses(planet_name, planet_house):
    # Quick duplicate or import from multi_layer_engine/astro_engine
    SPECIAL_ASPECTS = {
        "Mars":    [4, 8],
        "Jupiter": [5, 9],
        "Saturn":  [3, 10],
        "Rahu":    [5, 9],
        "Ketu":    [5, 9],
    }
    aspects = [7]  # universal for all planets
    aspects += SPECIAL_ASPECTS.get(planet_name.capitalize(), [])
    
    targets = []
    for offset in aspects:
        target = ((planet_house - 1 + offset - 1) % 12) + 1
        targets.append(target)
    return targets

def check_kuja_dosha_cancellation(planet_houses, house_lords, lagna_sign_idx=0):
    cancellations = []
    mars_house = planet_houses.get("Mars", 1)
    
    # house 1 corresponds to lagna_sign_idx, so mars_house sign is:
    mars_sign = (lagna_sign_idx + mars_house - 1) % 12
    
    # Cancelled if Mars in own sign or exalted
    if mars_sign in {0, 7}:  # Aries, Scorpio
        cancellations.append("Mars in own sign — Dosha cancelled")
    if mars_sign == 9:  # Capricorn
        cancellations.append("Mars exalted — Dosha cancelled")
    
    # Cancelled if Jupiter aspects Mars
    jup_house = planet_houses.get("Jupiter", 0)
    if jup_house:
        jup_aspects = get_aspected_houses("Jupiter", jup_house)
        if mars_house in jup_aspects:
            cancellations.append("Jupiter aspects Mars — Dosha reduced")
    
    return cancellations

def check_doshas(planet_houses, house_lords, lagna_sign_idx=0):
    doshas = []
    
    # KUJA DOSHA (Mangal Dosha) — Mars in 1,2,4,7,8,12
    mars_house = planet_houses.get("Mars")
    if mars_house and mars_house in {1,2,4,7,8,12}:
        severity = "High" if mars_house in {7,8} else "Moderate"
        cancellations = check_kuja_dosha_cancellation(planet_houses, house_lords, lagna_sign_idx)
        doshas.append({
            "name": "Kuja Dosha",
            "planet": "Mars",
            "house": mars_house,
            "severity": severity,
            "cancellation": cancellations
        })
    
    # GRAHAN DOSHA — Sun or Moon with Rahu or Ketu
    for luminary in ["Sun", "Moon"]:
        for node in ["Rahu", "Ketu"]:
            if planet_houses.get(luminary) and planet_houses.get(luminary) == planet_houses.get(node):
                doshas.append({
                    "name": "Grahan Dosha",
                    "planets": [luminary, node],
                    "house": planet_houses[luminary]
                })
    
    # GURU CHANDAL DOSHA — Jupiter with Rahu or Ketu
    for node in ["Rahu", "Ketu"]:
        if planet_houses.get("Jupiter") and planet_houses.get("Jupiter") == planet_houses.get(node):
            doshas.append({
                "name": "Guru Chandal Dosha",
                "planets": ["Jupiter", node],
                "house": planet_houses["Jupiter"]
            })
    
    # SHRAPIT DOSHA — Saturn with Rahu
    if planet_houses.get("Saturn") and planet_houses.get("Saturn") == planet_houses.get("Rahu"):
        doshas.append({"name": "Shrapit Dosha", "house": planet_houses["Saturn"]})
    
    # KEMDRUM DOSHA — Moon with no planets in adjacent houses
    moon_house = planet_houses.get("Moon")
    if moon_house:
        prev_house = (moon_house - 2) % 12 + 1
        next_house = moon_house % 12 + 1
        planets_near_moon = [p for p, h in planet_houses.items() 
                             if h in {prev_house, next_house} 
                             and p not in ("Moon", "Rahu", "Ketu", "Ascendant", "ASC")]
        if not planets_near_moon:
            doshas.append({
                "name": "Kemdrum Dosha",
                "moon_house": moon_house,
                "note": "Emotional isolation pattern — cancelled if Moon aspected by benefic"
            })
    
    return doshas
