import sys
sys.path.insert(0, 'backend')
from core.astro_engine import get_natal_chart
from core.ashtakavarga import calculate_ashtakavarga
from core.shadbala_engine import calculate_shadbala_rupas, calculate_bhava_bala

natal = get_natal_chart()

print("=== ASHTAKAVARGA SAV (House Totals) ===")
av = calculate_ashtakavarga(natal)
sav = av['sarvashtakavarga']
expected_sav = {1:26,2:43,3:30,4:25,5:24,6:34,7:22,8:29,9:29,10:18,11:28,12:29}
for h in range(1, 13):
    g = sav[h]; e = expected_sav[h]
    tag = "OK" if g == e else "WRONG"
    print(f"  H{h}: got={g} exp={e} [{tag}]")
print(f"Grand Total: {av['grand_total']} (expected 337)")

print()
print("=== BAV per Planet (Houses 1-12) ===")
bav_h = av['bhinnashtakavarga_by_house']
expected_bav = {
    'sun':    [5,5,6,2,5,4,1,4,4,2,5,5],
    'moon':   [5,7,3,4,1,6,5,4,3,6,3,2],
    'mars':   [1,6,4,3,2,5,2,3,4,2,4,3],
    'mercury':[6,6,4,5,5,5,4,3,4,2,5,5],
    'jupiter':[4,7,4,3,6,4,4,7,5,3,3,6],
    'venus':  [4,6,4,6,3,5,5,5,3,2,4,5],
    'saturn': [1,6,5,2,2,5,1,3,6,1,4,3],
}
for p in ['sun','moon','mars','mercury','jupiter','venus','saturn']:
    got = [bav_h[p][h] for h in range(1,13)]
    exp = expected_bav[p]
    tag = "OK" if got == exp else "DIFF"
    print(f"  {p}: {got}")
    if got != exp:
        print(f"  EXP: {exp} [{tag}]")
    else:
        print(f"  [{tag}]")

print()
print("=== SHADBALA (Rupas) ===")
shad = calculate_shadbala_rupas(natal)
expected_shad = {'Sun':9.41,'Moon':5.83,'Mars':6.34,'Mercury':8.11,'Jupiter':6.21,'Venus':6.35,'Saturn':4.59}
for p, exp in expected_shad.items():
    got = shad.get(p, {}).get('rupas', '?')
    if isinstance(got, float):
        ratio = round(got/exp, 2)
        tag = "CLOSE" if abs(got - exp) < 1.0 else "FAR"
    else:
        ratio = '?'; tag = '?'
    print(f"  {p}: got={got} exp={exp} ratio={ratio} [{tag}]")

print()
print("=== BHAVA BALA (Rank order) ===")
bhava = calculate_bhava_bala(natal)
exp_rank = {1:3,2:8,3:10,4:6,5:11,6:12,7:9,8:5,9:4,10:2,11:7,12:1}
for h in range(1,13):
    g = bhava[h]['rank']; e = exp_rank[h]
    tag = "OK" if g == e else "diff"
    print(f"  H{h}: rank_got={g} rank_exp={e} rupas={bhava[h]['rupas']} [{tag}]")
