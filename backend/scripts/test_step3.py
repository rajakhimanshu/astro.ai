from backend.core.astro_engine import get_natal_chart
from backend.core.yoga_engine import detect_all_yogas, format_yogas_for_ai

try:
    subject = get_natal_chart()
    print("NATAL SUBJECT LOADED SUCCESSFULLY\n")
    
    yogas = detect_all_yogas(subject)
    print(format_yogas_for_ai(yogas))
    
except Exception as e:
    import traceback
    traceback.print_exc()
