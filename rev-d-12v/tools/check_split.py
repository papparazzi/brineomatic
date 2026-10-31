"""Pin-for-pin check of the J1/J6 -> terminals split: old netlist vs new netlist.  usage: check_split.py old.xml new.xml"""
import sys, xml.etree.ElementTree as ET
def pins(p):
    r = ET.parse(p).getroot(); d = {}
    for n in r.find('nets'):
        for nd in n: d[(nd.get('ref'), nd.get('pin'))] = n.get('name')
    return d
a, b = pins(sys.argv[1]), pins(sys.argv[2])
mp = {('J1','1'):('J1','1'),('J1','3'):('J1','2'),('J1','5'):('J1','3'),('J1','2'):('J28','1'),('J1','4'):('J28','2'),('J1','6'):('J28','3'),
      ('J6','1'):('J6','1'),('J6','3'):('J6','2'),('J6','5'):('J6','3'),('J6','2'):('J29','1'),('J6','4'):('J29','2'),('J6','6'):('J29','3')}
bad = 0
for k, v in mp.items():
    ok = a[k] == b.get(v); bad += not ok
    print(f'{k[0]}.{k[1]} -> {v[0]}.{v[1]}: {a[k]} / {b.get(v)} {"OK" if ok else "MISMATCH"}')
old = {k: v for k, v in a.items() if k[0] not in ('J1', 'J6')}; new = {k: v for k, v in b.items() if k[0] not in ('J1', 'J6', 'J28', 'J29')}
diff = [k for k in set(old) | set(new) if old.get(k) != new.get(k)]
print('other pins that changed net:', diff, '| net names only in one netlist:', set(a.values()) ^ set(b.values()), '| split mismatches:', bad)
sys.exit(1 if bad or diff else 0)
