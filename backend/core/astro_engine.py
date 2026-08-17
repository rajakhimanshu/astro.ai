from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import yaml
import os
from dotenv import load_dotenv

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", 
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

def datetime_to_jd(dt, lon=0.0):
    """Converts a datetime object to Julian Day number using Swiss Ephemeris."""
    import swisseph as swe
    hour = dt.hour + dt.minute/60.0 + dt.second/3600.0
    return swe.julday(dt.year, dt.month, dt.day, hour)

def get_nakshatra_and_pada(abs_pos):
    """Calculates Nakshatra and Pada from absolute position (0-360)."""
    total_minutes = round(abs_pos * 60)
    nak_idx = (total_minutes // 800) % 27
    pada = ((total_minutes % 800) // 200) + 1
    return NAKSHATRAS[nak_idx], int(pada)

def get_divisional_chart(subject, division):
    """
    Calculates divisional chart (Varga) positions for planets and Lagna.
    Supported divisions: 9 (Navamsha), 10 (Dashamsha)
    Calculates based on BPHS rules.
    """
    m = subject.model()
    planets_keys = {
        'sun': 'sun', 'moon': 'moon', 'mercury': 'mercury', 'venus': 'venus', 
        'mars': 'mars', 'jupiter': 'jupiter', 'saturn': 'saturn',
        'true_north_lunar_node': 'rahu', 'true_south_lunar_node': 'ketu'
    }
    
    div_chart = {}
    
    # Process planets
    for key, name in planets_keys.items():
        p = getattr(m, key)
        div_chart[name] = calculate_varga_position(p.abs_pos, division)
        
    # Process Lagna
    div_chart['lagna'] = calculate_varga_position(m.ascendant.abs_pos, division)
    
    return div_chart

def calculate_varga_position(abs_pos, n):
    """
    Calculates the sign and position for any divisional chart (Varga).
    Implements standard BPHS (Brihat Parashara Hora Shastra) rules.
    """
    sign_idx = int(abs_pos // 30)
    pos_in_sign = abs_pos % 30
    
    res_sign_idx = 0
    
    if n == 1: # Rashi
        res_sign_idx = sign_idx
        
    elif n == 2: # Hora (2 parts)
        # Odd signs: 0-15 Sun (Leo), 15-30 Moon (Cancer)
        # Even signs: 0-15 Moon (Cancer), 15-30 Sun (Leo)
        is_odd = sign_idx % 2 == 0 # 0=Aries (Odd)
        if is_odd:
            res_sign_idx = 4 if pos_in_sign < 15 else 3 # Leo if 1st half, else Cancer
        else:
            res_sign_idx = 3 if pos_in_sign < 15 else 4 # Cancer if 1st half, else Leo
            
    elif n == 3: # Drekkana (3 parts)
        # 1st part: Same sign, 2nd: 5th from it, 3rd: 9th from it
        part = int(pos_in_sign // 10)
        res_sign_idx = (sign_idx + (part * 4)) % 12
        
    elif n == 4: # Chaturthamsa (4 parts)
        # 1, 4, 7, 10 from the sign
        part = int(pos_in_sign // 7.5)
        res_sign_idx = (sign_idx + (part * 3)) % 12
        
    elif n == 7: # Saptamsha (7 parts)
        # Odd: Start from sign, Even: Start from 7th sign
        part = int(pos_in_sign // (30/7))
        start_sign = sign_idx if sign_idx % 2 == 0 else (sign_idx + 6) % 12
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 9: # Navamsha (9 parts)
        # Fire: Aries, Earth: Cap, Air: Libra, Water: Cancer
        start_signs = [0, 9, 6, 3, 0, 9, 6, 3, 0, 9, 6, 3]
        start_sign = start_signs[sign_idx]
        part = int(pos_in_sign // (30/9))
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 10: # Dashamsha (10 parts)
        # Odd: Sign itself, Even: 9th from it
        start_sign = sign_idx if sign_idx % 2 == 0 else (sign_idx + 8) % 12
        part = int(pos_in_sign // 3)
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 12: # Dwadashamsha (12 parts)
        # Start from sign itself
        part = int(pos_in_sign // 2.5)
        res_sign_idx = (sign_idx + part) % 12
        
    elif n == 16: # Shodashamsha (16 parts)
        # Movable: Aries, Fixed: Leo, Dual: Sag
        starts = [0, 4, 8] # Aries, Leo, Sag
        start_sign = starts[sign_idx % 3]
        part = int(pos_in_sign // (30/16))
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 20: # Vimshamsha (20 parts)
        # Movable: Aries, Fixed: Sag, Dual: Leo
        starts = [0, 8, 4] # Aries, Sag, Leo
        start_sign = starts[sign_idx % 3]
        part = int(pos_in_sign // 1.5)
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 24: # Chaturvimshamsha (24 parts)
        # Odd: Leo, Even: Cancer (Wait, BPHS standard is Odd: Leo, Even: Cancer)
        start_sign = 4 if sign_idx % 2 == 0 else 3
        part = int(pos_in_sign // 1.25)
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 27: # Sapta-vimshamsha (Nakshatramsa)
        # Same logic as D9 but 27 parts
        start_signs = [0, 9, 6, 3, 0, 9, 6, 3, 0, 9, 6, 3]
        start_sign = start_signs[sign_idx]
        part = int(pos_in_sign // (30/27))
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 30: # Trimshamsha (30 parts)
        # Odd: 5 deg each for Mars, Sat, Jup, Mer, Ven
        # Even: 5 deg each for Ven, Mer, Jup, Sat, Mars
        if sign_idx % 2 == 0: # Odd
            if pos_in_sign < 5: res_sign_idx = 0 # Aries (Mars)
            elif pos_in_sign < 10: res_sign_idx = 10 # Aquarius (Sat)
            elif pos_in_sign < 18: res_sign_idx = 8 # Sag (Jup)
            elif pos_in_sign < 25: res_sign_idx = 2 # Gemini (Mer)
            else: res_sign_idx = 6 # Libra (Ven)
        else: # Even
            if pos_in_sign < 5: res_sign_idx = 1 # Taurus (Ven)
            elif pos_in_sign < 12: res_sign_idx = 5 # Virgo (Mer)
            elif pos_in_sign < 20: res_sign_idx = 11 # Pisces (Jup)
            elif pos_in_sign < 25: res_sign_idx = 9 # Cap (Sat)
            else: res_sign_idx = 7 # Scorpio (Mars)
            
    elif n == 40: # Khavedamsha (40 parts)
        # Odd: Aries, Even: Libra
        start_sign = 0 if sign_idx % 2 == 0 else 6
        part = int(pos_in_sign // 0.75)
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 45: # Akshavedamsha (45 parts)
        # Movable: Aries, Fixed: Leo, Dual: Sag
        starts = [0, 4, 8]
        start_sign = starts[sign_idx % 3]
        part = int(pos_in_sign // (30/45))
        res_sign_idx = (start_sign + part) % 12
        
    elif n == 60: # Shashtyamsha (60 parts)
        # Start from sign itself
        part = int(pos_in_sign // 0.5)
        res_sign_idx = (sign_idx + part) % 12
        
    else:
        # Generic fallback
        signs_to_advance = int(pos_in_sign * n // 30)
        res_sign_idx = (sign_idx * n + signs_to_advance) % 12

    res_sign = SIGNS[res_sign_idx % 12]
    return {
        "sign": res_sign,
        "sign_idx": res_sign_idx % 12,
        "degree_in_varga": round((pos_in_sign * n) % 30, 2)
    }

def get_d9_navamsa(subject):
    return get_divisional_chart(subject, 9)

def get_d10_dashamsa(subject):
    return get_divisional_chart(subject, 10)

def format_divisional_for_ai(div_chart, div_name):
    """Formats divisional chart for LLM context."""
    lines = [f"{div_name.upper()} CHART:"]
    
    # Sort to keep Lagna first, then others
    order = ['lagna', 'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
    
    lagna_sign_idx = div_chart['lagna']['sign_idx']
    
    for key in order:
        if key in div_chart:
            p = div_chart[key]
            # Calculate house relative to Varga Lagna (Whole Sign)
            house = (p['sign_idx'] - lagna_sign_idx + 12) % 12 + 1
            name = key.capitalize()
            lines.append(f"{name}: {p['sign']} (House {house})")
            
    return "\n".join(lines)

# --- PLANETARY STRENGTH & DIGNITY ---

# Natural Friendships in Vedic Astrology
PLANET_FRIENDS = {
    "sun": {"friends": ["moon", "mars", "jupiter"], "neutrals": ["mercury"], "enemies": ["venus", "saturn"]},
    "moon": {"friends": ["sun", "mercury"], "neutrals": ["mars", "jupiter", "venus", "saturn"], "enemies": []},
    "mars": {"friends": ["sun", "moon", "jupiter"], "neutrals": ["venus", "saturn"], "enemies": ["mercury"]},
    "mercury": {"friends": ["sun", "venus"], "neutrals": ["mars", "jupiter", "saturn"], "enemies": ["moon"]},
    "jupiter": {"friends": ["sun", "moon", "mars"], "neutrals": ["saturn"], "enemies": ["mercury", "venus"]},
    "venus": {"friends": ["mercury", "saturn"], "neutrals": ["mars", "jupiter"], "enemies": ["sun", "moon"]},
    "saturn": {"friends": ["mercury", "venus"], "neutrals": ["jupiter"], "enemies": ["sun", "moon", "mars"]},
    "rahu": {"friends": ["mercury", "venus", "saturn"], "neutrals": ["jupiter"], "enemies": ["sun", "moon", "mars"]},
    "ketu": {"friends": ["sun", "moon", "mars"], "neutrals": ["jupiter"], "enemies": ["mercury", "venus", "saturn"]}
}

def calculate_planet_dignity(planet, sign, degree):
    """Calculates the dignity and points for a planet based on sign and degree."""
    p = planet.lower()
    s = sign.capitalize()
    d = float(degree)
    
    # Dignity mappings
    dignity = "Neutral"
    points = 1
    
    if p == "sun":
        if s == "Aries":
            dignity = "Exalted"
            points = 5
        elif s == "Libra":
            dignity = "Debilitated"
            points = -3
        elif s == "Leo":
            if 0 <= d <= 20:
                dignity = "Moolatrikona"
                points = 3.5
            else:
                dignity = "Own Sign"
                points = 4
    
    elif p == "moon":
        if s == "Taurus":
            if 0 <= d <= 3:
                dignity = "Exalted"
                points = 5
            else:
                dignity = "Moolatrikona"
                points = 3.5
        elif s == "Scorpio":
            dignity = "Debilitated"
            points = -3
        elif s == "Cancer":
            dignity = "Own Sign"
            points = 4
            
    elif p == "mars":
        if s == "Capricorn":
            dignity = "Exalted"
            points = 5
        elif s == "Cancer":
            dignity = "Debilitated"
            points = -3
        elif s == "Aries":
            if 0 <= d <= 12:
                dignity = "Moolatrikona"
                points = 3.5
            else:
                dignity = "Own Sign"
                points = 4
        elif s == "Scorpio":
            dignity = "Own Sign"
            points = 4
            
    elif p == "mercury":
        if s == "Virgo":
            if 0 <= d <= 15:
                dignity = "Exalted"
                points = 5
            elif 16 <= d <= 20:
                dignity = "Moolatrikona"
                points = 3.5
            else:
                dignity = "Own Sign"
                points = 4
        elif s == "Pisces":
            dignity = "Debilitated"
            points = -3
        elif s == "Gemini":
            dignity = "Own Sign"
            points = 4
            
    elif p == "jupiter":
        if s == "Cancer":
            dignity = "Exalted"
            points = 5
        elif s == "Capricorn":
            dignity = "Debilitated"
            points = -3
        elif s == "Sagittarius":
            if 0 <= d <= 10:
                dignity = "Moolatrikona"
                points = 3.5
            else:
                dignity = "Own Sign"
                points = 4
        elif s == "Pisces":
            dignity = "Own Sign"
            points = 4
            
    elif p == "venus":
        if s == "Pisces":
            dignity = "Exalted"
            points = 5
        elif s == "Virgo":
            dignity = "Debilitated"
            points = -3
        elif s == "Libra":
            if 0 <= d <= 15:
                dignity = "Moolatrikona"
                points = 3.5
            else:
                dignity = "Own Sign"
                points = 4
        elif s == "Taurus":
            dignity = "Own Sign"
            points = 4
            
    elif p == "saturn":
        if s == "Libra":
            dignity = "Exalted"
            points = 5
        elif s == "Aries":
            dignity = "Debilitated"
            points = -3
        elif s == "Aquarius":
            if 0 <= d <= 20:
                dignity = "Moolatrikona"
                points = 3.5
            else:
                dignity = "Own Sign"
                points = 4
        elif s == "Capricorn":
            dignity = "Own Sign"
            points = 4
            
    elif p == "rahu":
        if s in ["Taurus", "Gemini"]:
            dignity = "Exalted"
            points = 5
        elif s in ["Scorpio", "Sagittarius"]:
            dignity = "Debilitated"
            points = -3
            
    elif p == "ketu":
        if s in ["Scorpio", "Sagittarius"]:
            dignity = "Exalted"
            points = 5
        elif s in ["Taurus", "Gemini"]:
            dignity = "Debilitated"
            points = -3

    # If dignity still neutral, check friendship
    if dignity == "Neutral":
        # We need to know who rules the current sign
        sign_lords = {
            "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
            "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
            "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter"
        }
        lord = sign_lords.get(s)
        if lord and p in PLANET_FRIENDS:
            rels = PLANET_FRIENDS[p]
            if lord in rels["friends"]:
                dignity = "Friendly"
                points = 2
            elif lord in rels["enemies"]:
                dignity = "Enemy"
                points = -1
                
    return {"dignity": dignity, "points": points}

def calculate_all_dignities(subject):
    """Calculates dignities, retro, and combustion for all planets."""
    m = subject.model()
    planets_keys = {
        'sun': 'sun', 'moon': 'moon', 'mercury': 'mercury', 'venus': 'venus', 
        'mars': 'mars', 'jupiter': 'jupiter', 'saturn': 'saturn',
        'true_north_lunar_node': 'rahu', 'true_south_lunar_node': 'ketu'
    }
    
    results = {}
    sun_pos = m.sun.abs_pos
    
    for key, name in planets_keys.items():
        p = getattr(m, key)
        dig_info = calculate_planet_dignity(name, p.sign, p.position)
        
        # Retrograde
        is_retro = p.retrograde
        
        # Combustion (distance from Sun)
        is_combust = False
        if name != "sun" and name not in ["rahu", "ketu"]:
            diff = abs(p.abs_pos - sun_pos)
            if diff > 180: diff = 360 - diff
            
            # Specific combustion orbs per user formula
            limit = 15.0 # default
            if name == "moon": limit = 12.0
            elif name == "mars": limit = 17.0
            elif name == "mercury": limit = 12.0 if is_retro else 14.0
            elif name == "jupiter": limit = 11.0
            elif name == "venus": limit = 8.0 if is_retro else 10.0
            elif name == "saturn": limit = 15.0
            
            if diff <= limit:
                is_combust = True
                dig_info["points"] -= 2 # Penalty for combustion
        
        results[name] = {
            "dignity": dig_info["dignity"],
            "points": dig_info["points"],
            "sign": p.sign,
            "house": p.house,
            "is_retrograde": is_retro,
            "is_combust": is_combust
        }
        
    return results

def get_strength_summary(subject):
    """Returns human readable strength summary for LLM context."""
    dignities = calculate_all_dignities(subject)
    lines = ["PLANETARY STRENGTH SUMMARY:"]
    
    # Define house map locally just in case
    house_map = {
        "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
        "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
        "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12
    }
    
    order = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    for name in order:
        if name in dignities:
            d = dignities[name]
            h_val = d['house']
            if isinstance(h_val, str):
                h_val = house_map.get(h_val, 0)
                
            strength = "Average"
            if d['points'] >= 5: strength = "Extreme"
            elif d['points'] >= 3.5: strength = "Strong"
            elif d['points'] >= 2: strength = "Good"
            elif d['points'] < 0: strength = "Weak"
            
            status_parts = []
            if d['is_retrograde']: status_parts.append("RETROGRADE")
            if d['is_combust']: status_parts.append("COMBUST")
            
            status_str = f" — {', '.join(status_parts)}" if status_parts else ""
            
            lines.append(f"{name.capitalize()}: {d['dignity']} ({strength}) in {d['sign']} House {h_val}{status_str}")
            
    return "\n".join(lines)

DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
# Standard Vimshottari year length (matches AstroSage / most modern calculators)
VIMSHOTTARI_DAYS_PER_YEAR = 365.25


def _nakshatra_balance(moon_lon: float) -> tuple[int, int, float]:
    """
    Nakshatra lord + remaining balance fraction using minute precision
    (consistent with get_nakshatra_and_pada).
    """
    total_minutes = round(moon_lon * 60)
    nak_idx = (total_minutes // 800) % 27
    lord_idx = nak_idx % 9
    pos_in_nak = total_minutes % 800
    remaining_frac = (800 - pos_in_nak) / 800.0
    return nak_idx, lord_idx, remaining_frac


def _vy_to_days(vy: float) -> float:
    return vy * VIMSHOTTARI_DAYS_PER_YEAR


def _add_vy(dt: datetime, vy: float) -> datetime:
    return dt + timedelta(days=_vy_to_days(vy))


def _sub_vy(dt: datetime, vy: float) -> datetime:
    return dt - timedelta(days=_vy_to_days(vy))


def _build_sub_periods(
    parent_start: datetime,
    parent_end: datetime,
    parent_vy: float,
    start_lord_idx: int,
) -> list[dict]:
    """Build 9 sub-periods (AD or PD) that exactly fill parent window."""
    periods = []
    current = parent_start
    for i in range(9):
        idx = (start_lord_idx + i) % 9
        lord = DASHA_LORDS[idx]
        if i == 8:
            end = parent_end
            dur_vy = (end - current).total_seconds() / (VIMSHOTTARI_DAYS_PER_YEAR * 86400)
        else:
            dur_vy = parent_vy * DASHA_YEARS[idx] / 120.0
            end = _add_vy(current, dur_vy)
        periods.append({
            "lord": lord,
            "start": current,
            "end": end,
            "duration_years": dur_vy,
        })
        current = end
    return periods


def _find_active(periods: list[dict], target_dt: datetime) -> dict:
    for p in periods:
        if p["start"] <= target_dt < p["end"]:
            return p
    return periods[-1] if periods else None


def calculate_vimshottari_dasha(birth_dt, moon_lon, target_dt=None):
    """
    Calculates Vimshottari Dasha periods (MD / AD / PD).
    Uses 365.25-day Vimshottari years with timedelta (not relativedelta fractions).
    """
    if target_dt is None:
        target_dt = datetime.now()

    _, lord_idx, remaining_frac = _nakshatra_balance(moon_lon)
    first_lord_vy = DASHA_YEARS[lord_idx]
    elapsed_vy = first_lord_vy * (1.0 - remaining_frac)
    first_md_start = _sub_vy(birth_dt, elapsed_vy)

    # Mahadasha timeline (2 full 120-year cycles)
    md_timeline = []
    current_start = first_md_start
    for cycle in range(2):
        for i in range(9):
            idx = (lord_idx + i + cycle * 9) % 9
            lord = DASHA_LORDS[idx]
            vy = DASHA_YEARS[idx]
            end = _add_vy(current_start, vy)
            md_timeline.append({
                "lord": lord,
                "start": current_start,
                "end": end,
                "years": vy,
            })
            current_start = end

    current_md = _find_active(md_timeline, target_dt)
    if not current_md:
        return {"error": "Target date out of dasha range"}

    md_lord_idx = DASHA_LORDS.index(current_md["lord"])
    ad_timeline = _build_sub_periods(
        current_md["start"], current_md["end"], current_md["years"], md_lord_idx
    )
    current_ad = _find_active(ad_timeline, target_dt)

    ad_lord_idx = DASHA_LORDS.index(current_ad["lord"])
    pd_timeline = _build_sub_periods(
        current_ad["start"], current_ad["end"], current_ad["duration_years"], ad_lord_idx
    )
    current_pd = _find_active(pd_timeline, target_dt)

    # Upcoming transitions (next PD / AD / MD ends)
    all_pd_ends = []
    found_current_md = False
    for md in md_timeline:
        if md is current_md:
            found_current_md = True
        if not found_current_md:
            continue
        m_lord_idx = DASHA_LORDS.index(md["lord"])
        ads = _build_sub_periods(md["start"], md["end"], md["years"], m_lord_idx)
        for ad in ads:
            a_idx = DASHA_LORDS.index(ad["lord"])
            pds = _build_sub_periods(ad["start"], ad["end"], ad["duration_years"], a_idx)
            for pd in pds:
                if pd["end"] > target_dt:
                    trans_type = "Pratyantardasha"
                    if pd["end"] == ad["end"]:
                        trans_type = "Antardasha"
                    if pd["end"] == md["end"]:
                        trans_type = "Mahadasha"
                    all_pd_ends.append({
                        "date": pd["end"],
                        "type": trans_type,
                        "md": md["lord"],
                        "ad": ad["lord"],
                        "pd": pd["lord"],
                    })
                if len(all_pd_ends) > 10:
                    break
            if len(all_pd_ends) > 10:
                break
        if len(all_pd_ends) > 10:
            break

    # Full hierarchical timeline (first 120-year cycle) with pratyantardashas
    full_timeline = []
    t_start = first_md_start
    for i in range(9):
        m_idx = (lord_idx + i) % 9
        m_lord = DASHA_LORDS[m_idx]
        m_vy = DASHA_YEARS[m_idx]
        m_end = _add_vy(t_start, m_vy)
        ads = _build_sub_periods(t_start, m_end, m_vy, m_idx)
        ad_list = []
        for ad in ads:
            a_idx = DASHA_LORDS.index(ad["lord"])
            pds = _build_sub_periods(ad["start"], ad["end"], ad["duration_years"], a_idx)
            ad_list.append({
                "lord": ad["lord"],
                "start": ad["start"].strftime("%Y-%m-%d"),
                "end": ad["end"].strftime("%Y-%m-%d"),
                "pratyantardashas": [
                    {
                        "lord": p["lord"],
                        "start": p["start"].strftime("%Y-%m-%d"),
                        "end": p["end"].strftime("%Y-%m-%d"),
                    }
                    for p in pds
                ],
            })
        full_timeline.append({
            "lord": m_lord,
            "start": t_start.strftime("%Y-%m-%d"),
            "end": m_end.strftime("%Y-%m-%d"),
            "antardashas": ad_list,
        })
        t_start = m_end

    def _fmt_end(dt: datetime) -> str:
        # Inclusive end date (last active day) for display
        return (dt - timedelta(seconds=1)).strftime("%Y-%m-%d")

    summary = (
        f"Currently in {current_md['lord']} Mahadasha (ends {_fmt_end(current_md['end'])}) > "
        f"{current_ad['lord']} Antardasha (ends {_fmt_end(current_ad['end'])}) > "
        f"{current_pd['lord']} Pratyantardasha (ends {_fmt_end(current_pd['end'])})"
    )

    return {
        "current_mahadasha": {
            "lord": current_md["lord"],
            "start": current_md["start"].isoformat(),
            "end": current_md["end"].isoformat(),
            "end_inclusive": _fmt_end(current_md["end"]),
        },
        "current_antardasha": {
            "lord": current_ad["lord"],
            "start": current_ad["start"].isoformat(),
            "end": current_ad["end"].isoformat(),
            "end_inclusive": _fmt_end(current_ad["end"]),
        },
        "current_pratyantardasha": {
            "lord": current_pd["lord"],
            "start": current_pd["start"].isoformat(),
            "end": current_pd["end"].isoformat(),
            "end_inclusive": _fmt_end(current_pd["end"]),
        },
        "pratyantardasha_timeline": [
            {
                "lord": p["lord"],
                "start": p["start"].isoformat(),
                "end": p["end"].isoformat(),
                "end_inclusive": _fmt_end(p["end"]),
            }
            for p in pd_timeline
        ],
        "upcoming_transitions": all_pd_ends[:5],
        "summary": summary,
        "full_timeline": full_timeline,
        "first_mahadasha_start": first_md_start.isoformat(),
    }

import kerykeion as kr
from kerykeion import AstrologicalSubject

# Load environment variables
load_dotenv()
GEONAMES_USER = os.getenv("GEONAMES_USERNAME", "demo_user")


def load_birth_data():
    # Use path relative to this file
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'birth_data.yaml')
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
        data['year'] = int(data['year'])
        data['month'] = int(data['month'])
        data['day'] = int(data['day'])
        data['hour'] = int(data['hour'])
        data['minute'] = int(data['minute'])
        return data

def get_sky_on_date(year, month, day, hour=12, minute=0, city='Jabalpur', nation='IN', name='Sky'):
    subject = AstrologicalSubject(
        name, int(year), int(month), int(day),
        int(hour), int(minute), city, nation,
        geonames_username=GEONAMES_USER,
        zodiac_type='Sidereal',
        sidereal_mode='LAHIRI',
        houses_system_identifier='W'
    )
    return subject

def get_natal_chart_from_profile(profile: dict):
    """Build kerykeion subject from a stored user profile."""
    birth = profile["meta"]["birth"]
    return get_sky_on_date(
        birth["year"], birth["month"], birth["day"],
        birth["hour"], birth["minute"],
        birth["city"], birth["nation"],
        profile["meta"].get("name", "Natal"),
    )


def get_natal_chart():
    bd = load_birth_data()
    return get_sky_on_date(
        bd['year'], bd['month'], bd['day'], 
        bd['hour'], bd['minute'], bd['city'], bd['nation'], bd['name']
    )

def get_current_sky():
    now = datetime.now()
    return get_sky_on_date(
        now.year, now.month, now.day, 
        now.hour, now.minute, 'Jabalpur', 'IN', 'CurrentSky'
    )

def get_house_from_asc(planet_abs_pos, asc_abs_pos):
    """Calculates house number (1-12) based on Whole Sign House system from a given Ascendant."""
    planet_sign_idx = int(planet_abs_pos // 30)
    asc_sign_idx = int(asc_abs_pos // 30)
    house = (planet_sign_idx - asc_sign_idx + 12) % 12 + 1
    return house

def format_detailed_report(subject, reference_abs_pos=None, reference_name=None):
    m = subject.model()
    planets_keys = [
        'sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn',
        'true_north_lunar_node', 'true_south_lunar_node',
        'uranus', 'neptune', 'pluto'
    ]
    
    lines = []
    lines.append(f"Report for: {m.name}")
    lines.append(f"Date: {m.year}-{m.month:02d}-{m.day:02d} {m.hour:02d}:{m.minute:02d}")
    
    if reference_abs_pos is not None:
        # If we have a reference, we display it as the chart center
        ref_sign = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"][int(reference_abs_pos // 30)]
        ref_nak, ref_pada = get_nakshatra_and_pada(reference_abs_pos)
        lines.append(f"Reference Center ({reference_name}): {ref_sign} ({reference_abs_pos:.2f}°) | Nakshatra: {ref_nak} (Pada {ref_pada})")
    else:
        asc_nak, asc_pada = get_nakshatra_and_pada(m.ascendant.abs_pos)
        lines.append(f"Lagna (Ascendant): {m.ascendant.sign} ({m.ascendant.abs_pos:.2f}°) | Nakshatra: {asc_nak} (Pada {asc_pada})")
    
    lines.append("-" * 90)
    lines.append(f"{'Graha':<12} | {'Sign':<5} | {'Degree':<10} | {'Nakshatra':<15} | {'Pada':<4} | {'Retro':<5} | {'House'}")
    lines.append("-" * 90)
    
    for key in planets_keys:
        p = getattr(m, key)
        nak, pada = get_nakshatra_and_pada(p.abs_pos)
        name = "Rahu" if key == 'true_north_lunar_node' else ("Ketu" if key == 'true_south_lunar_node' else p.name)
        retro = "YES" if p.retrograde else "NO"
        
        deg = int(p.position)
        rem = (p.position - deg) * 60
        mins = int(rem)
        secs = int((rem - mins) * 60)
        deg_str = f"{deg:02d}°{mins:02d}'{secs:02d}\""
        
        if reference_abs_pos is not None:
            house = get_house_from_asc(p.abs_pos, reference_abs_pos)
        else:
            house = p.house # Default house from the subject itself
            
        lines.append(f"{name:<12} | {p.sign:<5} | {deg_str:<10} | {nak:<15} | {pada:<4} | {retro:<5} | {house}")
    
    return "\n".join(lines)

def format_chart_for_ai(subject):
    m = subject.model()
    planets_keys = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'true_north_lunar_node', 'true_south_lunar_node']
    result = []
    for key in planets_keys:
        p = getattr(m, key)
        name = "Rahu" if key == 'true_north_lunar_node' else ("Ketu" if key == 'true_south_lunar_node' else p.name)
        nak, pada = get_nakshatra_and_pada(p.abs_pos)
        result.append(f"{name}: {p.sign} in {p.house} | Nakshatra: {nak} (Pada {pada}) | Retrograde: {'Yes' if p.retrograde else 'No'}")
    return '\n'.join(result)

def get_planet_snapshot_dict(subject, dasha_info):
    """Returns a structured dictionary of planetary positions and dasha info for database storage."""
    m = subject.model()
    planets_keys = {
        'sun': 'sun', 'moon': 'moon', 'mercury': 'mercury', 'venus': 'venus', 
        'mars': 'mars', 'jupiter': 'jupiter', 'saturn': 'saturn',
        'true_north_lunar_node': 'rahu', 'true_south_lunar_node': 'ketu'
    }
    
    house_map = {
        "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
        "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
        "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12
    }
    
    snapshot = {}
    for key, name in planets_keys.items():
        p = getattr(m, key)
        # Handle string house names from kerykeion
        h_val = p.house
        if isinstance(h_val, str):
            h_val = house_map.get(h_val, 0)
        
        snapshot[name] = {
            "sign": p.sign,
            "house": int(h_val),
            "degree": round(float(p.position), 2),
            "abs_pos": round(float(p.abs_pos), 2)
        }
    
    snapshot["mahadasha"] = dasha_info['current_mahadasha']['lord']
    snapshot["antardasha"] = dasha_info['current_antardasha']['lord']
    snapshot["pratyantardasha"] = dasha_info['current_pratyantardasha']['lord']
    snapshot["lagna"] = m.ascendant.sign
    snapshot["lagna_degree"] = round(float(m.ascendant.position), 2)
    
    return snapshot

if __name__ == '__main__':
    try:
        subject = get_natal_chart()
        print(format_detailed_report(subject))
    except Exception as e:
        print(f"Error: {e}")
