"""
core/karmic_engine.py
────────────────────────────────────────────────────
Karmic Narrative Engine
Interprets the chart as a soul journey using Rahu-Ketu axis and Atmakaraka.
────────────────────────────────────────────────────
"""

class KarmicNarrativeEngine:
    def __init__(self, planets):
        self.planets = planets
        self.rahu = planets.get('Rahu')
        self.ketu = planets.get('Ketu')
        self.ak = self._find_atmakaraka()

    def _find_atmakaraka(self):
        # Already computed in profile, but fallback logic
        p_list = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        sorted_p = sorted([(p, self.planets[p]['degree']) for p in p_list if p in self.planets], key=lambda x: x[1], reverse=True)
        return sorted_p[0][0] if sorted_p else "Sun"

    def get_soul_story(self):
        if not self.rahu or not self.ketu:
            return "Karmic axis undefined."
            
        r_house = self.rahu['house']
        k_house = self.ketu['house']
        
        narrative = f"Your Atmakaraka (Soul King) is {self.ak}, indicating your deepest internal identity is forged through {self.ak}'s significations. "
        
        # Rahu-Ketu Axis
        if r_house == 11 and k_house == 5:
            narrative += "With Rahu in the 11th and Ketu in the 5th, your soul is moving away from purely individual creative expression (Ketu 5H) toward mass impact and large-scale social networks (Rahu 11H). You have past-life mastery in personal intelligence but must now learn to handle public gains and community leadership."
        elif r_house == 1 and k_house == 7:
             narrative += "Your soul seeks to develop independence and self-identity (Rahu 1H). Past lives were spent in deep partnerships (Ketu 7H). This life: Learn to stand alone."
        else:
            narrative += f"Your karmic path spans the {k_house}H-{r_house}H axis, moving from {k_house} house internal comfort toward {r_house} house worldly expansion."
            
        return narrative

def format_karmic_report(narrative):
    return f"SOUL JOURNEY & KARMIC PURPOSE: {narrative}"
