"""Rev D step 24 (independent review of 13 Nov 2026, blocker B1): the input power path from the fuse F1 to the reverse-polarity
MOSFETs Q9/Q10 and on to +12V is rebuilt with wide copper. At step 23 the fuse output reached the MOSFETs only through 0.20/0.25 mm
tracks and two single vias (34-45 mOhm), and the MOSFET sources reached +12V through 0.25 mm tracks. The PRE_24 pour around F1 pin 2
was cut off from the pour around C13/C14 twice: by the ground jumper from C47 pin 2 to D19, and by the TMC2209_RX track running
diagonally through it. No net change; no part is added or removed.
  1. D19 (SMBJ16CA, two-way TVS) turned 180 deg, so that its PRE_24 pad sits in the input copper and its GND pad in the ground pour, as
     on Rev-C1 (Rev-C1 had PRE_24 on the upper pad too). The ground jumper C47.2 -> D19 is deleted; C47.2 keeps its ground via.
  2. TMC2209_RX re-routed on the top layer around the right side of F1 instead of through the input copper.
  3. Every thin PRE_24 track and both PRE_24 vias deleted; the PRE_24 pour now reaches both drains (2.8-3.3 mm wide). The 1.0 mm
     bottom track from F1 pin 2 to test point TP39 is kept.
  4. Each MOSFET source gets a +12V copper area with vias to the inner +12V plane (Q9: 6, Q10: 8), joined to the existing +12V pours.
  5. The gate net PFET_G re-routed on the outer side of the MOSFETs and on In1, so that it no longer crosses the power path.
     D56 and R78 stay where they are.
usage: pcb_review_fix_power.py <in.kicad_pcb> <out.kicad_pcb>      (KiCad 10 Python)"""
import sys
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
FPS = dict((f.GetReference(), f) for f in b.GetFootprints())
PRE, P12, GATE, GND, RX = "/Power Supply/PRE_24", "+12V", "/Power Supply/PFET_G", "GND", "TMC2209_RX"
NET = dict((n, b.FindNet(n)) for n in (PRE, P12, GATE, GND, RX))


def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def at(p, x, y): return abs(ToMM(p.x) - x) < 0.01 and abs(ToMM(p.y) - y) < 0.01
def pad(ref, num): return [p for p in FPS[ref].Pads() if p.GetNumber() == num][0]
def seg(t, a, c): return (at(t.GetStart(), *a) and at(t.GetEnd(), *c)) or (at(t.GetStart(), *c) and at(t.GetEnd(), *a))


def track(net, layer, w, *pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(NET[net]); b.Add(t)


def via(net, x, y, dia):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetWidth(FromMM(dia)); v.SetDrill(FromMM(0.3)); v.SetNet(NET[net]); b.Add(v)


def zone_outline(z, pts):
    o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
    for x, y in pts: o.Append(FromMM(x), FromMM(y))


def new_zone(net, prio, pts):
    z = pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNet(NET[net]); z.SetAssignedPriority(prio)
    z.SetLocalClearance(FromMM(0.25)); z.SetMinThickness(FromMM(0.25)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); zone_outline(z, pts); b.Add(z)


# starting state (step 23)
d19 = FPS["D19"]
assert at(d19.GetPosition(), 148.9, 58.7) and abs(d19.GetOrientationDegrees() - 90) < 0.01
assert pad("D19", "1").GetNetname() == PRE and at(pad("D19", "1").GetPosition(), 148.9, 60.85)
for ref, x, y in (("Q9", 139.0, 54.5), ("Q10", 139.0, 60.5), ("D56", 143.8, 58.0), ("R78", 143.8, 62.0), ("F1", 157.6, 78.35)):
    assert at(FPS[ref].GetPosition(), x, y), ref
TR = list(b.GetTracks())

# 1-5: delete the old copper
kill = []
for t in TR:
    n, v = t.GetNetname(), t.GetClass() == "PCB_VIA"
    if n == PRE and (v or not (t.GetLayer() == pcbnew.B_Cu and t.GetWidth() >= FromMM(0.99))): kill.append(t)
    elif n == GATE: kill.append(t)
    elif n == GND and not v and (seg(t, (152.1, 53.25), (152.1, 56.55)) or seg(t, (152.1, 56.55), (148.9, 56.55))): kill.append(t)
    elif n == P12 and v and at(t.GetPosition(), 137.839, 57.975): kill.append(t)
    elif n == P12 and not v and any(seg(t, a, c) for a, c in (((138.062, 55.45), (138.062, 57.751)), ((138.062, 57.751), (137.839, 57.975)),
                                                               ((138.062, 61.45), (139.098, 61.45)), ((139.098, 61.45), (143.212, 65.565)))): kill.append(t)
    elif n == RX and not v and t.GetLayer() == pcbnew.F_Cu and min(ToMM(t.GetStart().y), ToMM(t.GetEnd().y)) < 58.2 and ToMM(t.GetStart().x) > 151.5: kill.append(t)
count = lambda net, via_: sum(1 for t in kill if t.GetNetname() == net and (t.GetClass() == "PCB_VIA") == via_)
got = dict(pre=(count(PRE, False), count(PRE, True)), gate=(count(GATE, False), count(GATE, True)), gnd=count(GND, False),
           p12=(count(P12, False), count(P12, True)), rx=count(RX, False))
assert got == dict(pre=(28, 2), gate=(23, 3), gnd=2, p12=(4, 1), rx=6), got
for t in kill: b.Remove(t)

# 1. D19 turned 180 deg about its centre; its outline's end bar now runs at y 55.04, where the C13/C14 labels were
d19.SetOrientationDegrees(270)
assert at(pad("D19", "1").GetPosition(), 148.9, 56.55) and at(pad("D19", "2").GetPosition(), 148.9, 60.85)
FPS["C13"].Reference().SetPosition(P(145.2, 55.45))
FPS["C14"].Reference().SetPosition(P(150.75, 52.6)); FPS["C14"].Reference().SetTextAngleDegrees(90)

# 2. TMC2209_RX from R54 pin 1 around the right side of F1, then on to the existing track at (151.546, 58.301)
r54 = pad("R54", "1"); assert r54.GetNetname() == RX and at(r54.GetPosition(), 157.9, 53.325)
track(RX, pcbnew.F_Cu, 0.2, (157.9, 53.325), (159.2, 53.325), (160.1, 54.225), (160.1, 57.7), (159.3, 58.5), (151.745, 58.5), (151.546, 58.301))

# 3. PRE_24 pour: the old outline plus the area left of x 142.9 down to both drains
zp = [z for z in b.Zones() if z.GetNetname() == PRE]; assert len(zp) == 1
zone_outline(zp[0], ((139.0, 52.6), (143.9, 52.6), (144.4, 53.1), (151.0, 53.1), (151.0, 54.3), (158.8, 54.3), (159.4, 54.9), (159.4, 56.5),
                     (157.8, 58.1), (147.8, 58.1), (145.6, 55.9), (142.0, 55.9), (142.0, 61.3), (139.0, 61.3)))

# 4. +12V areas at the sources: Q9 joins the +12V pour at TP15, Q10 joins the +12V pour at C22/D49; vias to the In2 +12V plane
new_zone(P12, 14, ((135.6, 54.55), (138.85, 54.55), (138.85, 58.85), (136.1, 58.85), (136.1, 55.9), (135.6, 55.9)))
new_zone(P12, 14, ((136.4, 60.6), (138.85, 60.6), (138.85, 61.65), (141.75, 61.65), (141.75, 63.4), (142.4, 63.4), (142.4, 64.6), (136.4, 64.6)))
for x, y in ((137.55, 56.45), (138.45, 56.45), (137.55, 57.35), (138.45, 57.35), (137.55, 58.25), (138.45, 58.25)): via(P12, x, y, 0.6)
for x in (137.4, 138.3, 139.2, 140.1):
    for y in (62.55, 63.45): via(P12, x, y, 0.6)

# 5. gate net: Q9.1 and Q10.1 to vias on their outer side, joined on In1, then on to D56 (anode) and R78
g9, g10, dz, rr = pad("Q9", "1"), pad("Q10", "1"), pad("D56", "2"), pad("R78", "1")
assert all(p.GetNetname() == GATE for p in (g9, g10, dz, rr))
assert at(g9.GetPosition(), 138.0625, 53.55) and at(g10.GetPosition(), 138.0625, 59.55) and at(dz.GetPosition(), 143.8, 56.35) and at(rr.GetPosition(), 143.8, 62.825)
# the Q9 gate via sits above Q9: left of Q9 it would close the 1.1 mm neck that joins the TP15 corner of the In2 +12V plane to the rest
track(GATE, pcbnew.F_Cu, 0.25, (138.0625, 53.55), (138.0625, 51.9)); via(GATE, 138.0625, 51.9, 0.45)
track(GATE, pcbnew.F_Cu, 0.25, (138.0625, 59.55), (136.85, 59.55)); via(GATE, 136.85, 59.55, 0.45)
track(GATE, pcbnew.In1_Cu, 0.25, (138.0625, 51.9), (136.85, 53.1125), (136.85, 59.55), (137.35, 59.05), (141.1, 59.05), (142.8, 57.35)); via(GATE, 142.8, 57.35, 0.45)
track(GATE, pcbnew.F_Cu, 0.25, (142.8, 57.35), (143.8, 56.35), (144.9, 57.45), (144.9, 61.725), (143.8, 62.825))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b, True)      # True: leave the .kicad_pro alone (otherwise pcbnew rewrites it with default settings)
print("deleted", got, "| D19 now at %.0f deg" % d19.GetOrientationDegrees())
