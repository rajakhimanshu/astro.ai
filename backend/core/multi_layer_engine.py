"""
core/multi_layer_engine.py
────────────────────────────────────────────────────────────────────────
12-LAYER JYOTISH ENGINE — Complete Multi-Layer Vedic Astrology Analysis
Dynamic version without hardcoded user profiles.
────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime
from core.astro_engine import get_current_sky, calculate_all_dignities, SIGNS
from core.ashtakavarga import calculate_ashtakavarga

SIGN_IDX = {s: i for i, s in enumerate(SIGNS)}

# All 27 Nakshatras and their ruling planets
NAKSHATRA_LORDS = {
    "Ashwini":          "Ketu",    "Bharani":          "Venus",   "Krittika":         "Sun",
    "Rohini":           "Moon",    "Mrigashira":       "Mars",    "Ardra":            "Rahu",
    "Punarvasu":        "Jupiter", "Pushya":           "Saturn",  "Ashlesha":         "Mercury",
    "Magha":            "Ketu",    "Purva Phalguni":   "Venus",   "Uttara Phalguni":  "Sun",
    "Hasta":            "Moon",    "Chitra":           "Mars",    "Swati":            "Rahu",
    "Vishakha":         "Jupiter", "Anuradha":         "Saturn",  "Jyeshtha":         "Mercury",
    "Mula":             "Ketu",    "Purva Ashadha":    "Venus",   "Uttara Ashadha":   "Sun",
    "Shravana":         "Moon",    "Dhanishtha":       "Mars",    "Dhanishta":        "Mars",
    "Shatabhisha":      "Rahu",    "Purva Bhadrapada": "Jupiter", "Uttara Bhadrapada":"Saturn",
    "Revati":           "Mercury",
}

NAKSHATRA_SEQUENCE = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Panchanga tables
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
]
VARA_LORDS = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter", 5: "Venus", 6: "Saturn"}
VARA_NAMES = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]
KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja",
    "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

SPECIAL_ASPECTS = {
    "mars":    [4, 8],
    "jupiter": [5, 9],
    "saturn":  [3, 10],
    "rahu":    [5, 9],
    "ketu":    [5, 9],
}

KENDRA    = {1, 4, 7, 10}
TRIKONA   = {1, 5, 9}
UPACHAYA  = {3, 6, 10, 11}
DUSTHANA  = {6, 8, 12}
MARAKA    = {2, 7}

SIGN_MAP = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
    "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
    "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces"
}

def _house_type_label(h: int) -> str:
    types = []
    if h in KENDRA:   types.append("Kendra")
    if h in TRIKONA:  types.append("Trikona")
    if h in UPACHAYA: types.append("Upachaya")
    if h in DUSTHANA: types.append("Dusthana")
    if h in MARAKA:   types.append("Maraka")
    return "+".join(types) if types else "Neutral"

# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — Natal Aspects (Drishti)
# ─────────────────────────────────────────────────────────────────────────────

def get_natal_aspects(subject) -> str:
    """Layer 2: All natal planet-to-planet aspects."""
    m = subject.model()
    lagna_sign_raw = m.ascendant.sign
    lagna_sign = SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw)
    lagna_idx = SIGNS.index(SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw))
    
    planets_keys = {
        'sun': 'sun', 'moon': 'moon', 'mercury': 'mercury', 'venus': 'venus', 
        'mars': 'mars', 'jupiter': 'jupiter', 'saturn': 'saturn',
        'true_north_lunar_node': 'rahu', 'true_south_lunar_node': 'ketu'
    }
    
    house_planets = {}
    planet_house = {}
    
    for key, name in planets_keys.items():
        p = getattr(m, key)
        p_sign_raw = p.sign
        p_sign = SIGN_MAP.get(p_sign_raw, p_sign_raw)
        p_idx = SIGNS.index(SIGN_MAP.get(p_sign, p_sign))
        house = (p_idx - lagna_idx + 12) % 12 + 1
        planet_house[name] = house
        house_planets.setdefault(house, []).append(name.capitalize())

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 2 — NATAL ASPECTS (DRISHTI)",
        "═══ Every planet's 7th aspect + special aspects of Mars/Jupiter/Saturn ═══",
        "",
    ]

    for name in planets_keys.values():
        h = planet_house[name]
        aspects = []

        # Universal 7th aspect
        t7 = (h - 1 + 6) % 12 + 1
        planets_in_t7 = house_planets.get(t7, [])
        occ7 = ", ".join(planets_in_t7) if planets_in_t7 else "empty"
        aspects.append(f"7th→H{t7}({occ7})")

        # Special aspects
        for offset in SPECIAL_ASPECTS.get(name, []):
            target = (h - 1 + offset - 1) % 12 + 1
            occ = ", ".join(house_planets.get(target, [])) or "empty"
            aspects.append(f"{offset}th→H{target}({occ})")

        line = f"  {name.capitalize():8} [H{h}] → {' | '.join(aspects)}"
        lines.append(line)

    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — House Lordship Analysis
# ─────────────────────────────────────────────────────────────────────────────

def get_lord_analysis(subject) -> str:
    """Layer 3: Dynamic Lordship Analysis."""
    m = subject.model()
    lagna_sign_raw = m.ascendant.sign
    lagna_sign = SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw)
    lagna_idx = SIGNS.index(SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw))
    
    dignities = calculate_all_dignities(subject)
    
    SIGN_LORDS = {
        "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
        "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
        "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter"
    }

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 3 — HOUSE LORDSHIP ANALYSIS",
        "═══ The most important Jyotish concept: where does each lord sit? ═══",
        "",
        f"  {'H#':4} {'House Sign':14} {'H-Type':22} {'Lord':10} {'→ Sits In':10} {'Lord Sign':14} {'Lord Dignity':14} {'To-H Type'}",
        "  " + "─" * 105,
    ]

    for h in range(1, 13):
        sign_idx = (lagna_idx + h - 1) % 12
        house_sign = SIGNS[sign_idx]
        h_type = _house_type_label(h)
        lord = SIGN_LORDS[house_sign]
        
        lord_data = dignities.get(lord, {})
        lord_h = lord_data.get('house', '?')
        
        # Handle string house names if any
        if isinstance(lord_h, str):
            house_map = {
                "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
                "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
                "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12
            }
            lord_h = house_map.get(lord_h, '?')
            
        if lord_h == '?':
            # recalculate dynamically
            p_sign_raw = getattr(m, lord).sign
            p_sign = SIGN_MAP.get(p_sign_raw, p_sign_raw)
            p_idx = SIGNS.index(SIGN_MAP.get(p_sign, p_sign))
            lord_h = (p_idx - lagna_idx + 12) % 12 + 1
            
        lord_sign_raw = getattr(m, lord).sign
        lord_sign = SIGN_MAP.get(lord_sign_raw, lord_sign_raw)
        dignity = lord_data.get('dignity', '?')
        to_type = _house_type_label(lord_h) if isinstance(lord_h, int) else "?"
        
        lines.append(
            f"  H{h:<3} {house_sign:14} {h_type:22} {lord.capitalize():10} H{lord_h:<9} {lord_sign:14} {dignity:14} {to_type}"
        )

    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5 — Nakshatra Lord Chain (Sublord System)
# ─────────────────────────────────────────────────────────────────────────────

def get_nakshatra_chain_analysis(subject) -> str:
    """Layer 5: Nakshatra Lord Chain dynamically."""
    m = subject.model()
    lagna_sign_raw = m.ascendant.sign
    lagna_sign = SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw)
    lagna_idx = SIGNS.index(SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw))
    
    dignities = calculate_all_dignities(subject)
    
    planets_keys = {
        'sun': 'sun', 'moon': 'moon', 'mercury': 'mercury', 'venus': 'venus', 
        'mars': 'mars', 'jupiter': 'jupiter', 'saturn': 'saturn',
        'true_north_lunar_node': 'rahu', 'true_south_lunar_node': 'ketu'
    }

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 5 — NAKSHATRA LORD CHAIN (Sublord / Planet-Sign-Nakshatra Triplet)",
        "═══ Nakshatra lord acts as sub-ruler; filters the planet's expression ═══",
        "",
        f"  {'Planet':10} {'H':3} {'Sign':14} {'Nakshatra':22} {'Nak Lord':10} {'Lord→H':8} {'Lord Dignity'}",
        "  " + "─" * 90,
    ]

    for key, name in planets_keys.items():
        p = getattr(m, key)
        abs_pos = float(p.abs_pos)
        nak_idx = int(abs_pos / (360 / 27)) % 27
        nak = NAKSHATRA_SEQUENCE[nak_idx]
        nak_lord = NAKSHATRA_LORDS.get(nak, "?")
        
        p_sign_raw = p.sign
        p_sign = SIGN_MAP.get(p_sign_raw, p_sign_raw)
        p_idx = SIGNS.index(SIGN_MAP.get(p_sign, p_sign))
        house = (p_idx - lagna_idx + 12) % 12 + 1
        
        lord_data = dignities.get(nak_lord.lower(), {})
        lord_h = lord_data.get('house', '?')
        if isinstance(lord_h, str):
            house_map = {
                "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
                "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
                "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12
            }
            lord_h = house_map.get(lord_h, '?')
            
        if lord_h == '?':
            if nak_lord.lower() in planets_keys.values():
                nl_p = getattr(m, [k for k, v in planets_keys.items() if v == nak_lord.lower()][0])
                nl_sign_raw = nl_p.sign
                nl_sign = SIGN_MAP.get(nl_sign_raw, nl_sign_raw)
                nl_idx = SIGNS.index(SIGN_MAP.get(nl_sign, nl_sign))
                lord_h = (nl_idx - lagna_idx + 12) % 12 + 1
        
        dignity = lord_data.get('dignity', '?')

        lines.append(
            f"  {name.capitalize():10} H{house:<2} {p_sign:14} {nak:22} {nak_lord:10} H{lord_h:<7} {dignity}"
        )

    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 11 — Panchanga (Current Celestial Time Quality)
# ─────────────────────────────────────────────────────────────────────────────

def get_current_panchanga(subject=None) -> str:
    """Layer 11: Compute the 5 Panchanga elements for right now."""
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 11 — PANCHANGA (MUHURTA / CURRENT CELESTIAL TIME QUALITY)",
        "═══ The 5 elements of Vedic time — for all timing recommendations ═══",
        "",
    ]

    try:
        sky = get_current_sky()
        m   = sky.model()
        now = datetime.now()

        sun_lon  = m.sun.abs_pos
        moon_lon = m.moon.abs_pos

        tithi_deg  = (moon_lon - sun_lon) % 360
        tithi_num  = int(tithi_deg / 12) + 1
        paksha     = "Shukla (Waxing)" if tithi_num <= 15 else "Krishna (Waning)"
        tithi_name = TITHI_NAMES[(tithi_num - 1) % 15]

        py_day   = now.weekday()
        vara_idx = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}[py_day]
        vara_lord = VARA_LORDS[vara_idx]
        vara_name = VARA_NAMES[vara_idx]

        nak_idx     = int(moon_lon / (360 / 27)) % 27
        current_nak = NAKSHATRA_SEQUENCE[nak_idx]
        nak_lord    = NAKSHATRA_LORDS.get(current_nak, "?")
        moon_sign   = SIGNS[int(moon_lon // 30) % 12]

        yoga_deg  = (sun_lon + moon_lon) % 360
        yoga_idx  = int(yoga_deg / (360 / 27)) % 27
        yoga_name = YOGA_NAMES[yoga_idx]

        karana_idx  = int(tithi_deg / 6) % 11
        karana_name = KARANA_NAMES[karana_idx]

        lines += [
            f"  Current: {now.strftime('%A, %d %B %Y | %H:%M IST')}",
            "",
            f"  ┌─ PANCHANGA ────────────────────────────────────────────────────────┐",
            f"  │ 1. TITHI:     {tithi_name} (#{tithi_num}) — {paksha}",
            f"  │ 2. VARA:      {vara_name} — Day Lord: {vara_lord}",
            f"  │ 3. NAKSHATRA: Moon in {current_nak} ({moon_sign}) — Nak Lord: {nak_lord}",
            f"  │ 4. YOGA:      {yoga_name} (Sun+Moon combination quality)",
            f"  │ 5. KARANA:    {karana_name} (half-tithi quality)",
            f"  └────────────────────────────────────────────────────────────────────┘",
            "",
        ]
    except Exception as e:
        lines.append(f"  [Panchanga Error: {e}]")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 12 — Prashna / Horary (Chart for the Moment of Asking)
# ─────────────────────────────────────────────────────────────────────────────

def get_prashna_context(subject) -> str:
    """Layer 12: Prashna Context relative to Natal."""
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 12 — PRASHNA (HORARY — MOMENT-OF-ASKING CHART)",
        "═══ The chart at this exact moment reveals the nature of the question ═══",
        "",
    ]

    try:
        sky = get_current_sky()
        m_sky   = sky.model()
        now = datetime.now()
        
        m_natal = subject.model()
        lagna_sign_raw = m_natal.ascendant.sign
        lagna_sign = SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw)
        lagna_idx = SIGNS.index(SIGN_MAP.get(lagna_sign_raw, lagna_sign_raw))

        moon_lon = m_sky.moon.abs_pos
        moon_sign_i = int(moon_lon // 30) % 12
        moon_sign   = SIGNS[moon_sign_i]
        moon_deg    = round(moon_lon % 30, 2)
        prashna_nak = NAKSHATRA_SEQUENCE[int(moon_lon / (360/27)) % 27]
        prashna_nl  = NAKSHATRA_LORDS.get(prashna_nak, "?")

        try:
            asc_lon  = m_sky.ascendant.abs_pos
            asc_sign = SIGNS[int(asc_lon // 30) % 12]
            asc_deg  = round(asc_lon % 30, 2)
        except Exception:
            asc_sign, asc_deg = "Unavailable", 0.0

        pra_moon_h  = (moon_sign_i - lagna_idx + 12) % 12 + 1

        lines += [
            f"  Question asked at: {now.strftime('%A, %d %B %Y | %H:%M IST')}",
            "",
            f"  Prashna Lagna (Rising now): {asc_sign} {asc_deg}°",
            f"  Prashna Moon:              {moon_sign} {moon_deg}° → Transiting your H{pra_moon_h}",
            f"  Prashna Nakshatra:         {prashna_nak} (Lord: {prashna_nl})",
            "",
            f"  ┌─ PRASHNA INTERPRETATION GUIDE ─────────────────────────────────────┐",
            f"  │ 1. Prashna Moon in H{pra_moon_h} of natal chart: The question involves H{pra_moon_h} themes",
            f"  │ 2. Nak Lord {prashna_nl}: Outcome is filtered through {prashna_nl}'s domain",
            f"  │",
            f"  │ CURRENT PRASHNA STATE:",
            f"  │   Moon in {prashna_nak} ({prashna_nl}-ruled) transiting H{pra_moon_h}:",
            f"  │   Question nature = H{pra_moon_h} domain, answer quality = {prashna_nl}'s strength",
            f"  └──────────────────────────────────────────────────────────────────────┘",
            "",
        ]

    except Exception as e:
        lines.append(f"  [Prashna Error: {e}]")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 13 — Convergence & Confidence (Multi-Varga Strength)
# ─────────────────────────────────────────────────────────────────────────────

DIGNITY_WEIGHT = {
    "Exalted": 5, "Moolatrikona": 4, "Own Sign": 4,
    "Great Friend": 3, "Friend": 2, "Neutral": 1,
    "Enemy": 0, "Great Enemy": -1, "Debilitated": -2,
    "Friendly": 2, "Great_Friend": 3, "Great_Enemy": -1 # mapped variants
}

def get_convergence_analysis(subject) -> str:
    """Layer 13: Convergence across D1, D9, D10, D60."""
    from core.astro_engine import calculate_varga_position, calculate_planet_dignity, calculate_all_dignities
    
    m = subject.model()
    planets_keys = {
        'sun': 'sun', 'moon': 'moon', 'mercury': 'mercury', 'venus': 'venus', 
        'mars': 'mars', 'jupiter': 'jupiter', 'saturn': 'saturn',
        'true_north_lunar_node': 'rahu', 'true_south_lunar_node': 'ketu'
    }
    
    d1_dignities = calculate_all_dignities(subject)
    vargas = [9, 10, 60]
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 13 — CONVERGENCE & CONFIDENCE (MULTI-VARGA STRENGTH)",
        "═══ Average strength across D1, D9, D10, D60 charts ═══",
        "",
        f"  {'Planet':10} {'D1':12} {'D9':12} {'D10':12} {'D60':12} {'Score':6} {'Verdict'}",
        "  " + "─" * 90,
    ]
    
    for key, name in planets_keys.items():
        p = getattr(m, key)
        p_dignities = []
        
        # D1
        d1_dig = d1_dignities[name]['dignity']
        p_dignities.append(d1_dig)
        
        # Others
        for n in vargas:
            v_pos = calculate_varga_position(p.abs_pos, n)
            v_dig = calculate_planet_dignity(name, v_pos['sign'], v_pos['degree_in_varga'])['dignity']
            p_dignities.append(v_dig)
            
        scores = [DIGNITY_WEIGHT.get(d, 1) for d in p_dignities]
        avg = sum(scores) / len(scores)
        
        if avg >= 3.5:   verdict = "STRONG"
        elif avg >= 2.0: verdict = "MIXED"
        elif avg >= 0.5: verdict = "WEAK"
        else:            verdict = "VERY WEAK"
        
        lines.append(
            f"  {name.capitalize():10} {p_dignities[0]:12} {p_dignities[1]:12} {p_dignities[2]:12} {p_dignities[3]:12} {avg:<6.2f} {verdict}"
        )
        
    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# MASTER FUNCTION — Combine All Missing Layers into One Context Block
# ─────────────────────────────────────────────────────────────────────────────

def get_all_12_layers(subject) -> str:
    """
    Returns the complete multi-layer Jyotish analysis as one text block dynamically.
    Covers Layers 2, 3, 5, 11, 12, 13.
    """
    header = """
╔══════════════════════════════════════════════════════════════════════════════╗
║        MULTI-LAYER ANALYSIS ENGINE — LAYERS 2, 3, 5, 11, 12, 13             ║
║   Per multi.txt: A master astrologer holds all layers simultaneously.       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    sections = [header]

    runners = [
        ("Layer 2 — Natal Aspects",          get_natal_aspects),
        ("Layer 3 — House Lordships",         get_lord_analysis),
        ("Layer 5 — Nakshatra Lord Chain",    get_nakshatra_chain_analysis),
        ("Layer 11 — Panchanga/Muhurta",      get_current_panchanga),
        ("Layer 12 — Prashna/Horary",         get_prashna_context),
        ("Layer 13 — Convergence Score",      get_convergence_analysis),
    ]

    for label, fn in runners:
        try:
            if fn == get_current_panchanga:
                sections.append(fn())
            else:
                sections.append(fn(subject))
        except Exception as e:
            sections.append(f"\n[{label} ERROR: {e}]\n")

    return "\n".join(sections)
