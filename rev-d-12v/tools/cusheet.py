"""Sheet-resistance solver for the copper of one net on one layer, including pours (a track-network model treats pours as ideal).
Checked against R = rho*L/(w*t) on a straight 0.38 mm track between two pads (R51-D39): 2.83 / 2.98 mOhm at 0.05 / 0.025 mm grid vs 2.91.
Rasterises the filled zones, tracks and pads of the net inside a box, holds the source pads at 1 V and the sink pads (or vias) at 0 V,
solves Laplace's equation on the grid by conjugate gradients and reports the resistance R = R_sheet / I.
Each pad counts as an equipotential electrode (lead and solder), so the result is a slight underestimate at small pads.
usage: cusheet.py <board> <layer> <copper_um> <net> <grid_mm> <x0,y0,x1,y1> <SRC ref.pad[,ref.pad]> <SINK> [<SINK> ...]
       SINK = ref.pad[,ref.pad...] or 'vias' (every via of the net inside the box, together); each SINK is solved on its own.
Runs in KiCad's Python (pcbnew + numpy)."""
import sys
import numpy as np
import pcbnew
from pcbnew import FromMM, VECTOR2I

b = pcbnew.LoadBoard(sys.argv[1])
layer = b.GetLayerID(sys.argv[2]); t_um = float(sys.argv[3]); net = sys.argv[4]; h = float(sys.argv[5])
x0, y0, x1, y1 = map(float, sys.argv[6].split(','))
RS = 1.72e-8 / (t_um * 1e-6) * 1e3          # mOhm per square, copper at 20 C
nx, ny = int(round((x1 - x0) / h)), int(round((y1 - y0) / h))
xs = [x0 + h * (i + 0.5) for i in range(nx)]; ys = [y0 + h * (j + 0.5) for j in range(ny)]


def shape_of(item, grow=0.0):
    s = pcbnew.SHAPE_POLY_SET(); item.TransformShapeToPolygon(s, layer, FromMM(grow), FromMM(0.002), pcbnew.ERROR_INSIDE); return s


def raster(shapes):
    m = np.zeros((ny, nx), bool)
    for s in shapes:
        bb = s.BBox()
        i0 = max(0, int((pcbnew.ToMM(bb.GetLeft()) - x0) / h)); i1 = min(nx, int((pcbnew.ToMM(bb.GetRight()) - x0) / h) + 2)
        j0 = max(0, int((pcbnew.ToMM(bb.GetTop()) - y0) / h)); j1 = min(ny, int((pcbnew.ToMM(bb.GetBottom()) - y0) / h) + 2)
        for j in range(j0, j1):
            for i in range(i0, i1):
                if not m[j, i] and s.Contains(VECTOR2I(FromMM(xs[i]), FromMM(ys[j]))): m[j, i] = True
    return m


cu_shapes = []
for z in b.Zones():
    if z.GetNetname() == net and not z.GetIsRuleArea() and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer):
        cu_shapes.append(pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(layer)))
for t in b.GetTracks():
    if t.GetNetname() == net and t.IsOnLayer(layer): cu_shapes.append(shape_of(t))
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == net and p.IsOnLayer(layer): cu_shapes.append(shape_of(p))
CU = raster(cu_shapes)


def electrode(spec):
    if spec == 'vias':
        return raster([shape_of(t) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net
                       and x0 <= pcbnew.ToMM(t.GetX()) <= x1 and y0 <= pcbnew.ToMM(t.GetY()) <= y1])
    sh = []
    for s in spec.split(','):
        ref, num = s.split('.')
        sh += [shape_of(p) for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num and p.IsOnLayer(layer)]
    assert sh, spec
    return raster(sh)


def nb_sum(X, C):
    """sum of X over the 4 neighbours that are copper"""
    s = np.zeros_like(X)
    s[1:, :] += X[:-1, :] * C[:-1, :]; s[:-1, :] += X[1:, :] * C[1:, :]
    s[:, 1:] += X[:, :-1] * C[:, :-1]; s[:, :-1] += X[:, 1:] * C[:, 1:]
    return s


def solve(SRC, SNK):
    SRC = SRC & CU; SNK = SNK & CU & ~SRC
    U = CU & ~SRC & ~SNK
    deg = nb_sum(np.ones((ny, nx)), CU) * CU
    rhs = nb_sum(SRC.astype(float), CU) * U                     # known 1 V neighbours move to the right-hand side
    A = lambda X: (deg * X - nb_sum(X, CU)) * U
    x = np.zeros((ny, nx)); r = rhs - A(x); p = r.copy(); rr = (r * r).sum()
    for it in range(20000):
        Ap = A(p); a = rr / (p * Ap).sum(); x += a * p; r -= a * Ap
        rn = (r * r).sum()
        if rn < 1e-20 * max(1.0, (rhs * rhs).sum()): break
        p = r + (rn / rr) * p; rr = rn
    V = x * U + SRC
    I = (SRC * (deg * V - nb_sum(V, CU))).sum()                 # current leaving the source, in units of 1/R_sheet
    return RS / I if I > 0 else float('inf'), it, int(SRC.sum()), int(SNK.sum())


S0 = electrode(sys.argv[7])
print('%s %s %.1f um (R_sheet %.3f mOhm/sq), grid %.3f mm, %d x %d, copper cells %d' % (net, sys.argv[2], t_um, RS, h, nx, ny, CU.sum()))
for spec in sys.argv[8:]:
    R, it, ns, nk = solve(S0, electrode(spec))
    print('   %s -> %-14s %8.3f mOhm   (%d CG iterations, %d/%d electrode cells)' % (sys.argv[7], spec, R, it, ns, nk))
