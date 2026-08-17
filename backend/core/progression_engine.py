"""
core/progression_engine.py
────────────────────────────────────────────────────
Western Progressions & Solar Return
Secondary progressions (1 day = 1 year) and Solar Return charts.
────────────────────────────────────────────────────
"""
import swisseph as swe

PLANET_MAP = {
    swe.SUN: "Sun", swe.MOON: "Moon", swe.MARS: "Mars", 
    swe.MERCURY: "Mercury", swe.JUPITER: "Jupiter", 
    swe.VENUS: "Venus", swe.SATURN: "Saturn",
    swe.MEAN_NODE: "Rahu"  # Ketu is opposite
}

def secondary_progressions(birth_jd, age_years, birth_lat, birth_lon):
    """
    One day after birth = one year of life
    Progress chart by adding age in days to birth JD
    """
    progressed_jd = birth_jd + age_years  # 1 day per year
    
    prog_positions = {}
    for planet_id, name in PLANET_MAP.items():
        if name in ("Rahu", "Ketu"): continue
        pos = swe.calc_ut(progressed_jd, planet_id)[0][0]
        prog_positions[name] = pos
    
    # Progressed Ascendant — moves ~1° per year
    prog_houses = swe.houses(progressed_jd, birth_lat, birth_lon)[1]
    prog_asc = prog_houses[0]
    
    return {"positions": prog_positions, "ascendant": prog_asc, "jd": progressed_jd}

def solar_return_chart(birth_jd, birth_sun_pos, target_year, lat, lon):
    """
    Find exact moment Sun returns to natal degree in given year
    """
    # Approximate JD for that year
    approx_jd = birth_jd + (target_year * 365.25)
    
    # Narrow down to exact second
    for _ in range(50):  # iterate to precision
        current_sun = swe.calc_ut(approx_jd, swe.SUN)[0][0]
        diff = (birth_sun_pos - current_sun) % 360
        if diff > 180: diff -= 360
        approx_jd += diff / 360  # move proportionally
        if abs(diff) < 0.0001: break
    
    # Cast chart for this exact moment
    sr_houses = swe.houses(approx_jd, lat, lon)[1]
    
    sr_positions = {}
    for planet_id, name in PLANET_MAP.items():
        sr_positions[name] = swe.calc_ut(approx_jd, planet_id)[0][0]
        if name == "Rahu":
            sr_positions["Ketu"] = (sr_positions["Rahu"] + 180) % 360
            
    return {"jd": approx_jd, "ascendant": sr_houses[0], "positions": sr_positions}
