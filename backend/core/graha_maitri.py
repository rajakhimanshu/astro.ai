"""
core/graha_maitri.py
────────────────────────────────────────────────────
Graha Maitri (Compound Relationship Score)
Calculates relationship between two planets.
────────────────────────────────────────────────────
"""

# Copied from the user's definitions
NATURAL_FRIENDS = {
    "Sun":    {"friend":["Moon","Mars","Jupiter"], "enemy":["Venus","Saturn"], "neutral":["Mercury"]},
    "Moon":   {"friend":["Sun","Mercury"],         "enemy":[],               "neutral":["Mars","Jupiter","Venus","Saturn"]},
    "Mars":   {"friend":["Sun","Moon","Jupiter"],  "enemy":["Mercury"],       "neutral":["Venus","Saturn"]},
    "Mercury":{"friend":["Sun","Venus"],           "enemy":["Moon"],          "neutral":["Mars","Jupiter","Saturn"]},
    "Jupiter":{"friend":["Sun","Moon","Mars"],     "enemy":["Mercury","Venus"],"neutral":["Saturn"]},
    "Venus":  {"friend":["Mercury","Saturn"],      "enemy":["Sun","Moon"],    "neutral":["Mars","Jupiter"]},
    "Saturn": {"friend":["Mercury","Venus"],       "enemy":["Sun","Moon","Mars"],"neutral":["Jupiter"]},
}

COMPOUND_FRIENDSHIP = {
    ("friend","friend"): "Great Friend",
    ("friend","enemy"):  "Neutral",
    ("enemy","friend"):  "Neutral",
    ("enemy","enemy"):   "Great Enemy",
    ("neutral","friend"):"Friend",
    ("neutral","enemy"): "Enemy",
    ("friend","neutral"):"Friend",
    ("enemy","neutral"): "Enemy",
    ("neutral","neutral"):"Neutral",
}

def get_temporary_friendship(planet_a, planet_b, all_planet_houses):
    """
    Planets in 2, 3, 4, 10, 11, 12 from each other are temporary friends.
    Planets in same house or 5, 6, 7, 8, 9 from each other are temporary enemies.
    """
    house_a = all_planet_houses.get(planet_a, 1)
    house_b = all_planet_houses.get(planet_b, 1)
    dist = abs(house_a - house_b)
    dist = min(dist, 12 - dist)
    return "friend" if dist <= 5 else "enemy"

def graha_maitri_score(planet_a, planet_b, all_planet_houses):
    """
    For synastry or checking planetary relationships in natal chart
    """
    # Nodes don't have classical natural friendships defined here, but fallback to Neutral
    if planet_a not in NATURAL_FRIENDS or planet_b not in NATURAL_FRIENDS:
        return {"relationship": "Neutral", "score": 0}
        
    nat_rel = "neutral"
    for rel, planets in NATURAL_FRIENDS[planet_a].items():
        if planet_b in planets:
            nat_rel = rel
            break
    
    temp_rel = get_temporary_friendship(planet_a, planet_b, all_planet_houses)
    compound = COMPOUND_FRIENDSHIP.get((nat_rel, temp_rel), "Neutral")
    
    SCORE_MAP = {
        "Great Friend":2, "Friend":1, "Neutral":0,
        "Enemy":-1, "Great Enemy":-2
    }
    return {"relationship": compound, "score": SCORE_MAP.get(compound, 0)}
