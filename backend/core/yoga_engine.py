import json
try:
    from core.astro_engine import calculate_all_dignities, calculate_planet_dignity, SIGNS
except ImportError:
    from backend.core.astro_engine import calculate_all_dignities, calculate_planet_dignity, SIGNS

# Standard Sign Lords
SIGN_LORDS = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
    "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
    "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter"
}

def get_house_lord(house_num, lagna_sign_idx):
    """Finds the lord of a given house number (1-12)."""
    sign_idx = (lagna_sign_idx + house_num - 1) % 12
    sign_name = SIGNS[sign_idx]
    return SIGN_LORDS[sign_name]

def are_connected(p1_name, p1_house, p2_name, p2_house, dignities):
    """Checks if two planets are connected via conjunction, mutual aspect, or exchange."""
    # 1. Conjunction
    if p1_house == p2_house:
        return "Conjunction"
    
    # 2. Mutual Aspect
    if is_aspecting(p1_name, p1_house, p2_house) and is_aspecting(p2_name, p2_house, p1_house):
        return "Mutual Aspect"
    
    # 3. Exchange (Parivartana)
    # We need to know which houses these planets rule
    # This logic is more complex as planets rule two houses. 
    # For simplicity, we'll focus on Conjunction and Mutual Aspect for now, 
    # or handle exchange separately in the specific yoga detector.
    
    return None

def is_aspecting(p_name, p_house, target_house):
    """Checks if a planet is aspecting a target house (Whole Sign)."""
    diff = (target_house - p_house + 12) % 12
    
    # All planets aspect the 7th
    if diff == 6: return True
    
    # Special aspects
    if p_name == "mars" and diff in [3, 7]: return True # 4th, 8th
    if p_name == "jupiter" and diff in [4, 8]: return True # 5th, 9th
    if p_name == "saturn" and diff in [2, 9]: return True # 3rd, 10th
    if p_name in ["rahu", "ketu"] and diff in [4, 8]: return True # 5th, 9th (standard Vedic)
    
    return False

SIGN_MAP = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
    "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
    "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces"
}

def detect_all_yogas(subject):
    """Main function to detect all supported yogas."""
    m = subject.model()
    dignities = calculate_all_dignities(subject)
    
    # Setup data
    lagna_sign_raw = m.ascendant.sign
    lagna_sign = SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw)
    lagna_idx = SIGNS.index(lagna_sign)
    
    house_map = {
        "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
        "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
        "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12
    }
    
    planet_positions = {}
    for name, data in dignities.items():
        h = data['house']
        if isinstance(h, str): h = house_map.get(h, 0)
        planet_positions[name] = h

    # House Lords map
    house_lords = {h: get_house_lord(h, lagna_idx) for h in range(1, 13)}
    
    yogas = {
        "raj_yogas": [],
        "dhana_yogas": [],
        "special_yogas": []
    }

    # 1. RAJ YOGAS (Kendra 1,4,7,10 & Trikona 1,5,9)
    kendras = [1, 4, 7, 10]
    trikonas = [1, 5, 9]
    
    seen_raj = set()
    for k in kendras:
        for t in trikonas:
            l1 = house_lords[k]
            l2 = house_lords[t]
            if l1 == l2: continue # Same planet (Lagna lord)
            
            conn = are_connected(l1, planet_positions[l1], l2, planet_positions[l2], dignities)
            if conn:
                pair = tuple(sorted([l1, l2]))
                if pair not in seen_raj:
                    yogas["raj_yogas"].append({
                        "name": "Raj Yoga",
                        "planets": [l1.capitalize(), l2.capitalize()],
                        "details": f"{l1.capitalize()} (lord of {k}) and {l2.capitalize()} (lord of {t}) in {conn}",
                        "description": "Powerful yoga for status, authority, and success."
                    })
                    seen_raj.add(pair)

    # 2. DHANA YOGAS (2, 5, 9, 11)
    dhana_houses = [2, 5, 9, 11]
    for i in range(len(dhana_houses)):
        for j in range(i + 1, len(dhana_houses)):
            l1 = house_lords[dhana_houses[i]]
            l2 = house_lords[dhana_houses[j]]
            if l1 == l2: continue
            
            conn = are_connected(l1, planet_positions[l1], l2, planet_positions[l2], dignities)
            if conn:
                yogas["dhana_yogas"].append({
                    "name": "Dhana Yoga",
                    "planets": [l1.capitalize(), l2.capitalize()],
                    "details": f"Wealth lords {l1.capitalize()} ({dhana_houses[i]}) and {l2.capitalize()} ({dhana_houses[j]}) in {conn}",
                    "description": "Yoga for financial prosperity and accumulation of wealth."
                })

    # 3. GAJA KESARI YOGA
    moon_house = planet_positions['moon']
    jupiter_house = planet_positions['jupiter']
    dist = (jupiter_house - moon_house + 12) % 12 + 1
    if dist in [1, 4, 7, 10]:
        yogas["special_yogas"].append({
            "name": "Gaja Kesari Yoga",
            "planets": ["Moon", "Jupiter"],
            "details": f"Jupiter is in House {dist} from Moon",
            "description": "Indicates wisdom, fame, and respected position."
        })

    # 4. BUDHA ADITYA YOGA
    if planet_positions['sun'] == planet_positions['mercury']:
        yogas["special_yogas"].append({
            "name": "Budha Aditya Yoga",
            "planets": ["Sun", "Mercury"],
            "details": "Sun and Mercury are conjunct",
            "description": "Indicates intelligence, communication skills, and professional expertise."
        })

    # 5. CHANDRA MANGALA YOGA
    conn = are_connected("moon", planet_positions['moon'], "mars", planet_positions['mars'], dignities)
    if conn:
        yogas["special_yogas"].append({
            "name": "Chandra Mangala Yoga",
            "planets": ["Moon", "Mars"],
            "details": f"Moon and Mars in {conn}",
            "description": "Indicates energy, earnings through effort, and emotional intensity."
        })

    # 6. VIPARITA RAJ YOGA
    dusthanas = [6, 8, 12]
    for h in dusthanas:
        lord = house_lords[h]
        lord_house = planet_positions[lord]
        if lord_house in dusthanas:
            yogas["special_yogas"].append({
                "name": "Viparita Raj Yoga",
                "planets": [lord.capitalize()],
                "details": f"{h}th lord {lord.capitalize()} in {lord_house}th house (Dusthana)",
                "description": "Success through challenges, unexpected rise, or gains from others' losses."
            })

    # 7. PANCHA MAHAPURUSHA YOGAS
    # Planet in Own/Exalted in Kendra (1,4,7,10)
    mahadasha_planets = {
        "mars": "Ruchaka Yoga",
        "mercury": "Bhadra Yoga",
        "jupiter": "Hamsa Yoga",
        "venus": "Malavya Yoga",
        "saturn": "Sasa Yoga"
    }
    for p_name, y_name in mahadasha_planets.items():
        if planet_positions[p_name] in kendras:
            d = dignities[p_name]
            if d['dignity'] in ["Exalted", "Own Sign", "Moolatrikona"]:
                yogas["special_yogas"].append({
                    "name": y_name,
                    "planets": [p_name.capitalize()],
                    "details": f"{p_name.capitalize()} is {d['dignity']} in Kendra house {planet_positions[p_name]}",
                    "description": f"One of the five great planetary combinations for {p_name.capitalize()}."
                })

    # 8. NEECHA BHANGA RAJ YOGA
    # Standard rules for cancellation of debilitation
    DEBIL_IN = {"sun": 6, "moon": 7, "mars": 3, "mercury": 11, "jupiter": 9, "venus": 5, "saturn": 0}
    EXALT_IN = {"sun": 0, "moon": 1, "mars": 9, "mercury": 5, "jupiter": 3, "venus": 11, "saturn": 6}
    
    for p_name, s_idx in [(p, dignities[p]['sign']) for p in DEBIL_IN.keys()]:
        # Normalize sign name (handle abbreviations like 'Ari')
        full_sign_name = SIGN_MAP.get(s_idx, s_idx)
        try:
            p_si = SIGNS.index(full_sign_name)
        except ValueError:
            continue # Skip if sign not found
            
        if p_si == DEBIL_IN[p_name]:
            # Rule 1: Lord of debilitation sign is in Kendra from Asc or Moon
            debil_lord = SIGN_LORDS[s_idx]
            dl_house = planet_positions[debil_lord]
            
            dist_asc = (dl_house - 1 + 12) % 12
            dist_moon = (dl_house - moon_house + 12) % 12
            
            if dist_asc in [0, 3, 6, 9] or dist_moon in [0, 3, 6, 9]:
                yogas["special_yogas"].append({
                    "name": "Neecha Bhanga Raj Yoga",
                    "planets": [p_name.capitalize()],
                    "details": f"Debilitation of {p_name.capitalize()} cancelled by its sign lord {debil_lord.capitalize()} in Kendra",
                    "description": "Indicates overcoming obstacles to achieve great success."
                })
                continue
            
            # Rule 2: Exaltation lord of the sign is in Kendra from Asc or Moon
            exalt_lord_name = SIGN_LORDS[SIGNS[EXALT_IN[p_name]]]
            el_house = planet_positions[exalt_lord_name]
            dist_asc_el = (el_house - 1 + 12) % 12
            dist_moon_el = (el_house - moon_house + 12) % 12
            
            if dist_asc_el in [0, 3, 6, 9] or dist_moon_el in [0, 3, 6, 9]:
                yogas["special_yogas"].append({
                    "name": "Neecha Bhanga Raj Yoga",
                    "planets": [p_name.capitalize()],
                    "details": f"Debilitation of {p_name.capitalize()} cancelled by exaltation lord in Kendra",
                    "description": "Indicates transformation of weakness into power."
                })

    # 9. KALA SARPA YOGA (Simplified)
    rahu_house = planet_positions['rahu']
    ketu_house = planet_positions['ketu']
    # Check if all other 7 planets are between Rahu and Ketu
    # (This is a bit more involved to check the arc, skip for now or implement simply)
    
    return yogas

def format_yogas_for_ai(yoga_results):
    """Formats the detected yogas for the LLM context."""
    lines = ["ACTIVE YOGAS IN BIRTH CHART:"]
    
    total = len(yoga_results["raj_yogas"]) + len(yoga_results["dhana_yogas"]) + len(yoga_results["special_yogas"])
    if total == 0:
        return "ACTIVE YOGAS IN BIRTH CHART: None detected."
        
    for y in yoga_results["raj_yogas"]:
        lines.append(f"- {y['name']}: {y['details']}")
        lines.append(f"  Result: {y['description']}")
        
    for y in yoga_results["dhana_yogas"]:
        lines.append(f"- {y['name']}: {y['details']}")
        lines.append(f"  Result: {y['description']}")
        
    for y in yoga_results["special_yogas"]:
        lines.append(f"- {y['name']}: {y['details']}")
        lines.append(f"  Result: {y['description']}")
        
    return "\n".join(lines)
