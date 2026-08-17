"""
core/bhava_chalit.py
────────────────────────────────────────────────────
Bhava Chalit (Actual House Placement)
Calculates actual house placement based on Bhava Madhya.
────────────────────────────────────────────────────
"""

def get_bhava_madhya(asc_abs_pos):
    """
    Equal house Bhava Madhya — each house midpoint is 30° apart from ascendant.
    For unequal houses use Placidus/Koch cusps from Swiss Ephemeris.
    """
    madhyas = []
    for i in range(12):
        madhya = (asc_abs_pos + i * 30) % 360
        madhyas.append(madhya)
    return madhyas

def get_bhava_chalit_house(planet_abs_pos, house_cusps_abs):
    """
    house_cusps_abs: list of 12 absolute positions of house MIDPOINTS (Bhava Madhya)
    A planet belongs to the house whose midpoint it is closest to
    """
    # Calculate Bhava Sandhi (house boundaries) = midpoint between adjacent Bhava Madhyas
    sandhis = []
    for i in range(12):
        mid = (house_cusps_abs[i] + house_cusps_abs[(i+1) % 12]) / 2
        # Handle wrap-around when averaging
        if abs(house_cusps_abs[i] - house_cusps_abs[(i+1) % 12]) > 180:
            mid = (mid + 180) % 360
        sandhis.append(mid % 360)
    
    # Find which Bhava the planet falls in
    for i in range(12):
        start = sandhis[i]
        end   = sandhis[(i+1) % 12]
        
        if start <= end:
            if start <= planet_abs_pos < end:
                return i + 1
        else:  # wraps around 360
            if planet_abs_pos >= start or planet_abs_pos < end:
                return i + 1
    
    return 1  # fallback
