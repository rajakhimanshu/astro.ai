from backend.core.astro_engine import get_natal_chart
from backend.core.ashtakavarga import calculate_ashtakavarga, format_ashtakavarga_for_ai

try:
    subject = get_natal_chart()
    print("NATAL SUBJECT LOADED SUCCESSFULLY\n")
    
    av_data = calculate_ashtakavarga(subject)
    print(format_ashtakavarga_for_ai(av_data))
    
    print("\nIndividual House SAV Scores:")
    for h in range(1, 13):
        print(f"House {h}: {av_data['sarvashtakavarga'][f'house_{h}']}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
