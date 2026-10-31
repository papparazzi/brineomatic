"""Try a GND (or other net) stitching via near a pad until DRC improves.  usage: via_search.py <pcb> <net> <x> <y>"""
import sys, os, json, shutil, subprocess, collections, math
PY = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
CLI = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
H = os.path.dirname(os.path.abspath(__file__))
pcb, net, x, y = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]); TOL = int(sys.argv[5]) if len(sys.argv) > 5 else 0
tmp = pcb[:-10] + '_try.kicad_pcb'; shutil.copy(pcb[:-10] + '.kicad_pro', tmp[:-10] + '.kicad_pro')
def drc(p):
    subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', p + '.j', p], capture_output=True)
    d = json.load(open(p + '.j')); c = collections.Counter(v['type'] for v in d['violations'])
    return sum(c[k] for k in ('clearance', 'track_dangling', 'via_dangling', 'hole_clearance', 'track_width', 'drill_out_of_range', 'annular_width')) + 1000 * (c['shorting_items'] + c['tracks_crossing']), len(d['unconnected_items'])
b0, u0 = drc(pcb); print('base', b0, u0)
cands = sorted(((dx, dy) for dx in [i * 0.5 for i in range(-8, 9)] for dy in [i * 0.5 for i in range(-8, 9)] if 0.9 <= math.hypot(dx, dy) <= 3.5), key=lambda t: math.hypot(*t))
for dx, dy in cands:
    spec = [['F', x, y, x + dx, y + dy, 0.3], ['via', x + dx, y + dy]]
    json.dump(spec, open(pcb + '.s.json', 'w'))
    subprocess.run([PY, os.path.join(H, 'pcb_addtrack.py'), pcb, tmp, net, pcb + '.s.json'], capture_output=True)
    if not os.path.exists(tmp): continue
    b, u = drc(tmp)
    if b <= b0 + TOL and u < u0:
        shutil.move(tmp, pcb); print('ACCEPT via at', x + dx, y + dy, b, u); break
    os.remove(tmp)
else:
    print('no via position works')
