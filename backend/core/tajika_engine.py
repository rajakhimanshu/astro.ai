"""
core/tajika_engine.py
────────────────────────────────────────────────────
Tajika Annual Chart (Varshaphal) Engine
Computes the Solar Return chart for the upcoming year.
────────────────────────────────────────────────────
"""
from datetime import datetime
from core.astro_engine import get_sky_on_date, SIGNS

class TajikaEngine:
    def __init__(self, natal_chart):
        self.natal = natal_chart
        self.natal_sun = natal_chart.model().sun.abs_pos

    def get_varshaphal(self, year):
        # We find a date near the birthday where Sun is at natal Sun degree
        # Simplified for proxy: Birthday at 12:00 PM
        bd = {
            'year': year,
            'month': self.natal.month,
            'day': self.natal.day,
            'city': self.natal.city,
            'nation': self.natal.nation
        }
        annual_sky = get_sky_on_date(bd['year'], bd['month'], bd['day'], city=bd['city'], nation=bd['nation'])
        m = annual_sky.model()
        
        # Muntha: moves 1 sign per year from Lagna
        # Age at that year
        age = year - self.natal.year
        
        SIGN_MAP = {
            "Ari": 0, "Tau": 1, "Gem": 2, "Can": 3, "Leo": 4, "Vir": 5,
            "Lib": 6, "Sco": 7, "Sag": 8, "Cap": 9, "Aqu": 10, "Pis": 11,
            "Aries": 0, "Taurus": 1, "Gemini": 2, "Cancer": 3, "Leo": 4, "Virgo": 5,
            "Libra": 6, "Scorpio": 7, "Sagittarius": 8, "Capricorn": 9, "Aquarius": 10, "Pisces": 11
        }
        
        natal_lagna_idx = SIGN_MAP.get(self.natal.model().ascendant.sign, 0)
        muntha_sign_idx = (natal_lagna_idx + age) % 12
        
        return {
            "year": year,
            "lagna": m.ascendant.sign,
            "muntha": SIGNS[muntha_sign_idx],
            "year_lord": self._determine_year_lord(m.ascendant.sign)
        }

    def _determine_year_lord(self, lagna):
        # Simplified: Lagna Lord is the year lord
        SIGN_LORDS = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
            "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
            "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        return SIGN_LORDS.get(lagna, "Sun")

def format_tajika_report(data):
    return f"TAJIKA ANNUAL CHART ({data['year']}): Lagna: {data['lagna']} | Year Lord: {data['year_lord']} | Muntha: {data['muntha']} House (Moving karmic focus)."
