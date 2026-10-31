"""Greedy gap closer: for each net, join islands with F.Cu/B.Cu jumpers that do not add DRC violations.
usage: close_gaps.py <pcb> <net> [net ...]   (edits <pcb> in place; uses kicad-cli + KiCad python)"""
import sys, os, json, math, subprocess, shutil, itertools, collections
PY = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
CLI = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
HERE = os.path.dirname(os.path.abspath(__file__))
pcb, nets = sys.argv[1], sys.argv[2:]
tmp = pcb[:-10] + '_try.kicad_pcb'
for suf in ('.kicad_pro',):
    shutil.copy(pcb[:-10] + suf, tmp[:-10] + suf)
def run(*a):
    return subprocess.run(a, capture_output=True, text=True)
def drc(path):
    run(CLI, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', path + '.drc.json', path)
    d = json.load(open(path + '.drc.json'))
    c = collections.Counter(v['type'] for v in d['violations'])
    bad = c['clearance'] + c['shorting_items'] + c['track_dangling'] + c['via_dangling'] + c['hole_clearance'] + c['drill_out_of_range'] + 1000 * (c['shorting_items'] + c['tracks_crossing']) + c['track_width'] + c['via_diameter'] + c['annular_width']
    return bad, len(d['unconnected_items'])
def islands():
    r = run(PY, os.path.join(HERE, 'pcb_islands.py'), pcb, pcb + '.isl.json', *nets)
    return json.load(open(pcb + '.isl.json'))
def cands(p, q, w):
    (x1, y1), (x2, y2) = p, q
    L = []
    L.append([['F', x1, y1, x2, y2, w]])
    L.append([['F', x1, y1, x2, y1, w], ['F', x2, y1, x2, y2, w]])
    L.append([['F', x1, y1, x1, y2, w], ['F', x1, y2, x2, y2, w]])
    d = math.hypot(x2 - x1, y2 - y1) or 1
    o = 1.1
    a = (x1 + (x2 - x1) / d * o, y1 + (y2 - y1) / d * o); z = (x2 - (x2 - x1) / d * o, y2 - (y2 - y1) / d * o)
    if d > 2.5:
        L.append([['F', x1, y1, a[0], a[1], w], ['via', a[0], a[1]], ['B', a[0], a[1], z[0], z[1], w], ['via', z[0], z[1]], ['F', z[0], z[1], x2, y2, w]])
    return L
base_bad, base_unc = drc(pcb)
print('start', base_bad, base_unc)
tried = set()
while True:
    isl = islands()
    if not isl:
        break
    progress = False
    pairs = []
    for net, comps in isl.items():
        for i, j in itertools.combinations(range(len(comps)), 2):
            ranked = sorted(((math.hypot(a[1] - b[1], a[2] - b[2]), a, b) for a in comps[i] for b in comps[j]), key=lambda t: t[0])
            seen_refs = set()
            for r in ranked:
                key2 = (r[1][0].split('.')[0], r[2][0].split('.')[0])
                if key2 in seen_refs:
                    continue
                seen_refs.add(key2); pairs.append((r[0], net, r[1], r[2]))
                if len(seen_refs) >= 6:
                    break
    pairs.sort(key=lambda t: t[0])
    for dist, net, a, b in pairs:
        k = (net, a[0], b[0])
        if k in tried:
            continue
        tried.add(k)
        for spec in cands((a[1], a[2]), (b[1], b[2]), 0.3):
            json.dump(spec, open(pcb + '.spec.json', 'w'))
            run(PY, os.path.join(HERE, 'pcb_addtrack.py'), pcb, tmp, net, pcb + '.spec.json')
            if not os.path.exists(tmp):
                continue
            bad, unc = drc(tmp)
            print(' try', net, a[0], b[0], round(dist, 1), 'bad', bad, 'unc', unc)
            if bad <= base_bad and unc < base_unc:
                shutil.move(tmp, pcb); base_bad, base_unc = bad, unc; progress = True
                print('  ACCEPT', net, a[0], '->', b[0], 'bad', bad, 'unc', unc)
                break
            os.remove(tmp)
        if progress:
            break
    if not progress:
        break
print('end', base_bad, base_unc)
