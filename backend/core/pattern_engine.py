import json
import sqlite3
from datetime import datetime
from core.astro_engine import get_current_sky, get_planet_snapshot_dict, calculate_vimshottari_dasha, load_birth_data

def get_current_signature():
    """Returns a 'planetary signature' dictionary for the current slow-moving planets."""
    # 1. Get current sky and dasha
    current_sky = get_current_sky()
    
    bd = load_birth_data()
    birth_dt = datetime(bd['year'], bd['month'], bd['day'], bd['hour'], bd['minute'])
    natal_chart = get_natal_chart_for_pattern()
    moon_lon_at_birth = natal_chart.model().moon.abs_pos
    
    dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon_at_birth)
    snapshot = get_planet_snapshot_dict(current_sky, dasha_info)
    
    return {
        "mahadasha": snapshot["mahadasha"],
        "antardasha": snapshot["antardasha"],
        "saturn_house": snapshot["saturn"]["house"],
        "jupiter_house": snapshot["jupiter"]["house"],
        "rahu_house": snapshot["rahu"]["house"],
        "ketu_house": snapshot["ketu"]["house"],
        "saturn_sign": snapshot["saturn"]["sign"],
        "jupiter_sign": snapshot["jupiter"]["sign"]
    }

def get_natal_chart_for_pattern():
    # Helper to avoid circular imports or repeated code
    from core.astro_engine import get_natal_chart
    return get_natal_chart()

def get_event_signature(planet_snapshot_json):
    """Extracts slow-planet signature from a stored JSON snapshot."""
    snap = json.loads(planet_snapshot_json)
    return {
        "mahadasha": snap.get("mahadasha"),
        "antardasha": snap.get("antardasha"),
        "saturn_house": snap.get("saturn", {}).get("house"),
        "jupiter_house": snap.get("jupiter", {}).get("house"),
        "rahu_house": snap.get("rahu", {}).get("house"),
        "ketu_house": snap.get("ketu", {}).get("house"),
        "saturn_sign": snap.get("saturn", {}).get("sign"),
        "jupiter_sign": snap.get("jupiter", {}).get("sign")
    }

def calculate_similarity_score(sig1, sig2):
    """Compares two signatures and returns a score 0-100 with matching factors."""
    score = 0
    matches = []
    
    # MD: 25 points
    if sig1["mahadasha"] == sig2["mahadasha"]:
        score += 25
        matches.append("Same Mahadasha")
        
    # AD: 20 points
    if sig1["antardasha"] == sig2["antardasha"]:
        score += 20
        matches.append("Same Antardasha")
        
    # Saturn House: 20 points (±1 tolerance)
    s1, s2 = sig1["saturn_house"], sig2["saturn_house"]
    if s1 and s2:
        diff = abs(s1 - s2)
        if diff == 0:
            score += 20
            matches.append("Saturn in same house")
        elif diff == 1 or diff == 11: # 11 handles 12 to 1 wrap
            score += 10
            matches.append("Saturn in adjacent house")

    # Jupiter House: 20 points (±1 tolerance)
    j1, j2 = sig1["jupiter_house"], sig2["jupiter_house"]
    if j1 and j2:
        diff = abs(j1 - j2)
        if diff == 0:
            score += 20
            matches.append("Jupiter in same house")
        elif diff == 1 or diff == 11:
            score += 10
            matches.append("Jupiter in adjacent house")

    # Rahu/Ketu: 15 points (±1 tolerance)
    r1, r2 = sig1["rahu_house"], sig2["rahu_house"]
    if r1 and r2:
        diff = abs(r1 - r2)
        if diff == 0:
            score += 15
            matches.append("Rahu/Ketu axis identical")
        elif diff == 1 or diff == 11:
            score += 7
            matches.append("Rahu/Ketu axis similar")

    return score, matches

def find_similar_past_periods(top_n=3):
    """Finds top N most astrologically similar events from history."""
    current_sig = get_current_signature()
    
    conn = sqlite3.connect('data/life_events.db')
    conn.row_factory = sqlite3.Row
    events = conn.execute('SELECT * FROM events WHERE planet_snapshot IS NOT NULL').fetchall()
    conn.close()
    
    scored_events = []
    for ev in events:
        try:
            ev_sig = get_event_signature(ev['planet_snapshot'])
            score, matches = calculate_similarity_score(current_sig, ev_sig)
            scored_events.append({
                "id": ev['id'],
                "date": ev['date'],
                "title": ev['title'],
                "description": ev['description'],
                "outcome": ev['outcome'],
                "emotion_score": ev['emotion_score'],
                "score": score,
                "matches": matches
            })
        except Exception as e:
            print(f"Error processing event {ev['id']}: {e}")
            
    # Sort by score descending
    scored_events.sort(key=lambda x: x['score'], reverse=True)
    return scored_events[:top_n]

def format_pattern_report(similar_events):
    """Formats the results into a text report for the LLM."""
    if not similar_events:
        return "PATTERN ANALYSIS: No similar past periods found in history."
        
    lines = [f"PATTERN ANALYSIS: {len(similar_events)} similar past periods found.\n"]
    
    for i, ev in enumerate(similar_events):
        signal = "LOW"
        if ev['score'] >= 70: signal = "HIGH"
        elif ev['score'] >= 40: signal = "MEDIUM"
        
        lines.append(f"MATCH {i+1} (Score: {ev['score']}/100) — {ev['date']}")
        lines.append(f"Event: {ev['title']}")
        lines.append(f"Details: {ev['description']}")
        lines.append(f"Matching factors: {', '.join(ev['matches'])}")
        lines.append(f"Past outcome: {ev['outcome']}")
        lines.append(f"Past emotion: {ev['emotion_score']}")
        lines.append(f"Pattern signal: {signal} SIMILARITY\n")
        
    return "\n".join(lines)
