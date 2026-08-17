import sys; sys.path.insert(0,'backend')
from core.astro_engine import get_natal_chart
from core.shadbala_engine import calculate_shadbala_rupas
natal = get_natal_chart()
shad = calculate_shadbala_rupas(natal)
planets = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']
exp = {'Sun':564.52,'Moon':349.99,'Mars':380.63,'Mercury':486.48,'Jupiter':372.31,'Venus':381.28,'Saturn':275.21}
for p in planets:
    d = shad[p]
    c = d['components']
    kd = c['kala_detail']
    got = d['virupas']; expected = exp[p]
    diff = round(expected - got, 1)
    print(p + ": got=" + str(got) + " exp=" + str(expected) + " DIFF=" + str(diff))
    print("  Sthana=" + str(c['sthana']) + " Dig=" + str(c['dig']) + " Kala=" + str(c['kala']) + " Chesta=" + str(c['chesta']) + " Nais=" + str(c['naisargika']) + " Drik=" + str(c['drik']))
    print("  Kala: natho=" + str(kd['natho']) + " paksha=" + str(kd['paksha']) + " tribha=" + str(kd['tribhaga']) + " hora=" + str(kd['hora']) + " dina=" + str(kd['dina']) + " masa=" + str(kd['masa']) + " varsha=" + str(kd['varsha']) + " ayana=" + str(kd['ayana']))
    print()
