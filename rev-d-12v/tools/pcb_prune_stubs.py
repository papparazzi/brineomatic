"""Remove dangling track/via stubs (ends touching nothing) iteratively.  usage: pcb_prune_stubs.py in out [net1,net2,...]   (optional: only prune these nets)"""
import sys, pcbnew
TOL = 1000
ONLY = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None
b = pcbnew.LoadBoard(sys.argv[1])
def key(p): return (round(p.x / TOL), round(p.y / TOL))
total = 0
for _once in (1,):
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox(); pads.setdefault(p.GetNetname(), []).append((bb, p))
    trk = [t for t in b.GetTracks()]
    ends = {}   # (net, layer-ish) -> count by point
    def pts(t):
        if t.GetClass() == 'PCB_VIA': return [(t.GetPosition(), None)]
        return [(t.GetStart(), t.GetLayer()), (t.GetEnd(), t.GetLayer())]
    cnt = {}
    for t in trk:
        for p, L in pts(t):
            cnt.setdefault((t.GetNetname(), key(p)), []).append((t, L))
    rm = []
    for t in trk:
        if ONLY is not None and t.GetNetname() not in ONLY: continue
        if t.GetClass() == 'PCB_VIA':
            ok = False
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                pass
            n = sum(1 for o, _ in cnt[(t.GetNetname(), key(t.GetPosition()))] if o is not t)
            padhit = any(bb.Contains(t.GetPosition()) for bb, _ in pads.get(t.GetNetname(), []))
            zone = False
            if n == 0 and not padhit:
                # via may connect to a zone: keep if inside a zone of same net
                for z in b.Zones():
                    if z.GetNetname() == t.GetNetname() and z.HitTestFilledArea(pcbnew.F_Cu, t.GetPosition()): zone = True
                    if z.GetNetname() == t.GetNetname() and z.HitTestFilledArea(pcbnew.B_Cu, t.GetPosition()): zone = True
                    if z.GetNetname() == t.GetNetname() and z.HitTestFilledArea(pcbnew.In1_Cu, t.GetPosition()): zone = True
                if not zone: rm.append(t)
            continue
        bad = False
        for p, L in pts(t):
            others = [o for o, _ in cnt[(t.GetNetname(), key(p))] if o is not t]
            same = [o for o in others if o.GetClass() == 'PCB_VIA' or o.GetLayer() == L]
            padhit = any(bb.Contains(p) and q.IsOnLayer(L) for bb, q in pads.get(t.GetNetname(), []))
            zone = any(z.GetNetname() == t.GetNetname() and z.HitTestFilledArea(L, p) for z in b.Zones())
            if not same and not padhit and not zone: bad = True
        if bad: rm.append(t)
    for t in rm: b.Remove(t)
    total += len(rm)
print('removed', total)
b.Save(sys.argv[2])
