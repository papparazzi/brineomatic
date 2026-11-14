"""Rev D step 26 (independent review of 13 Nov 2026, major M1): the servo supply 5V_HIGH_POWER gets wide top-layer copper from D10
to the servo terminals J6 and J29. At step 25 it left D10 as a 0.25 mm track and ran about 33 mm on inner layer In1, then over the
bottom layer to J29 pin 2 and back up In1 to J6 pin 2 (230 mOhm from F2 to J6.2, 161 mOhm to J29.2; Rev-C1: 1.5 mm top track,
5-6 mOhm). No net change; no part is added, removed or moved.
  1. Every thin 5V_HIGH_POWER track east of D10 (top, In1 and bottom layer, 25 segments) and four of its vias deleted. Kept: the
     F2/C21/U4 copper, the 1.5 mm track from C21 to D10, and the via with its bottom-layer link to test point TP42.
  2. New top-layer route: D10 pin 1 -> 1.8 mm diagonal between the Net-(D11-A2) via and the +5V via (0.27 mm gap to each) -> 2.0 mm
     north at x 142.7 -> 4.0 mm east at y 26.6, in the free band between the top plug row and the TMC2209 parts -> 2.5 mm trunk at
     x 169.6 -> 2.5 mm into J6 pin 2 and J29 pin 2.
  3. The TP42 via moves 0.14 mm west onto the centre line of the 2.0 mm track, which ends on it from both sides (142.838 -> 142.7);
     its bottom-layer link follows. The ground stitching via at (141.6, 31.55), in the way of the 2.0 mm track, moves 1.2 mm west
     to (140.4, 31.55).
usage: pcb_servo_power.py <in.kicad_pcb> <out.kicad_pcb>      (KiCad 10 Python)"""
import sys
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
FPS = dict((f.GetReference(), f) for f in b.GetFootprints())
SV, GND = "5V_HIGH_POWER", "GND"
NET = dict((n, b.FindNet(n)) for n in (SV, GND))


def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def at(p, x, y): return abs(ToMM(p.x) - x) < 0.01 and abs(ToMM(p.y) - y) < 0.01
def pad(ref, num): return [p for p in FPS[ref].Pads() if p.GetNumber() == num][0]


def track(net, layer, w, *pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(NET[net]); b.Add(t)


# starting state (step 25)
for ref, num, x, y in (("D10", "1", 134.8, 44.0), ("J6", "2", 176.0, 20.995), ("J29", "2", 176.0, 35.295), ("TP42", "1", 141.5, 33.8)):
    p = pad(ref, num); assert p.GetNetname() == SV and at(p.GetPosition(), x, y), (ref, num)
TR = list(b.GetTracks())
keep_via = [t for t in TR if t.GetClass() == "PCB_VIA" and t.GetNetname() == SV and at(t.GetPosition(), 142.838, 33.08)]
tp_link = [t for t in TR if t.GetClass() != "PCB_VIA" and t.GetNetname() == SV and t.GetLayer() == pcbnew.B_Cu
           and at(t.GetStart(), 142.838, 33.08) and at(t.GetEnd(), 142.22, 33.08)]
gnd_via = [t for t in TR if t.GetClass() == "PCB_VIA" and t.GetNetname() == GND and at(t.GetPosition(), 141.6, 31.55)]
assert len(keep_via) == 1 and len(tp_link) == 1 and len(gnd_via) == 1

# 1. delete the thin route
kill = []
for t in TR:
    if t.GetNetname() != SV: continue
    x0 = min(ToMM(t.GetStart().x), ToMM(t.GetEnd().x))
    if t.GetClass() == "PCB_VIA":
        if t not in keep_via: kill.append(t)
    elif t.GetLayer() == pcbnew.In1_Cu: kill.append(t)
    elif t.GetLayer() == pcbnew.F_Cu and t.GetWidth() < FromMM(0.3) and x0 > 134.7: kill.append(t)
    elif t.GetLayer() == pcbnew.B_Cu and x0 > 160: kill.append(t)
layer = lambda t: "via" if t.GetClass() == "PCB_VIA" else t.GetLayerName()
got = dict((k, sum(1 for t in kill if layer(t) == k)) for k in ("F.Cu", "In1.Cu", "B.Cu", "via"))
assert got == {"F.Cu": 8, "In1.Cu": 15, "B.Cu": 2, "via": 4}, got
for t in kill: b.Remove(t)

# 2. the new route on the top layer
track(SV, pcbnew.F_Cu, 1.8, (135.65, 44.53), (142.7, 37.48))
track(SV, pcbnew.F_Cu, 2.0, (142.7, 37.48), (142.7, 33.08), (142.7, 26.6))
track(SV, pcbnew.F_Cu, 4.0, (142.7, 26.6), (169.6, 26.6))
track(SV, pcbnew.F_Cu, 2.5, (169.6, 26.6), (169.6, 20.995), (176.0, 20.995))
track(SV, pcbnew.F_Cu, 2.5, (169.6, 26.6), (169.6, 35.295), (176.0, 35.295))

# 3. TP42 via onto the track's centre line; ground stitching via out of the way of the 2.0 mm track
keep_via[0].SetPosition(P(142.7, 33.08)); tp_link[0].SetStart(P(142.7, 33.08))
gnd_via[0].SetPosition(P(140.4, 31.55))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b, True)      # True: leave the .kicad_pro alone (otherwise pcbnew rewrites it with default settings)
print("deleted", got, "| added 8 top-layer segments | TP42 via -> (142.7, 33.08) | GND via (141.6, 31.55) -> (140.4, 31.55)")
