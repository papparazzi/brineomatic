"""Brute-force a 2-via B.Cu (or F.Cu) connection between two points of one net using the strict DRC metric.
usage: route_pair.py <pcb> <net> x1 y1 x2 y2"""
import sys, os, json, shutil, subprocess, collections, itertools
PY = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
CLI = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
H = os.path.dirname(os.path.abspath(__file__))
pcb, net = sys.argv[1], sys.argv[2]; x1, y1, x2, y2 = map(float, sys.argv[3:7])
tmp = pcb[:-10] + '_try.kicad_pcb'; shutil.copy(pcb[:-10] + '.kicad_pro', tmp[:-10] + '.kicad_pro')
def drc(p):
    subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', p + '.j', p], capture_output=True)
    d = json.load(open(p + '.j')); c = collections.Counter(v['type'] for v in d['violations'])
    return sum(c[k] for k in ('clearance', 'track_dangling', 'via_dangling', 'hole_clearance', 'track_width', 'drill_out_of_range', 'annular_width')) + 1000 * (c['shorting_items'] + c['tracks_crossing']), len(d['unconnected_items'])
b0, u0 = drc(pcb); print('base', b0, u0)
offs = [(0, 1.3), (0, -1.3), (1.3, 0), (-1.3, 0), (1.3, 1.3), (-1.3, -1.3), (1.3, -1.3), (-1.3, 1.3)]
n = 0
for o1, o2 in itertools.product(offs, offs):
    a = (x1 + o1[0], y1 + o1[1]); z = (x2 + o2[0], y2 + o2[1])
    for mid in (None, (z[0], a[1]), (a[0], z[1])):
        spec = [['F', x1, y1, a[0], a[1], 0.25], ['via', a[0], a[1]]]
        pts = [a] + ([mid] if mid else []) + [z]
        for p, q in zip(pts, pts[1:]):
            spec.append(['B', p[0], p[1], q[0], q[1], 0.25])
        spec += [['via', z[0], z[1]], ['F', z[0], z[1], x2, y2, 0.25]]
        json.dump(spec, open(pcb + '.s.json', 'w'))
        subprocess.run([PY, os.path.join(H, 'pcb_addtrack.py'), pcb, tmp, net, pcb + '.s.json'], capture_output=True)
        if not os.path.exists(tmp): continue
        b, u = drc(tmp); n += 1
        if b <= b0 + 1 and u < u0:
            shutil.move(tmp, pcb); print('ACCEPT', a, mid, z, b, u); sys.exit(0)
        os.remove(tmp)
print('none of', n)
