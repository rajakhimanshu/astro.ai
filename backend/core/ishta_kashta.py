"""
core/ishta_kashta.py
────────────────────────────────────────────────────
Ishta/Kashta Phala
Measures how benefic vs malefic a planet actually is functioning.
────────────────────────────────────────────────────
"""
import math

def ishta_kashta_phala(uccha_bala, chesta_bala):
    """
    Measures how benefic vs malefic a planet actually is functioning based on Shadbala components.
    """
    ishta  = round(math.sqrt(max(0, uccha_bala * chesta_bala)), 4)
    kashta = round(math.sqrt(max(0, (60 - uccha_bala) * (60 - chesta_bala))), 4)
    
    ratio = ishta / (ishta + kashta) if (ishta + kashta) > 0 else 0.5
    
    if ratio >= 0.65:   nature = "Strongly Benefic"
    elif ratio >= 0.55: nature = "Mildly Benefic"
    elif ratio >= 0.45: nature = "Neutral"
    elif ratio >= 0.35: nature = "Mildly Malefic"
    else:               nature = "Strongly Malefic"
    
    return {
        "ishta": ishta, 
        "kashta": kashta, 
        "ratio": round(ratio, 4), 
        "nature": nature
    }
