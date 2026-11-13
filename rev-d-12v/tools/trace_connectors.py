"""Independent connectivity trace (does not use KiCad's DRC): for every pad of every connector, walk the copper
(track ends, vias, pads, filled zones) and report which other pads it reaches and over which layers.
usage: trace_connectors.py <pcb> [REF ...]"""
import sys, math, collections
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
want = sys.argv[2:]
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
by_net = collections.defaultdict(lambda: {"pads": [], "trk": [], "via": [], "zone": []})
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname(): by_net[p.GetNetname()]["pads"].append((fp.GetReference(), p))
for t in b.GetTracks():
    by_net[t.GetNetname()]["via" if t.GetClass() == "PCB_VIA" else "trk"].append(t)
for z in b.Zones():
    if not z.GetIsRuleArea(): by_net[z.GetNetname()]["zone"].append(z)
def on_seg(p, t, tol):
    a, c = t.GetStart(), t.GetEnd(); dx, dy = c.x - a.x, c.y - a.y; L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / L))
    return math.hypot(p.x - (a.x + u * dx), p.y - (a.y + u * dy)) <= tol
def samples(t, step=200000):
    a, c = t.GetStart(), t.GetEnd(); n = max(1, int(math.hypot(c.x - a.x, c.y - a.y) // step))
    return [pcbnew.VECTOR2I(int(a.x + (c.x - a.x) * i / n), int(a.y + (c.y - a.y) * i / n)) for i in range(n + 1)]
def trace(net, ref, pad):
    n = by_net[net]; items = [("pad", r, p) for r, p in n["pads"]] + [("trk", None, t) for t in n["trk"]] + [("via", None, v) for v in n["via"]]
    for z in n["zone"]:
        for l in z.GetLayerSet().Seq():
            ps = z.GetFilledPolysList(l)
            for i in range(ps.OutlineCount()): items.append(("zone", (l, i), ps))
    def layers(it):
        k, x, o = it
        if k == "trk": return {o.GetLayer()}
        if k == "via": return set(CU)
        if k == "pad": return set(l for l in CU if o.IsOnLayer(l))
        return {x[0]}
    def touch(a, c):
        if not (layers(a) & layers(c)): return False
        ka, kc = a[0], c[0]
        if ka > kc: a, c = c, a; ka, kc = kc, ka
        A, C = a[2], c[2]
        if (ka, kc) == ("trk", "trk"):
            w = (A.GetWidth() + C.GetWidth()) // 2
            return any(on_seg(p, C, w) for p in (A.GetStart(), A.GetEnd())) or any(on_seg(p, A, w) for p in (C.GetStart(), C.GetEnd()))
        if (ka, kc) == ("trk", "via"): return on_seg(C.GetPosition(), A, (A.GetWidth() + C.GetWidth(pcbnew.F_Cu)) // 2)
        if (ka, kc) == ("pad", "trk"): return any(A.HitTest(q) for q in samples(C))
        if (ka, kc) == ("pad", "via"): return A.HitTest(C.GetPosition())
        if (ka, kc) == ("pad", "pad"): return False
        if (ka, kc) == ("via", "via"): return False
        if ka == "zone" and kc == "zone":      # same-net pours on one layer that overlap or abut are one piece of copper
            oa, oc = A.Outline(a[1][1]), C.Outline(c[1][1])
            if not oa.BBox().Intersects(oc.BBox()): return False
            for o1, o2 in ((oa, oc), (oc, oa)):
                for k in range(o1.PointCount()):
                    v = o1.CPoint(k)
                    if o2.PointInside(v) or o2.PointOnEdge(v, 30000): return True
            return False
        if kc == "zone" or ka == "zone":
            z, o = (c, a) if kc == "zone" else (a, c)
            out = z[2].Outline(z[1][1])
            pts = [o[2].GetPosition()] if o[0] in ("pad", "via") else (samples(o[2]) if o[0] == "trk" else [])
            if o[0] == "pad":   # solid or thermal-spoke connection: sample the pad outline and just outside it
                bb = o[2].GetBoundingBox(); cx, cy = o[2].GetPosition().x, o[2].GetPosition().y
                for k in range(16):
                    dx, dy = math.cos(k * math.pi / 8), math.sin(k * math.pi / 8)
                    for extra in (-50000, 60000, 150000):
                        pts.append(pcbnew.VECTOR2I(int(cx + dx * (bb.GetWidth() // 2 + extra)), int(cy + dy * (bb.GetHeight() // 2 + extra))))
            return any(out.PointInside(pcbnew.VECTOR2I(p.x, p.y)) for p in pts)
        return False
    start = [i for i, it in enumerate(items) if it[0] == "pad" and it[1] == ref and it[2].GetNumber() == pad.GetNumber()]
    seen = set(start); q = list(start)
    while q:
        i = q.pop()
        for j in range(len(items)):
            if j not in seen and touch(items[i], items[j]): seen.add(j); q.append(j)
    used = collections.Counter()
    for i in seen:
        k, x, o = items[i]
        if k == "trk": used[b.GetLayerName(o.GetLayer()).replace(".Cu", "")] += mm(o.GetLength())
        if k == "zone": used["pour:" + b.GetLayerName(x[0]).replace(".Cu", "")] += 0
    reached = sorted(set("%s.%s" % (items[i][1], items[i][2].GetNumber()) for i in seen if items[i][0] == "pad") - {"%s.%s" % (ref, pad.GetNumber())})
    allp = set("%s.%s" % (r, p.GetNumber()) for r, p in n["pads"]) - {"%s.%s" % (ref, pad.GetNumber())}
    return reached, sorted(allp - set(reached)), used, sum(1 for i in seen if items[i][0] == "via")
bad = 0
for fp in sorted(b.GetFootprints(), key=lambda f: (f.GetReference()[0], int("".join(ch for ch in f.GetReference() if ch.isdigit()) or 0))):
    r = fp.GetReference()
    if (want and r not in want) or (not want and r[0] != "J"): continue
    done = set()
    for p in fp.Pads():
        if not p.GetNetname() or p.GetNumber() in done: continue
        done.add(p.GetNumber())
        reached, missing, used, nv = trace(p.GetNetname(), r, p)
        if missing: bad += 1
        lay = ", ".join("%s %.0f mm" % (k, v) if v else k for k, v in sorted(used.items()))
        print("%-4s pin %-2s %-22s -> %-3d pads%s | %s%s | e.g. %s" % (r, p.GetNumber(), p.GetNetname().split("/")[-1][:22], len(reached), " (ALL)" if not missing else " MISSING %d: %s" % (len(missing), missing[:6]), lay, ", %d vias" % nv if nv else "", ", ".join(reached[:4])))
print("pads with unreached net members:", bad)
