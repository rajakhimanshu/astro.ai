from core.astro_engine import get_natal_chart, get_current_sky, format_detailed_report
import os
from datetime import datetime

def run_system_test():
    print("-> Running system test and generating output.txt...")
    
    # 1. Get Natal Chart
    natal = get_natal_chart()
    natal_m = natal.model()
    natal_asc_pos = natal_m.ascendant.abs_pos
    natal_moon_pos = natal_m.moon.abs_pos
    
    natal_report = format_detailed_report(natal)
    
    # 2. Get Current Sky
    current = get_current_sky()
    
    # Transit Section 1: From Natal Lagna (Virgo)
    transit_lagna_report = format_detailed_report(
        current, 
        reference_abs_pos=natal_asc_pos, 
        reference_name="Birth Lagna (Virgo)"
    )
    
    # Transit Section 2: From Natal Moon (Cancer)
    transit_moon_report = format_detailed_report(
        current, 
        reference_abs_pos=natal_moon_pos, 
        reference_name="Birth Moon (Cancer)"
    )
    
    # 3. Combine and write to file
    full_output = "==========================================================================================\n"
    full_output += "                                JYOTISH AI - SYSTEM REPORT                                \n"
    full_output += "==========================================================================================\n\n"
    
    full_output += "--- [1] BIRTH (NATAL) CHART ---\n"
    full_output += natal_report
    full_output += "\n\n"
    
    full_output += "--- [2] CURRENT TRANSITS (Relative to your Birth Lagna) ---\n"
    full_output += "This shows how today's planets are placed in houses starting from your Lagna (Virgo).\n"
    full_output += transit_lagna_report
    full_output += "\n\n"
    
    full_output += "--- [3] CURRENT TRANSITS (Relative to your Birth Moon) ---\n"
    full_output += "This shows how today's planets are placed in houses starting from your Moon (Cancer).\n"
    full_output += transit_moon_report
    full_output += "\n\n"
    
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    full_output += f"Last Updated: {timestamp}\n"
    
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(full_output)
    
    print("✅ Success! Check 'output.txt' for your updated report.")

if __name__ == "__main__":
    run_system_test()
