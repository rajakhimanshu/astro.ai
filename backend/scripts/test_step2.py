from backend.core.astro_engine import get_natal_chart, get_strength_summary

try:
    subject = get_natal_chart()
    print("NATAL SUBJECT LOADED SUCCESSFULLY\n")
    
    summary = get_strength_summary(subject)
    print(summary)
    
except Exception as e:
    import traceback
    traceback.print_exc()
