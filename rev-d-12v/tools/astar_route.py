"""Single-net grid router (F.Cu/B.Cu + through vias) for the few connections the autorouter left open.
usage: astar_route.py <pcb> <net> x1 y1 x2 y2 <out_spec.json>      (start/target are points on F.Cu pads of that net)
Obstacles = tracks, vias, pads of OTHER nets (inflated by clearance + half width); zones ignored (they refill around)."""
import sys, json, heapq, math
import numpy as np
from PIL import Image, ImageDraw
import pcbnew
pcb, net = sys.argv[1], sys.argv[2]
x1, y1, x2, y2 = map(float, sys.argv[3:7]); out = sys.argv[7]
RES = 0.1; X0, Y0, X1, Y1 = 30.0, 25.0, 175.0, 96.0
W, H = int((X1 - X0) / RES), int((Y1 - Y0) / RES)
TRK, CLR, VIA = 0.25, 0.22, 0.6
b = pcbnew.LoadBoard(pcb); mm = pcbnew.ToMM
layers = {pcbnew.F_Cu: 0, pcbnew.In1_Cu: 1, pcbnew.In2_Cu: 2, pcbnew.B_Cu: 3}
def px(x, y): return ((x - X0) / RES, (y - Y0) / RES)
imgs = [Image.new('1', (W, H), 0) for _ in range(4)]
draws = [ImageDraw.Draw(i) for i in imgs]
def circ(d, x, y, r):
    cx, cy = px(x, y); rr = r / RES; d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=1)
def seg(d, a, c, w):
    d.line([px(*a), px(*c)], fill=1, width=max(1, int(round(w / RES))))
    circ(d, a[0], a[1], w / 2); circ(d, c[0], c[1], w / 2)
def inflate(extra):
    return extra
for t in b.GetTracks():
    if t.GetNetname() == net:
        continue
    if t.GetClass() == 'PCB_VIA':
        r = mm(t.GetWidth()) / 2 + CLR + TRK / 2
        for d in draws:
            circ(d, mm(t.GetX()), mm(t.GetY()), r)
    else:
        L = layers.get(t.GetLayer())
        if L is not None:
            seg(draws[L], (mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth()) + 2 * (CLR + TRK / 2))
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname() == net:
            continue
        bb = p.GetBoundingBox(); e = CLR + TRK / 2
        box = [px(mm(bb.GetX()) - e, mm(bb.GetY()) - e), px(mm(bb.GetRight()) + e, mm(bb.GetBottom()) + e)]
        for L in range(4):
            if p.IsOnLayer(list(layers)[L]):
                draws[L].rectangle(box, fill=1)
# board edge keep-out 0.5 mm
arr = [np.array(i, dtype=bool) for i in imgs]
via_block = arr[0] | arr[1] | arr[2] | arr[3]
# vias need larger clearance: dilate the combined mask by (VIA - TRK)/2 in cells
from scipy.ndimage import binary_dilation  # noqa
k = int(round((VIA - TRK) / 2 / RES)) + 1
via_block = binary_dilation(via_block, iterations=k)
for a in arr:
    a[:20, :] = True; a[-20:, :] = True; a[:, :20] = True; a[:, -20:] = True
def cell(x, y): return (int(round((y - Y0) / RES)), int(round((x - X0) / RES)))
s, g = cell(x1, y1), cell(x2, y2)
def free(L, r, c): return 0 <= r < H and 0 <= c < W and not arr[L][r, c]
# endpoints sit on their own pads: clear a small disc around them on F.Cu and on B.Cu for via escape
for (r, c) in (s, g):
    arr[0][max(0, r - 4):r + 5, max(0, c - 4):c + 5] = False
start, goal = (0, s[0], s[1]), (0, g[0], g[1])
dirs = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
openq = [(0, 0, start)]; best = {start: 0}; prev = {}
VC = 6.0
while openq:
    f, gc, cur = heapq.heappop(openq)
    if cur == goal:
        break
    if gc > best.get(cur, 1e9):
        continue
    L, r, c = cur
    for dr, dc, w in dirs:
        n = (L, r + dr, c + dc)
        if free(L, n[1], n[2]) or (n[1], n[2]) in (g, s):
            if dr and dc and not (free(L, r + dr, c) and free(L, r, c + dc)):
                continue
            ng = gc + w
            if ng < best.get(n, 1e9):
                best[n] = ng; prev[n] = cur
                heapq.heappush(openq, (ng + math.hypot(n[1] - g[0], n[2] - g[1]) , ng, n))
    if 0 <= r < H and 0 <= c < W and not via_block[r, c]:
        for L2 in (0, 3):
            if L2 != L and L in (0, 3) and free(L2, r, c):
                n = (L2, r, c); ng = gc + VC
                if ng < best.get(n, 1e9):
                    best[n] = ng; prev[n] = cur
                    heapq.heappush(openq, (ng + math.hypot(r - g[0], c - g[1]), ng, n))
if goal not in prev and start != goal:
    print('NO PATH'); sys.exit(1)
path = [goal]
while path[-1] != start:
    path.append(prev[path[-1]])
path.reverse()
def xy(n): return (X0 + n[2] * RES, Y0 + n[1] * RES)
spec = []; run = [path[0]]
def flush(run):
    if len(run) < 2:
        return
    L = run[0][0]
    pts = [run[0]]
    for i in range(1, len(run) - 1):
        a, c, d = run[i - 1], run[i], run[i + 1]
        if (c[1] - a[1], c[2] - a[2]) != (d[1] - c[1], d[2] - c[2]):
            pts.append(c)
    pts.append(run[-1])
    for p, q in zip(pts, pts[1:]):
        (xa, ya), (xb, yb) = xy(p), xy(q)
        spec.append(['F' if L == 0 else 'B', round(xa, 2), round(ya, 2), round(xb, 2), round(yb, 2), TRK])
for a, c in zip(path, path[1:]):
    if a[0] != c[0]:
        flush(run); x, y = xy(a); spec.append(['via', round(x, 2), round(y, 2)]); run = [c]
    else:
        run.append(c)
flush(run)
spec[0][1:3] = [x1, y1]
json.dump(spec, open(out, 'w'))
print('path ok', len(path), 'cells,', sum(1 for s_ in spec if s_[0] == 'via'), 'vias,', round(sum(math.hypot(s_[3] - s_[1], s_[4] - s_[2]) for s_ in spec if s_[0] != 'via'), 1), 'mm')
