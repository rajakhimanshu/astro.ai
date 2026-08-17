"""
core/jaimini_padas.py
────────────────────────────────────────────────────
Jaimini Pada Engine (Micro-Predictions)
Tracks planetary transits through sign subdivisions (Navamshas/Padas)
for precise weekly/monthly timing.
────────────────────────────────────────────────────
"""
from datetime import datetime, timedelta
from core.astro_engine import get_current_sky, SIGNS

class JaiminiPadaEngine:
    def determine_pada(self, degree_in_sign):
        # 9 padas per sign, each 3°20' (200 minutes)
        pada_idx = int(degree_in_sign // (30/9))
        return pada_idx + 1

    def get_current_pada_snapshot(self):
        sky = get_current_sky()
        m = sky.model()
        planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'saturn', 'true_north_lunar_node']
        
        snapshot = {}
        for p in planets:
            obj = getattr(m, p)
            name = "Rahu" if p == 'true_north_lunar_node' else p.capitalize()
            deg = obj.position
            pada = self.determine_pada(deg)
            # Navamsha sign calculation
            sign_idx = int(obj.abs_pos // 30)
            # Standard Navamsha starting signs (Fire/Earth/Air/Water)
            starts = [0, 9, 6, 3, 0, 9, 6, 3, 0, 9, 6, 3]
            nav_sign_idx = (starts[sign_idx] + (pada - 1)) % 12
            
            snapshot[name] = {
                "sign": obj.sign,
                "pada": pada,
                "nav_sign": SIGNS[nav_sign_idx],
                "degree": round(deg, 2)
            }
        return snapshot

    def predict_micro_events(self, snapshot):
        events = []
        # Key interpretations based on current pada
        jup = snapshot['Jupiter']
        if jup['pada'] in [1, 5, 9]:
            events.append("Jupiter in Dharma-Pada: Week supports higher wisdom, teaching, and moral clarity.")
        elif jup['pada'] in [2, 6]:
            events.append("Jupiter in Artha-Pada: Week focuses on material consolidation and financial planning.")
        
        sat = snapshot['Saturn']
        if sat['pada'] in [4, 8]:
            events.append("Saturn in Moksha-Pada: Internal reflection and letting go of outdated structures is the theme.")
            
        return events

def format_pada_report(snapshot, events):
    lines = ["JAIMINI PADA MICRO-TIMING (Current Week):"]
    for name, data in snapshot.items():
        lines.append(f"  {name:8} in {data['sign']} Pada {data['pada']} ({data['nav_sign']} Navamsha)")
    lines.append("\n  [Micro-Narratives]:")
    for e in events:
        lines.append(f"  - {e}")
    return "\n".join(lines)
