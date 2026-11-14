"""Copper network analysis of one net: bottleneck (widest) path and DC resistance between pads.
usage: cunet.py <board> <outer_um> <inner_um> <net> <SRC ref.pad> <DST ref.pad> [<DST2> ...]
Zone islands are treated as ideal (zero-resistance) nodes, so resistances are lower bounds when pours are involved."""
import sys, math, collections
import pcbnew

bf = sys.argv[1]
T_OUT = float(sys.argv[2]) * 1e-6
T_IN = float(sys.argv[3]) * 1e-6
net = sys.argv[4]
src = sys.argv[5]
dsts = sys.argv[6:]
RHO = 1.72e-8
VIA_PLATE = 20e-6
BOARD_T = 1.6e-3
b = pcbnew.LoadBoard(bf)
M = pcbnew.ToMM
cu_layers = [l for l in b.GetEnabledLayers().CuStack()]
lname = {l: b.GetLayerName(l) for l in cu_layers}


def thick(l):
    return T_OUT if l in (pcbnew.F_Cu, pcbnew.B_Cu) else T_IN


nodes = {}       # key -> id
edges = []       # (a, b, R, width_mm, desc)


def node(key):
    if key not in nodes:
        nodes[key] = len(nodes)
    return nodes[key]


def ptkey(l, p):
    return ('P', l, round(p.x / 1000), round(p.y / 1000))   # 1 um grid


segs = []        # (layer, a VECTOR2I, b VECTOR2I, width, track)
for t in b.GetTracks():
    if t.GetNetname() != net:
        continue
    if t.GetClass() == 'PCB_VIA':
        continue
    if t.GetClass() == 'PCB_ARC':
        segs.append((t.GetLayer(), t.GetStart(), t.GetMid(), t.GetWidth()))
        segs.append((t.GetLayer(), t.GetMid(), t.GetEnd(), t.GetWidth()))
    else:
        segs.append((t.GetLayer(), t.GetStart(), t.GetEnd(), t.GetWidth()))
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net]
pads = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == net:
            pads.append((fp.GetReference() + '.' + p.GetNumber(), p))
islands = []     # (layer, polyset, idx, name)
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() != net:
        continue
    for l in z.GetLayerSet().Seq():
        if not z.HasFilledPolysForLayer(l):
            continue
        ps = z.GetFilledPolysList(l)
        for i in range(ps.OutlineCount()):
            islands.append((l, ps, i, 'zone%s-%d' % (lname.get(l, l), i)))

# split segments at points (track endpoints / vias / pads) lying on their interior
pts_by_layer = collections.defaultdict(list)
for (l, a, e, w) in segs:
    pts_by_layer[l] += [a, e]
for v in vias:
    for l in cu_layers:
        pts_by_layer[l].append(v.GetPosition())


def proj(p, a, e):
    ax, ay, ex, ey = a.x, a.y, e.x, e.y
    dx, dy = ex - ax, ey - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return None
    t = ((p.x - ax) * dx + (p.y - ay) * dy) / L2
    if t <= 1e-6 or t >= 1 - 1e-6:
        return None
    qx, qy = ax + t * dx, ay + t * dy
    return t, math.hypot(p.x - qx, p.y - qy)


newsegs = []
for (l, a, e, w) in segs:
    cuts = []
    for p in pts_by_layer[l]:
        r = proj(p, a, e)
        if r and r[1] <= w / 2:
            cuts.append((r[0], p))
    cuts.sort(key=lambda c: c[0])
    prev = a
    for t_, p in cuts:
        q = pcbnew.VECTOR2I(int(a.x + t_ * (e.x - a.x)), int(a.y + t_ * (e.y - a.y)))
        newsegs.append((l, prev, q, w, p))
        prev = q
    newsegs.append((l, prev, e, w, None))

for (l, a, e, w, snap) in newsegs:
    L = math.hypot(e.x - a.x, e.y - a.y) * 1e-9
    R = RHO * L / (w * 1e-9 * thick(l)) if L > 0 else 1e-9
    ka, ke = ptkey(l, a), ptkey(l, e)
    edges.append((node(ka), node(ke), R, M(w), '%s w%.2f L%.2f' % (lname[l], M(w), L * 1e3)))
    if snap is not None:
        edges.append((node(ke), node(ptkey(l, snap)), 1e-9, 99, 'snap'))

# vias: connect the via point on every layer in its span
for v in vias:
    pos = v.GetPosition()
    lay = [l for l in cu_layers if v.IsOnLayer(l)]
    d = v.GetDrillValue() * 1e-9
    Rv = RHO * (BOARD_T / max(1, len(lay) - 1)) / (math.pi * d * VIA_PLATE)
    for i in range(len(lay) - 1):
        edges.append((node(ptkey(lay[i], pos)), node(ptkey(lay[i + 1], pos)), Rv, round(M(v.GetDrillValue()), 2), 'via d%.2f' % M(v.GetDrillValue())))

# connect point nodes that fall inside pads / zone islands
pointkeys = [k for k in list(nodes) if k[0] == 'P']
_isl_cache = {}


def overlap(shape, ps, i):
    key = (id(ps), i)
    if key not in _isl_cache:
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(ps.Outline(i))
        for h in range(ps.HoleCount(i)):
            one.AddHole(ps.Hole(i, h))
        _isl_cache[key] = one
    one = _isl_cache[key]
    bb1, bb2 = shape.BBox(), one.BBox()
    if bb1.GetRight() < bb2.GetLeft() or bb1.GetLeft() > bb2.GetRight() or bb1.GetBottom() < bb2.GetTop() or bb1.GetTop() > bb2.GetBottom():
        return False
    inter = pcbnew.SHAPE_POLY_SET(shape)
    inter.BooleanIntersection(one)
    return inter.Area() > 1e3   # > 0.001 mm2 (units nm^2 -> 1e3 nm^2 is tiny; area in nm^2)
for name, p in pads:
    pn = node(('PAD', name))
    for l in cu_layers:
        if not p.IsOnLayer(l):
            continue
        sh = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(sh, l, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_OUTSIDE)
        for k in pointkeys:
            if k[1] == l and sh.Contains(pcbnew.VECTOR2I(k[2] * 1000, k[3] * 1000)):
                edges.append((pn, nodes[k], 1e-6, 99, 'pad'))
        # pad also touches zone islands on that layer (polygon overlap, so thermal spokes and drill holes are handled)
        sh2 = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(sh2, l, pcbnew.FromMM(0.02), pcbnew.FromMM(0.005), pcbnew.ERROR_OUTSIDE)
        for (zl, ps, i, zn) in islands:
            if zl != l:
                continue
            if overlap(sh2, ps, i):
                edges.append((pn, node(('Z', zl, i, id(ps))), 1e-6, 99, 'pad-zone %s' % zn))
for (zl, ps, i, zn) in islands:
    zn_id = node(('Z', zl, i, id(ps)))
    for k in pointkeys:
        if k[1] == zl and ps.Contains(pcbnew.VECTOR2I(k[2] * 1000, k[3] * 1000), i):
            edges.append((zn_id, nodes[k], 1e-6, 99, 'zone'))
# overlapping fills of different zones of the same net on the same layer are connected (KiCad connectivity does this)
for ia in range(len(islands)):
    for ib in range(ia + 1, len(islands)):
        la, psa, ii, _ = islands[ia]
        lb, psb, jj, _ = islands[ib]
        if la != lb or psa is psb:
            continue
        ola, olb = psa.Outline(ii), psb.Outline(jj)
        ba, bb_ = ola.BBox(), olb.BBox()
        if ba.GetRight() < bb_.GetLeft() or ba.GetLeft() > bb_.GetRight() or ba.GetBottom() < bb_.GetTop() or ba.GetTop() > bb_.GetBottom():
            continue
        if '_isl_b' not in globals():
            _isl_b = {}
        key = (id(psb), jj)
        if key not in _isl_b:
            one = pcbnew.SHAPE_POLY_SET()
            one.AddOutline(olb)
            for h in range(psb.HoleCount(jj)):
                one.AddHole(psb.Hole(jj, h))
            _isl_b[key] = one
        one = _isl_b[key]
        touch = False
        for kk in range(0, ola.PointCount(), 1):
            if one.Collide(ola.CPoint(kk), pcbnew.FromMM(0.03)):
                touch = True
                break
        if touch:
            edges.append((node(('Z', la, ii, id(psa))), node(('Z', lb, jj, id(psb))), 1e-6, 99, 'zone-zone'))
# vias touching zone islands (annular ring overlap; the fill may have a hole at the drill)
for v in vias:
    pos = v.GetPosition()
    r = v.GetWidth(pcbnew.F_Cu) // 2 + pcbnew.FromMM(0.02)
    ring = pcbnew.SHAPE_POLY_SET()
    ring.NewOutline()
    for kk in range(16):
        a = 2 * math.pi * kk / 16
        ring.Append(int(pos.x + r * math.cos(a)), int(pos.y + r * math.sin(a)))
    for (zl, ps, i, zn) in islands:
        if v.IsOnLayer(zl) and overlap(ring, ps, i):
            edges.append((node(('Z', zl, i, id(ps))), node(ptkey(zl, pos)), 1e-6, 99, 'via-zone'))

N = len(nodes)
adj = collections.defaultdict(list)
for (a, e, R, w, d) in edges:
    adj[a].append((e, R, w, d))
    adj[e].append((a, R, w, d))
name_of = {v: k for k, v in nodes.items()}


def widest(s, t):
    import heapq
    best = {s: 1e9}
    prev = {}
    h = [(-1e9, s)]
    while h:
        negw, u = heapq.heappop(h)
        if u == t:
            break
        if -negw < best.get(u, -1):
            continue
        for (v, R, w, d) in adj[u]:
            nw = min(-negw, w)
            if nw > best.get(v, -1):
                best[v] = nw
                prev[v] = (u, d, w)
                heapq.heappush(h, (-nw, v))
    if t not in best:
        return None, []
    path = []
    u = t
    while u != s:
        pu, d, w = prev[u]
        path.append((d, w))
        u = pu
    return best[t], path[::-1]


def resistance(s, t):
    # merge near-ideal edges (pads, zones, snaps) with union-find, then solve the nodal equations exactly
    par = {}
    def f(x):
        while par.get(x, x) != x:
            par[x] = par.get(par[x], par[x])
            x = par[x]
        return x
    for (a, e, R, w, d) in edges:
        if R < 1e-5:
            ra, re_ = f(a), f(e)
            if ra != re_:
                par[ra] = re_
    S, T = f(s), f(t)
    if S == T:
        return 0.0
    nb = collections.defaultdict(lambda: collections.defaultdict(float))
    for (a, e, R, w, d) in edges:
        if R < 1e-5:
            continue
        ra, re_ = f(a), f(e)
        if ra == re_:
            continue
        g = 1.0 / R
        nb[ra][re_] += g
        nb[re_][ra] += g
    comp = {S}
    st = [S]
    while st:
        u = st.pop()
        for v in nb[u]:
            if v not in comp:
                comp.add(v)
                st.append(v)
    if T not in comp:
        return None
    idx = {u: i for i, u in enumerate(sorted(u for u in comp if u != T))}
    n = len(idx)
    A = [[0.0] * n for _ in range(n)]
    rhs = [0.0] * n
    for u, i in idx.items():
        for v, g in nb[u].items():
            A[i][i] += g
            if v != T:
                A[i][idx[v]] -= g
    rhs[idx[S]] = 1.0
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(A[r][c]))
        A[c], A[piv] = A[piv], A[c]
        rhs[c], rhs[piv] = rhs[piv], rhs[c]
        pv = A[c][c]
        for r in range(c + 1, n):
            if A[r][c] != 0.0:
                fct = A[r][c] / pv
                Ar, Ac = A[r], A[c]
                for k in range(c, n):
                    Ar[k] -= fct * Ac[k]
                rhs[r] -= fct * rhs[c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (rhs[r] - sum(A[r][k] * x[k] for k in range(r + 1, n))) / A[r][r]
    return x[idx[S]]


s = node(('PAD', src))
print('NET %s  nodes %d edges %d  (outer %.1f um, inner %.1f um, via plating %.0f um)' % (net, N, len(edges), T_OUT * 1e6, T_IN * 1e6, VIA_PLATE * 1e6))
for dname in dsts:
    t = node(('PAD', dname))
    w, path = widest(s, t)
    if w is None:
        print('  %s -> %s: NOT CONNECTED' % (src, dname))
        continue
    R = resistance(s, t)
    narrow = [d for (d, ww) in path if ww < 99]
    print('  %s -> %s: bottleneck width %.2f mm, R = %.1f mOhm' % (src, dname, w, R * 1e3))
    print('      widest path elements (non-zone): %s' % ' | '.join(narrow))
