"""Nudge vias (and FID1) away from clearance violations; keep a move only if DRC strictly improves.
usage: nudge.py <pcb>   (pcb must have a sibling .kicad_pro)"""
import sys, os, json, math, shutil, subprocess, collections
PY = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
CLI = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
pcb = sys.argv[1]
tmp = pcb[:-10] + '_try.kicad_pcb'; shutil.copy(pcb[:-10] + '.kicad_pro', tmp[:-10] + '.kicad_pro')
def drc(p):
    subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', p + '.j', p], capture_output=True)
    d = json.load(open(p + '.j')); c = collections.Counter(v['type'] for v in d['violations'])
    score = c['clearance'] + c['hole_clearance'] + 1000 * (c['shorting_items'] + c['tracks_crossing'] + c['track_dangling'] + c['via_dangling'] + c['drill_out_of_range'] + c['track_width']) + 50 * len(d['unconnected_items'])
    return score, d
def mover(src, dst, ref_or_pos, dx, dy):
    code = f'''
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard({src!r}); mmf = pcbnew.ToMM
tgt = {ref_or_pos!r}
if isinstance(tgt, str):
    f = b.FindFootprintByReference(tgt); f.SetPosition(VECTOR2I(f.GetX() + mm({dx}), f.GetY() + mm({dy})))
else:
    x, y = tgt
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' and abs(mmf(t.GetX()) - x) < 0.06 and abs(mmf(t.GetY()) - y) < 0.06:
            via = t; break
    old = via.GetPosition(); new = VECTOR2I(old.x + mm({dx}), old.y + mm({dy}))
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_TRACK':
            if abs(t.GetStart().x - old.x) < 2000 and abs(t.GetStart().y - old.y) < 2000: t.SetStart(new)
            if abs(t.GetEnd().x - old.x) < 2000 and abs(t.GetEnd().y - old.y) < 2000: t.SetEnd(new)
    via.SetPosition(new)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save({dst!r})
'''
    subprocess.run([PY, '-c', code], capture_output=True)
base, d = drc(pcb); print('base', base)
done = set()
while True:
    cands = []
    for v in d['violations']:
        if v['type'] != 'clearance':
            continue
        its = v['items']
        for a, o in ((0, 1), (1, 0)):
            ia, io = its[a], its[o]
            if ia['description'].startswith('Via') or ia['description'].startswith('Pad [<no net>] of FID1'):
                cands.append((ia, io))
    cands = [c for c in cands if (c[0]['uuid']) not in done]
    if not cands:
        break
    ia, io = cands[0]; done.add(ia['uuid'])
    px, py = ia['pos']['x'], ia['pos']['y']; qx, qy = io['pos']['x'], io['pos']['y']
    n = math.hypot(px - qx, py - qy) or 1; ux, uy = (px - qx) / n, (py - qy) / n
    tgt = 'FID1' if 'FID1' in ia['description'] else (round(px, 3), round(py, 3))
    ok = False
    for dist in (0.1, 0.2, 0.3, 0.45):
        for ang in (0, 35, -35, 70, -70):
            c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            dx, dy = dist * (ux * c - uy * s), dist * (ux * s + uy * c)
            mover(pcb, tmp, tgt, dx, dy)
            if not os.path.exists(tmp):
                continue
            sc, d2 = drc(tmp)
            os.remove(tmp)
            if sc < base:
                mover(pcb, pcb + '.new.kicad_pcb', tgt, dx, dy); shutil.move(pcb + '.new.kicad_pcb', pcb)
                base, d = drc(pcb); print('moved', ia['description'][:30], 'by', round(dx, 2), round(dy, 2), '->', base); ok = True; break
        if ok:
            break
    if not ok:
        print('could not fix', ia['description'][:40], px, py)
print('end', base)
