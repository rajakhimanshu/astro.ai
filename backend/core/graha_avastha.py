"""
core/graha_avastha.py
────────────────────────────────────────────────────
Graha Avastha Engine
Calculates planetary states that modify interpretation.
────────────────────────────────────────────────────
"""

def get_graha_avastha(planet, abs_pos, house, is_retrograde, dignity, age_of_person=None):
    """
    Planetary states that modify interpretation
    """
    states = []
    degree = abs_pos % 30
    sign_idx = int(abs_pos // 30) % 12
    
    # BALA AVASTHA (by degree in sign - depends on odd/even sign)
    is_odd = sign_idx % 2 == 0 # 0=Aries (odd)
    if is_odd:
        if 0 <= degree < 6:     bala = "Infant"      # weak, no results
        elif 6 <= degree < 12:  bala = "Child"        # partial results
        elif 12 <= degree < 18: bala = "Adolescent"   # moderate
        elif 18 <= degree < 24: bala = "Adult"        # full results
        elif 24 <= degree <= 30: bala = "Old"          # past peak
    else:
        if 0 <= degree < 6:     bala = "Old"          # past peak
        elif 6 <= degree < 12:  bala = "Adult"        # full results
        elif 12 <= degree < 18: bala = "Adolescent"   # moderate
        elif 18 <= degree < 24: bala = "Child"        # partial results
        elif 24 <= degree <= 30: bala = "Infant"      # weak, no results
    states.append({"type":"Bala", "state":bala})
    
    # LAJJITA (Ashamed) — planets in 5th with Rahu,Ketu,Saturn,Sun,Mars
    # GARVITA (Proud) — exalted or Moolatrikona
    if dignity in ("Exalted", "Moolatrikona"):
        states.append({"type":"Garvita", "state":"Proud — delivers superior results"})
    
    # KSHUDITA (Hungry) — in enemy sign or aspected by enemy
    if dignity in ("Enemy", "Great Enemy", "Debilitated"):
        states.append({"type":"Kshudita", "state":"Hungry — struggles to deliver"})
    
    # TRUSHITA (Thirsty) — in watery sign aspected by malefic
    WATERY_SIGNS = {3, 7, 11}  # Cancer, Scorpio, Pisces
    if sign_idx in WATERY_SIGNS:
        states.append({"type":"Trushita", "state":"Thirsty — emotional instability"})
    
    # MUDITA (Delighted) — in friend's sign or with benefics
    if dignity in ("Friend", "Great Friend", "Own Sign"):
        states.append({"type":"Mudita", "state":"Delighted — gives good results"})
    
    # DEEPTAVASTHA — exalted and high degree
    if dignity == "Exalted" and degree >= 18:
        states.append({"type":"Deepta", "state":"Radiant — maximum power"})
    
    return states
