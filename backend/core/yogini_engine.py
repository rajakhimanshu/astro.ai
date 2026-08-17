"""
core/yogini_engine.py
────────────────────────────────────────────────────
Yogini Dasha Engine
8-year female/creative cycle based on Moon nakshatra.
────────────────────────────────────────────────────
"""
from datetime import datetime, timedelta

YOGINI_NAMES  = ["Mangala","Pingala","Dhanya","Bhramari","Bhadrika","Ulka","Siddha","Sankata"]
YOGINI_LORDS  = ["Moon","Sun","Jupiter","Mars","Mercury","Saturn","Venus","Rahu"]
YOGINI_YEARS  = [1,2,3,4,5,6,7,8]  # years for each yogini

def get_yogini_dasha(moon_abs_pos, birth_date):
    nak_index = int(moon_abs_pos / (360/27))
    yogini_index = nak_index % 8
    
    yogini_lord = YOGINI_LORDS[yogini_index]
    total_years = YOGINI_YEARS[yogini_index]
    
    # Balance remaining in first yogini
    deg_in_nak = moon_abs_pos % (360/27)
    fraction_elapsed = deg_in_nak / (360/27)
    balance = total_years * (1 - fraction_elapsed)
    
    # Build full sequence for 5 cycles (~180 years)
    sequence = []
    current_date = birth_date
    
    for cycle in range(5):
        for i in range(8):
            idx = (yogini_index + i + cycle * 8) % 8
            name  = YOGINI_NAMES[idx]
            lord  = YOGINI_LORDS[idx]
            years = YOGINI_YEARS[idx] if (i > 0 or cycle > 0) else balance
            
            end_date = current_date + timedelta(days=years * 365.25)
            sequence.append({"yogini":name, "lord":lord, "start":current_date, "end":end_date, "years": years})
            current_date = end_date
    
    return sequence

def format_yogini_report(data):
    """Fallback for AI report formatting."""
    # Assuming 'data' is the sequence list
    if not data:
        return "[Yogini Dasha Unavailable]"
    
    now = datetime.now()
    current_y = None
    for d in data:
        if d['start'] <= now < d['end']:
            current_y = d
            break
            
    if not current_y:
        return "[Yogini Dasha Out of Bounds]"
        
    return f"YOGINI DASHA (8-Year Precise Cycle): Currently in {current_y['yogini']} ({current_y['lord']} energy) | Window: {current_y['start'].strftime('%b %Y')} to {current_y['end'].strftime('%b %Y')}"
