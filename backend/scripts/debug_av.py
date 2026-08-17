from core.astro_engine import get_natal_chart
from core.ashtakavarga import calculate_ashtakavarga

try:
    subject = get_natal_chart()
    av = calculate_ashtakavarga(subject)
    print("Sarvashtakavarga (SAV) results:")
    for h, score in av['sarvashtakavarga'].items():
        print(f"House {h}: {score}")
        
    print("\nSun BAV:")
    for h, score in av['bhinnashtakavarga'].items():
        print(f"House {h}: {score['sun']}")
except Exception as e:
    import traceback
    traceback.print_exc()
