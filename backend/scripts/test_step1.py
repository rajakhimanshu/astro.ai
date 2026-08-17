from backend.core.astro_engine import get_natal_chart, get_d9_navamsa, get_d10_dashamsa, format_divisional_for_ai

try:
    subject = get_natal_chart()
    print("NATAL SUBJECT LOADED SUCCESSFULLY\n")
    
    d9 = get_d9_navamsa(subject)
    print(format_divisional_for_ai(d9, "D9 Navamsa"))
    print("\n" + "="*30 + "\n")
    
    d10 = get_d10_dashamsa(subject)
    print(format_divisional_for_ai(d10, "D10 Dashamsa"))
    
except Exception as e:
    import traceback
    traceback.print_exc()
