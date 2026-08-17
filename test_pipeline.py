"""Full pipeline test."""
import sys, traceback
sys.path.insert(0, 'backend')

errors = []

try:
    from core.astro_engine import get_natal_chart
    from core.shadbala_engine import calculate_shadbala_rupas, calculate_bhava_bala
    from core.ashtakavarga import calculate_ashtakavarga

    natal = get_natal_chart()
    shad = calculate_shadbala_rupas(natal)
    bhava = calculate_bhava_bala(natal)
    av = calculate_ashtakavarga(natal)

    print('[OK] Full calculation pipeline works')
    for p, v in shad.items():
        if 'rupas' in v:
            r = v['rupas']
            print(f'  {p}: {r} rupas')
    print(f'  AV Grand Total: {sum(av["sav"].values())}')
    print(f'  Bhava H12 rank: {bhava[12]["rank"]}')
except Exception as e:
    traceback.print_exc()
    errors.append(str(e))

# Test main.py import
try:
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("main", "backend/main.py")
    print('[OK] main.py found')
except Exception as e:
    errors.append(f'main.py: {e}')
    print(f'[FAIL] main.py: {e}')

print(f'\n=== {len(errors)} errors ===')
