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

DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

def get_nakshatra_and_pada(abs_pos):
    """Calculates Nakshatra and Pada from absolute position (0-360)."""
    total_minutes = round(abs_pos * 60)
    nak_idx = (total_minutes // 800) % 27
    pada = ((total_minutes % 800) // 200) + 1
    return NAKSHATRAS[nak_idx], int(pada)

def calculate_vimshottari_dasha(birth_dt, moon_lon, target_dt=None):
    """
    Calculates Vimshottari Dasha periods.
    birth_dt: datetime object of birth
    moon_lon: Sidereal longitude of Moon
    target_dt: datetime object to calculate dasha for (defaults to now)
    """
    if target_dt is None:
        target_dt = datetime.now()

    # 1. Determine starting nakshatra and lord
    nak_size = 360 / 27  # 13.333...
    nak_idx = int(moon_lon / nak_size)
    lord_idx = nak_idx % 9
    
    # 2. Calculate balance of first dasha
    elapsed_in_nak = moon_lon % nak_size
    remaining_perc = (nak_size - elapsed_in_nak) / nak_size
    
    first_lord_years = DASHA_YEARS[lord_idx]
    remaining_years = first_lord_years * remaining_perc
    
    # Calculate start of the very first dasha (the one at birth)
    # The first dasha started SOME time before birth
    elapsed_years = first_lord_years * (elapsed_in_nak / nak_size)
    # We'll use relativedelta for better calendar accuracy
    # Note: Astrology traditionally uses 360-day years or 365.25. 
    # relativedelta(years=...) is standard for modern interpretations.
    first_dasha_start = birth_dt - relativedelta(years=int(elapsed_years), days=int((elapsed_years % 1) * 365.25))
    
    # 3. Build the Mahadasha timeline
    md_timeline = []
    current_start = first_dasha_start
    
    # We need to cover at least 120 years from birth, plus some buffer
    # Let's run for 2 cycles just in case (240 years)
    for cycle in range(2):
        for i in range(9):
            idx = (lord_idx + i + cycle * 9) % 9
            lord = DASHA_LORDS[idx]
            years = DASHA_YEARS[idx]
            end = current_start + relativedelta(years=years)
            md_timeline.append({
                "lord": lord,
                "start": current_start,
                "end": end,
                "years": years
            })
            current_start = end

    # 4. Find current Mahadasha
    current_md = None
    for md in md_timeline:
        if md['start'] <= target_dt < md['end']:
            current_md = md
            break
            
    if not current_md:
        return {"error": "Target date out of dasha range"}

    # 5. Calculate Antardashas for current Mahadasha
    ad_timeline = []
    md_start = current_md['start']
    md_total_years = current_md['years']
    
    # AD order starts from the MD lord itself
    md_lord_idx = DASHA_LORDS.index(current_md['lord'])
    curr_ad_start = md_start
    for i in range(9):
        idx = (md_lord_idx + i) % 9
        ad_lord = DASHA_LORDS[idx]
        ad_years = DASHA_YEARS[idx]
        # AD length = (MD years * AD years) / 120
        ad_duration_years = (md_total_years * ad_years) / 120
        ad_end = curr_ad_start + relativedelta(years=int(ad_duration_years), days=int((ad_duration_years % 1) * 365.25))
        ad_timeline.append({
            "lord": ad_lord,
            "start": curr_ad_start,
            "end": ad_end,
            "duration_years": ad_duration_years
        })
        curr_ad_start = ad_end

    current_ad = next(ad for ad in ad_timeline if ad['start'] <= target_dt < ad['end'])

    # 6. Calculate Pratyantardashas for current Antardasha
    pd_timeline = []
    ad_start = current_ad['start']
    ad_duration_years = current_ad['duration_years']
    
    ad_lord_idx = DASHA_LORDS.index(current_ad['lord'])
    curr_pd_start = ad_start
    for i in range(9):
        idx = (ad_lord_idx + i) % 9
        pd_lord = DASHA_LORDS[idx]
        pd_years = DASHA_YEARS[idx]
        # PD length = (AD duration * PD years) / 120
        pd_duration_years = (ad_duration_years * pd_years) / 120
        pd_end = curr_pd_start + relativedelta(years=int(pd_duration_years), days=int((pd_duration_years % 1) * 365.25))
        pd_timeline.append({
            "lord": pd_lord,
            "start": curr_pd_start,
            "end": pd_end
        })
        curr_pd_start = pd_end

    current_pd = next(pd for pd in pd_timeline if pd['start'] <= target_dt < pd['end'])

    # 7. Next 5 transitions (can be MD, AD or PD changes)
    # For simplicity, we'll just track the next upcoming PD ends, 
    # as every PD change is a transition.
    all_pd_ends = []
    # Collect PD ends for current AD and subsequent ADs
    found_current_md = False
    for md in md_timeline:
        if md == current_md: found_current_md = True
        if not found_current_md: continue
        
        # Calculate ADs for this MD
        m_start = md['start']
        m_years = md['years']
        m_lord_idx = DASHA_LORDS.index(md['lord'])
        c_ad_start = m_start
        for i in range(9):
            a_idx = (m_lord_idx + i) % 9
            a_lord = DASHA_LORDS[a_idx]
            a_years = DASHA_YEARS[a_idx]
            a_dur = (m_years * a_years) / 120
            c_ad_end = c_ad_start + relativedelta(years=int(a_dur), days=int((a_dur % 1) * 365.25))
            
            # Calculate PDs for this AD
            c_pd_start = c_ad_start
            for j in range(9):
                p_idx = (a_idx + j) % 9
                p_lord = DASHA_LORDS[p_idx]
                p_years = DASHA_YEARS[p_idx]
                p_dur = (a_dur * p_years) / 120
                c_pd_end = c_pd_start + relativedelta(years=int(p_dur), days=int((p_dur % 1) * 365.25))
                
                if c_pd_end > target_dt:
                    # Determine what type of transition this is
                    trans_type = "Pratyantardasha"
                    if c_pd_end == c_ad_end: trans_type = "Antardasha"
                    if c_pd_end == md['end']: trans_type = "Mahadasha"
                    
                    all_pd_ends.append({
                        "date": c_pd_end,
                        "to_lord": DASHA_LORDS[(p_idx + 1) % 9] if trans_type == "Pratyantardasha" else (DASHA_LORDS[(a_idx + 1) % 9] if trans_type == "Antardasha" else DASHA_LORDS[(m_lord_idx + 1) % 9]),
                        "type": trans_type,
                        "md": md['lord'],
                        "ad": a_lord,
                        "pd": p_lord
                    })
                c_pd_start = c_pd_end
                if len(all_pd_ends) > 10: break
            c_ad_start = c_ad_end
            if len(all_pd_ends) > 10: break
        if len(all_pd_ends) > 10: break

    # 8. Human readable summary
    summary = f"Currently in {current_md['lord']} Mahadasha (ends {current_md['end'].strftime('%b %Y')}) > " \
              f"{current_ad['lord']} Antardasha (ends {current_ad['end'].strftime('%b %Y')}) > " \
              f"{current_pd['lord']} Pratyantardasha (ends {current_pd['end'].strftime('%b %d, %Y')})"

    return {
        "current_mahadasha": current_md,
        "current_antardasha": current_ad,
        "current_pratyantardasha": current_pd,
        "upcoming_transitions": all_pd_ends[:5],
        "summary": summary
    }

import kerykeion as kr
from kerykeion import AstrologicalSubject

# Load environment variables
load_dotenv()
GEONAMES_USER = os.getenv("GEONAMES_USERNAME", "himanshurajak_22")


def load_birth_data():
    with open('config/birth_data.yaml', 'r') as f:
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
