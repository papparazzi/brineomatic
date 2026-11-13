"""Rev D step 20: board outline 155.6 x 84.5 -> 160.0 x 90.0 mm. No net change.
The extra 4.4 mm goes to the west (dev-board) side. The extra 5.5 mm goes to the top, and the seven top-edge plugs move up with the
edge so that they stay at the board edge. At each old pin position a plated hole (via 1.2 / 0.6 mm) stays, so every existing track and
plane connection ends exactly where it did; a track on the top and on the bottom layer joins it to the moved pin.
South and east edges, all other parts and the mounting holes do not move.
usage: pcb_resize_160x90.py <step19.kicad_pcb> <out.kicad_pcb>      (KiCad 10 Python)"""
import sys
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
FPS = dict((f.GetReference(), f) for f in b.GetFootprints()); DRAW = list(b.GetDrawings())
def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
DX, DY = 4.4, 5.5

# ---------------------------------------------------------------- outline
def mx(v): return v - FromMM(DX) if ToMM(v) < 35 else v          # west edge and the west ends of the horizontal lines
def my(v): return v - FromMM(DY) if ToMM(v) < 16 else v          # top edge and the top ends of the vertical lines
n = 0
for d in DRAW:
    if d.GetLayer() != pcbnew.Edge_Cuts: continue
    s, e = d.GetStart(), d.GetEnd()
    if d.ShowShape() == "Arc":
        c = d.GetCenter(); d.Move(VECTOR2I(mx(c.x) - c.x, my(c.y) - c.y))
    else:
        d.SetStart(VECTOR2I(mx(s.x), my(s.y))); d.SetEnd(VECTOR2I(mx(e.x), my(e.y)))
    n += 1
assert n == 8, n

# ---------------------------------------------------------------- top-edge plugs
POWER = ("GND", "+5V", "+12V", "+3.3V")
moved = []
for ref in ("J4", "J11", "J3", "J18", "J22", "J5", "J21"):
    fp = FPS[ref]
    assert fp.GetOrientationDegrees() == 180
    old = [(p.GetNumber(), ToMM(p.GetPosition().x), ToMM(p.GetPosition().y), p.GetNet(), p.GetNetname()) for p in fp.Pads()]
    fp.Move(VECTOR2I(0, FromMM(-DY)))
    for num, x, y, net, name in old:
        v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetWidth(pcbnew.F_Cu, FromMM(1.2)); v.SetDrill(FromMM(0.6)); v.SetNet(net); b.Add(v)
        w = 1.0 if (name in POWER or ref == "J21") else 0.5      # supplies and motor phases wide, sensor signals 0.5 mm
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            t = pcbnew.PCB_TRACK(b); t.SetStart(P(x, y)); t.SetEnd(P(x, y - DY)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
    moved.append(ref)

# ---------------------------------------------------------------- their labels: name between plug and the old-pin holes, legend below the holes
k = 0
for d in DRAW:
    if d.GetClass() != "PCB_TEXT" or d.GetLayer() != pcbnew.F_SilkS or not d.IsKnockout(): continue
    y = ToMM(d.GetPosition().y)
    if abs(y - 26.45) < 0.01: d.SetPosition(VECTOR2I(d.GetPosition().x, FromMM(20.60))); k += 1
    elif abs(y - 28.35) < 0.01: d.SetPosition(VECTOR2I(d.GetPosition().x, FromMM(24.55))); k += 1
assert k == 7 + 20, k

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
bb = b.GetBoardEdgesBoundingBox()
print("moved plugs", moved, "| outline now %.2f x %.2f mm" % (ToMM(bb.GetWidth()), ToMM(bb.GetHeight())))
