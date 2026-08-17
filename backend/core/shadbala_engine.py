"""
core/shadbala_engine.py — BPHS Shadbala (exact formulas per specification)
"""
import math
from datetime import datetime, timedelta

# ── Constants ──────────────────────────────────────────────────────────────────
SHADBALA_MIN_REQ = {
    "Sun": 5.0, "Moon": 6.0, "Mars": 5.0,
    "Mercury": 7.0, "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0
}
NAISARGIKA_BALA = {
    "Sun": 60.0, "Moon": 51.43, "Venus": 42.86, "Jupiter": 34.29,
    "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57,
}
EXALTATION_ABS = {
    "Sun": 10.0, "Moon": 33.0, "Mars": 298.0,
    "Mercury": 165.0, "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0,
}
OWN_SIGNS = {
    "Sun": [4], "Moon": [3], "Mars": [0, 7],
    "Mercury": [2, 5], "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10],
}
MOOLATRIKONA = {
    "Sun": 4, "Moon": 1, "Mars": 0, "Mercury": 5,
    "Jupiter": 8, "Venus": 6, "Saturn": 10,
}
SIGN_LORDS = [
    "Mars","Venus","Mercury","Moon","Sun","Mercury",
    "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"
]
# Natural friendship table
NAT = {
    "Sun":     {"f":{"Moon","Mars","Jupiter"},     "e":{"Venus","Saturn"},       "n":{"Mercury"}},
    "Moon":    {"f":{"Sun","Mercury"},             "e":set(),                    "n":{"Mars","Jupiter","Venus","Saturn"}},
    "Mars":    {"f":{"Sun","Moon","Jupiter"},      "e":{"Mercury"},              "n":{"Venus","Saturn"}},
    "Mercury": {"f":{"Sun","Venus"},               "e":{"Moon"},                 "n":{"Mars","Jupiter","Saturn"}},
    "Jupiter": {"f":{"Sun","Moon","Mars"},         "e":{"Mercury","Venus"},      "n":{"Saturn"}},
    "Venus":   {"f":{"Mercury","Saturn"},          "e":{"Sun","Moon"},           "n":{"Mars","Jupiter"}},
    "Saturn":  {"f":{"Mercury","Venus"},           "e":{"Sun","Moon","Mars"},    "n":{"Jupiter"}},
}
DIG_BALA_BEST = {"Sun":10,"Moon":4,"Mars":10,"Mercury":1,"Jupiter":1,"Venus":4,"Saturn":7}
# BPHS: Sun,Jupiter,Venus = diurnal; Moon,Mars,Saturn = nocturnal
DIURNAL  = {"Sun","Jupiter","Venus"}
NOCTURNAL = {"Moon","Mars","Saturn"}
WEEKDAY_LORDS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]  # Sun=0
# Hora sequences per weekday starting from sunrise
HORA_SEQS = [
    ["Sun","Venus","Mercury","Moon","Saturn","Jupiter","Mars"],    # Sunday
    ["Moon","Saturn","Jupiter","Mars","Sun","Venus","Mercury"],    # Monday
    ["Mars","Sun","Venus","Mercury","Moon","Saturn","Jupiter"],    # Tuesday
    ["Mercury","Moon","Saturn","Jupiter","Mars","Sun","Venus"],    # Wednesday
    ["Jupiter","Mars","Sun","Venus","Mercury","Moon","Saturn"],    # Thursday
    ["Venus","Mercury","Moon","Saturn","Jupiter","Mars","Sun"],    # Friday
    ["Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"],    # Saturday
]
TRIBHAGA_DAY   = ["Mercury","Sun","Saturn"]
TRIBHAGA_NIGHT = ["Moon","Venus","Mars"]

# Dignity point values per varga (Sapta Vargiya Bala)
DIGNITY_PTS = {
    "exalted": 20, "moolatrikona": 18, "own": 15,
    "great_friend": 12, "friend": 8, "neutral": 4,
    "enemy": 2, "great_enemy": 1, "debilitated": 0,
}

# ── Utility ────────────────────────────────────────────────────────────────────
def _si(p): return int(p // 30) % 12
def _house(abs_pos, li): return (_si(abs_pos) - li + 12) % 12 + 1
def _deg(p): return p % 30


def _sunrise_sunset_local(year, month, day, lat, lon):
    """Accurate sunrise/sunset via Swiss Ephemeris (UTC), converted to local civil time."""
    import swisseph as swe
    geopos = (float(lon), float(lat), 0.0)
    jd_noon = swe.julday(year, month, day, 12.0)
    try:
        rise = swe.rise_trans(jd_noon, swe.SUN, geopos, swe.CALC_RISE | swe.BIT_DISC_CENTER)[1][0]
        sett = swe.rise_trans(jd_noon, swe.SUN, geopos, swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]
        tz_offset_hours = lon / 15.0
        sunrise = datetime(year, month, day) + timedelta(hours=(rise - jd_noon) * 24 + tz_offset_hours)
        sunset = datetime(year, month, day) + timedelta(hours=(sett - jd_noon) * 24 + tz_offset_hours)
        return sunrise, sunset
    except Exception:
        lat_r = math.radians(lat)
        doy = datetime(year, month, day).timetuple().tm_yday
        decl = math.radians(23.44) * math.cos(math.radians(360 / 365 * (doy - 172)))
        cos_ha = max(-1.0, min(1.0, -math.tan(lat_r) * math.tan(decl)))
        ha = math.degrees(math.acos(cos_ha))
        corr = 5.5 - lon / 15.0
        sunrise = datetime(year, month, day) + timedelta(hours=12.0 - ha / 15.0 + corr)
        sunset = datetime(year, month, day) + timedelta(hours=12.0 + ha / 15.0 + corr)
        return sunrise, sunset

# ── Compound Friendship ────────────────────────────────────────────────────────
def _nat_rel(planet, other):
    t = NAT.get(planet, {})
    if other in t.get("f", set()): return "friend"
    if other in t.get("e", set()): return "enemy"
    return "neutral"

def _temp_rel(h_planet, h_other):
    diff = abs(h_planet - h_other) % 12
    if diff > 6: diff = 12 - diff
    return "friend" if diff <= 5 else "enemy"

def _compound_rel(planet, other, h_planet, h_other):
    if other == planet: return "own"
    nat = _nat_rel(planet, other)
    tmp = _temp_rel(h_planet, h_other)
    if nat == "friend"  and tmp == "friend": return "great_friend"
    if nat == "friend"  and tmp == "enemy":  return "neutral"
    if nat == "enemy"   and tmp == "friend": return "neutral"
    if nat == "enemy"   and tmp == "enemy":  return "great_enemy"
    if nat == "neutral" and tmp == "friend": return "friend"
    if nat == "neutral" and tmp == "enemy":  return "enemy"
    return "neutral"

def _dignity(planet, sign_idx, planet_house, all_houses):
    exalt = _si(EXALTATION_ABS[planet])
    debit = (exalt + 6) % 12
    if sign_idx == debit:   return "debilitated"
    if sign_idx == exalt:   return "exalted"
    if sign_idx == MOOLATRIKONA.get(planet): return "moolatrikona"
    if sign_idx in OWN_SIGNS.get(planet, []): return "own"
    lord = SIGN_LORDS[sign_idx]
    if lord == planet: return "own"
    lord_house = all_houses.get(lord, planet_house)
    return _compound_rel(planet, lord, planet_house, lord_house)

# ── Sthana Bala ────────────────────────────────────────────────────────────────
def _uccha_bala(planet, abs_pos):
    peak = EXALTATION_ABS[planet]
    diff = abs(abs_pos - peak) % 360
    if diff > 180: diff = 360 - diff
    return round(60.0 * (1.0 - diff / 180.0), 2)

def _varga(abs_pos, n):
    """General varga calculator based on astro_engine.py logic."""
    si = int(abs_pos // 30) % 12
    pos = abs_pos % 30
    part = int(pos // (30/n))
    
    if n == 1: return si * 30
    if n == 2: # Hora
        if si % 2 == 0: # Odd
            return (4 if pos < 15 else 3) * 30
        else: # Even
            return (3 if pos < 15 else 4) * 30
    if n == 3: # Drekkana
        return ((si + (part * 4)) % 12) * 30
    if n == 7: # Saptamsha
        start = si if si % 2 == 0 else (si + 6) % 12
        return ((start + part) % 12) * 30
    if n == 9: # Navamsha
        starts = [0, 9, 6, 3, 0, 9, 6, 3, 0, 9, 6, 3]
        return ((starts[si] + part) % 12) * 30
    if n == 12: # Dwadashamsha
        return ((si + part) % 12) * 30
    if n == 30: # Trimshamsha
        if si % 2 == 0: # Odd
            if pos < 5: return 0 * 30 # Aries (Mars)
            elif pos < 10: return 10 * 30 # Aquarius (Sat)
            elif pos < 18: return 8 * 30 # Sag (Jup)
            elif pos < 25: return 2 * 30 # Gemini (Mer)
            else: return 6 * 30 # Libra (Ven)
        else: # Even
            if pos < 5: return 1 * 30 # Taurus (Ven)
            elif pos < 12: return 5 * 30 # Virgo (Mer)
            elif pos < 20: return 11 * 30 # Pisces (Jup)
            elif pos < 25: return 9 * 30 # Cap (Sat)
            else: return 7 * 30 # Scorpio (Mars)
    return ((si * n + part) % 12) * 30

def _sapv(planet, d1_abs, planet_house, all_houses):
    total = 0
    # Calculate dignity in D1, D2, D3, D7, D9, D12, D30
    for n in [1, 2, 3, 7, 9, 12, 30]:
        v_abs = _varga(d1_abs, n)
        v_si = int(v_abs // 30) % 12
        # For Sapta Vargiya, we need the lord of the varga sign
        # and its relationship to the planet
        dig = _dignity(planet, v_si, planet_house, all_houses)
        total += DIGNITY_PTS.get(dig, 4)
    return round(float(total), 2)

def _ooja_yugma(planet, d1_abs, d9_abs):
    ODD_LIKE = {"Sun","Mars","Jupiter"}
    EVEN_LIKE = {"Moon","Venus"}
    BOTH_LIKE = {"Mercury","Saturn"}
    total = 0.0
    for abs_pos in [d1_abs, d9_abs]:
        is_odd = _si(abs_pos) % 2 == 0   # Aries=0 is odd
        if planet in ODD_LIKE:
            total += 15.0 if is_odd else 0.0
        elif planet in EVEN_LIKE:
            total += 0.0 if is_odd else 15.0
        elif planet in BOTH_LIKE:
            total += 15.0
    return total

def _kendradi(house):
    if house in {1,4,7,10}: return 60.0
    if house in {2,5,8,11}: return 30.0
    return 15.0

def _drekkana(planet, abs_pos):
    MALE    = {"Sun","Mars","Jupiter"}
    NEUTRAL = {"Mercury","Saturn"}
    FEMALE  = {"Moon","Venus"}
    d = _deg(abs_pos)
    drek = 0 if d < 10 else (1 if d < 20 else 2)
    if drek == 0 and planet in MALE:    return 15.0
    if drek == 1 and planet in NEUTRAL: return 15.0
    if drek == 2 and planet in FEMALE:  return 15.0
    return 0.0

# ── Dig Bala ───────────────────────────────────────────────────────────────────
def _dig_bala(planet, house):
    best = DIG_BALA_BEST[planet]
    diff = abs(house - best)
    if diff > 6: diff = 12 - diff
    return round(60.0 * (1.0 - diff / 6.0), 2)

# ── Kala Bala ──────────────────────────────────────────────────────────────────
def _nathonnatha(planet, is_day):
    if planet in DIURNAL:   return 60.0 if is_day else 0.0
    if planet in NOCTURNAL: return 0.0 if is_day else 60.0
    return 30.0  # Mercury

def _paksha_bala(planet, moon_abs, sun_abs):
    """
    Paksha Bala: 0-60 based on lunar phase.
    Waxing (Shukla, 0-180°): Benefics strong, Malefics weak
    Waning (Krishna, 180-360°): Malefics strong, Benefics weak
    """
    angle = (moon_abs - sun_abs) % 360
    BENEFICS = {"Jupiter","Venus","Mercury","Moon"}
    MALEFICS  = {"Sun","Mars","Saturn"}
    waxing = angle <= 180

    if planet == "Moon" or planet in BENEFICS:
        # Strong at full moon (180°), weak at new moon (0° or 360°)
        if waxing:
            return round(min(60.0, angle / 3.0), 2)
        else:
            return round(min(60.0, (360.0 - angle) / 3.0), 2)
    if planet in MALEFICS:
        # Strong at new moon (0°/360°), weak at full moon (180°)
        if waxing:
            return round(min(60.0, (180.0 - angle) / 3.0), 2)
        else:
            return round(min(60.0, (angle - 180.0) / 3.0), 2)
    return 30.0


def _tribhaga(planet, is_day, birth_dt, sunrise_dt, sunset_dt):
    if planet == "Jupiter": return 60.0
    try:
        if is_day:
            span = (sunset_dt - sunrise_dt).total_seconds()
            elapsed = (birth_dt - sunrise_dt).total_seconds()
            lord = TRIBHAGA_DAY[min(int(elapsed / span * 3), 2)]
        else:
            if birth_dt < sunrise_dt:
                prev = sunset_dt - timedelta(days=1)
                span = (sunrise_dt - prev).total_seconds()
                elapsed = (birth_dt - prev).total_seconds()
            else:
                nxt = sunrise_dt + timedelta(days=1)
                span = (nxt - sunset_dt).total_seconds()
                elapsed = (birth_dt - sunset_dt).total_seconds()
            lord = TRIBHAGA_NIGHT[min(int(elapsed / span * 3), 2)]
        return 60.0 if planet == lord else 0.0
    except Exception:
        return 0.0

def _hora_bala(planet, weekday_sun, birth_dt, sunrise_dt):
    try:
        seq = HORA_SEQS[weekday_sun]
        hrs = (birth_dt - sunrise_dt).total_seconds() / 3600.0
        lord = seq[int(hrs) % 7]
        return 60.0 if planet == lord else 0.0
    except Exception:
        return 0.0

def _vara_bala(planet, weekday_sun):
    return 45.0 if planet == WEEKDAY_LORDS[weekday_sun] else 0.0

def _masa_bala(planet, moon_abs, sun_abs, birth_dt):
    """Lord of weekday on which current lunar month (Shukla Pratipada) started."""
    try:
        angle = (moon_abs - sun_abs) % 360
        days_since_nm = angle / 12.19  # Moon travels ~12.19°/day relative to Sun
        nm_dt = birth_dt - timedelta(days=days_since_nm)
        wd = (nm_dt.weekday() + 1) % 7   # convert Mon=0 → Sun=0
        return 30.0 if planet == WEEKDAY_LORDS[wd] else 0.0
    except Exception:
        return 0.0

def _varsha_bala(planet, birth_year, moon_abs, sun_abs, birth_dt):
    """Lord of weekday on which Chaitra Shukla Pratipada (Hindu New Year) fell."""
    try:
        # Find new moon nearest to spring equinox in birth year
        mar21 = datetime(birth_year, 3, 21)
        # Approx: iterate from Mar 1 to find nearest new moon
        # Simple: use Moon-Sun angle at Mar 21 to back-calc new moon date
        # For robustness: use a fixed approximation based on synodic month
        # Synodic month = 29.53 days
        # Find number of synodic months from J2000 to Mar 21 of birth year
        j2000 = datetime(2000, 1, 6, 18, 14)  # known new moon
        days_from_j2000 = (mar21 - j2000).total_seconds() / 86400
        months = days_from_j2000 / 29.53059
        last_nm_days = (months - int(months)) * 29.53059
        chaitra_nm = mar21 - timedelta(days=last_nm_days)
        wd = (chaitra_nm.weekday() + 1) % 7
        return 15.0 if planet == WEEKDAY_LORDS[wd] else 0.0
    except Exception:
        return 0.0

def _ayana_bala(planet, abs_pos, declination=None):
    """60 × |sin(declination)|; N preferred by diurnal planets, S by nocturnal."""
    if declination is None:
        lam = math.radians(abs_pos)
        declination = math.degrees(math.asin(math.sin(math.radians(23.44)) * math.sin(lam)))
    raw = 60.0 * abs(math.sin(math.radians(declination)))
    # Diurnal planets prefer North, nocturnal prefer South
    prefer_north = planet in DIURNAL
    dec_is_north = declination >= 0
    if prefer_north == dec_is_north:
        return round(raw, 2)
    else:
        return round(60.0 - raw, 2)

# ── Chesta Bala ────────────────────────────────────────────────────────────────
MEAN_MOTION = {"Mars":0.524,"Mercury":1.383,"Jupiter":0.083,"Venus":1.200,"Saturn":0.033}

def _chesta_bala(planet, is_retro, speed, paksha, ayana):
    if planet == "Moon": return paksha   # Moon uses Paksha Bala
    if planet == "Sun":  return ayana    # Sun uses Ayana Bala
    if is_retro: return 60.0
    mean = MEAN_MOTION.get(planet, 1.0)
    spd = abs(speed) if speed is not None else mean
    ratio = spd / mean
    if ratio > 1.75:   return 60.0
    if ratio > 1.25:   return 45.0
    if ratio > 0.75:   return 7.5
    if ratio > 0.25:   return 15.0
    return 30.0   # very slow / near stationary

# ── Drik Bala ──────────────────────────────────────────────────────────────────
def _drik_bala(planet, house, all_houses, is_waxing_moon):
    BENEFICS = {"Jupiter","Venus","Mercury"}
    MALEFICS  = {"Sun","Mars","Saturn","Rahu","Ketu"}
    score = 0.0
    for other, other_house in all_houses.items():
        if other == planet: continue
        fwd = (other_house - house) % 12
        # Check if other planet aspects this house
        contrib = 0.0
        if fwd == 6:  # 7th house full aspect
            contrib = 15.0
        elif other == "Mars"    and fwd in {3, 7}:  contrib = 15.0 * 0.75
        elif other == "Jupiter" and fwd in {4, 8}:  contrib = 15.0 * 0.75
        elif other == "Saturn"  and fwd in {2, 9}:  contrib = 15.0 * 0.75
        if contrib == 0.0: continue
        # Moon: waxing = benefic, waning = malefic
        if other == "Moon":
            score += contrib if is_waxing_moon else -contrib
        elif other in BENEFICS:
            score += contrib
        elif other in MALEFICS:
            score -= contrib
    return round(score, 2)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

def calculate_shadbala_rupas(subject) -> dict:
    m = subject.model()
    PKEYS = {'sun':'Sun','moon':'Moon','mars':'Mars','mercury':'Mercury',
             'jupiter':'Jupiter','venus':'Venus','saturn':'Saturn'}
    try:
        yr=subject.year;mo=subject.month;dy=subject.day
        hr=subject.hour;mn=subject.minute;lat=subject.lat;lng=subject.lng
    except Exception:
        yr,mo,dy,hr,mn,lat,lng=2006,8,22,9,37,23.18,79.95

    birth_dt=datetime(yr,mo,dy,hr,mn)
    wd_sun=(birth_dt.weekday()+1)%7  # Sun=0

    sunrise_dt, sunset_dt = _sunrise_sunset_local(yr, mo, dy, lat, lng)
    is_day = sunrise_dt <= birth_dt <= sunset_dt

    lagna_abs=float(m.ascendant.abs_pos)
    li=_si(lagna_abs)
    sun_abs=float(m.sun.abs_pos)
    moon_abs=float(m.moon.abs_pos)
    moon_phase=(moon_abs-sun_abs)%360
    is_waxing=moon_phase<180

    planet_data={}
    for k,n in PKEYS.items():
        p=getattr(m,k)
        ab=float(p.abs_pos)
        planet_data[n]={
            "abs":ab,"house":_house(ab,li),
            "retro":bool(getattr(p,'retrograde',False)),
            "speed":getattr(p,'longitude_speed',getattr(p,'speed',None)),
        }
    all_houses={n:d["house"] for n,d in planet_data.items()}

    results={}
    for k,name in PKEYS.items():
        d=planet_data[name];ab=d["abs"];house=d["house"];retro=d["retro"];spd=d["speed"]

        # Sthana Bala
        uccha  =_uccha_bala(name,ab)
        # _sapv now calculates all 7 vargas internally using _varga
        sapv   =_sapv(name,ab,house,all_houses)
        d9v    =_varga(ab, 9)
        ooja   =_ooja_yugma(name,ab,d9v)
        kendra =_kendradi(house)
        drek   =_drekkana(name,ab)
        sthana =uccha+sapv+ooja+kendra+drek

        # Dig Bala
        dig=_dig_bala(name,house)

        # Kala Bala (7 sub-components + Ayana)
        natho =_nathonnatha(name,is_day)
        paksha=_paksha_bala(name,moon_abs,sun_abs)
        tribha=_tribhaga(name,is_day,birth_dt,sunrise_dt,sunset_dt)
        vara  =_vara_bala(name,wd_sun)
        masa  =_masa_bala(name,moon_abs,sun_abs,birth_dt)
        varsha=_varsha_bala(name,yr,moon_abs,sun_abs,birth_dt)
        hora  =_hora_bala(name,wd_sun,birth_dt,sunrise_dt)
        ayana =_ayana_bala(name,ab)
        kala  =natho+paksha+tribha+vara+masa+varsha+hora+ayana

        # Chesta Bala
        chesta=_chesta_bala(name,retro,spd,paksha,ayana)

        # Naisargika + Drik
        nais=NAISARGIKA_BALA[name]
        drik=_drik_bala(name,house,all_houses,is_waxing)

        total=sthana+dig+kala+chesta+nais+drik
        rupas=round(total/60.0,2)
        req=SHADBALA_MIN_REQ[name]
        results[name]={
            "virupas":round(total,2),"rupas":rupas,"required":req,
            "ratio":round(rupas/req,2),"status":"PASS" if rupas>=req else "FAIL",
            "ishta_phala":round(math.sqrt(max(0,uccha*chesta)),2),
            "kashta_phala":round(math.sqrt(max(0,(60-uccha)*max(0,60-chesta))),2),
            "components":{
                "sthana":round(sthana,2),"dig":round(dig,2),
                "kala":round(kala,2),"chesta":round(chesta,2),
                "naisargika":round(nais,2),"drik":round(drik,2),
                "kala_detail":{"nathonnatha":natho,"paksha":round(paksha,2),
                    "tribhaga":tribha,"vara":vara,"masa":masa,
                    "varsha":varsha,"hora":hora,"ayana":round(ayana,2)},
                "sthana_detail":{"uccha":uccha,"sapv":sapv,
                    "ooja":ooja,"kendradi":kendra,"drekkana":drek},
            }
        }

    results["Rahu"]={"rupas":round((results["Saturn"]["rupas"]+results["Venus"]["rupas"])/2,2)}
    results["Ketu"]={"rupas":round((results["Mars"]["rupas"]+results["Jupiter"]["rupas"])/2,2)}
    return results


def calculate_bhava_bala(subject) -> dict:
    m=subject.model()
    shadbala=calculate_shadbala_rupas(subject)
    lagna_abs=float(m.ascendant.abs_pos);li=_si(lagna_abs)
    PKEYS={'sun':'Sun','moon':'Moon','mars':'Mars','mercury':'Mercury',
           'jupiter':'Jupiter','venus':'Venus','saturn':'Saturn'}
    planet_houses={}
    occupant_vir={h:0.0 for h in range(1,13)}
    for k,n in PKEYS.items():
        p=getattr(m,k);h=_house(float(p.abs_pos),li)
        planet_houses[n]=h
        occupant_vir[h]+=shadbala[n]["virupas"]*0.5
    bdg={h:(60 if h in{1,4,7,10} else(30 if h in{2,5,8,11} else 15)) for h in range(1,13)}
    BENEFICS={"Jupiter","Venus","Mercury"}
    MALEFICS={"Sun","Mars","Saturn"}
    asp={h:0.0 for h in range(1,13)}
    for planet,ph in planet_houses.items():
        wt=shadbala[planet]["virupas"]/600.0
        sign=1 if planet in BENEFICS else(-1 if planet in MALEFICS else 0)
        for h in range(1,13):
            fwd=(ph-h)%12;c=0.0
            if fwd==6: c=15.0
            elif planet=="Mars"    and fwd in{3,7}: c=11.25
            elif planet=="Jupiter" and fwd in{4,8}: c=11.25
            elif planet=="Saturn"  and fwd in{2,9}: c=11.25
            asp[h]+=c*wt*sign
    scores={}
    for h in range(1,13):
        lord=SIGN_LORDS[(li+h-1)%12]
        scores[h]=shadbala[lord]["virupas"]+bdg[h]+occupant_vir[h]+max(0,asp[h]*10)
    srt=sorted(scores.items(),key=lambda x:-x[1])
    ranks={h:i+1 for i,(h,_) in enumerate(srt)}
    return {h:{"virupas":round(scores[h],2),"rupas":round(scores[h]/60.0,2),"rank":ranks[h]}
            for h in range(1,13)}
