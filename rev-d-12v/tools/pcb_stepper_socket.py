"""Rev D step 18: TMC2209 chip U9 -> socketed BIGTREETECH TMC2209 V1.3 module.
usage: pcb_stepper_socket.py <in.kicad_pcb> <out.kicad_pcb>   (KiCad 10 Python)

Module pin geometry from BTT's own drawing "TMC2209 V1.3-SIZE.pdf" (15.24 x 20.32 mm, two 1x8 rows 12.70 mm apart,
2.54 mm pitch, INDEX and DIAG on the EN edge at +2.54 / +5.08 mm from EN). Module is turned 90 deg clockwise:
control row on top (y 28.70, EN at the east end), motor row below (y 41.40, VM at the east end) so that
B2, B1, A1, A2 line up west->east with the existing output filter and J21.
Leaves TMC2209_EN/STEP/DIR/TX/DIAG and MS1/MS2 unrouted for the autorouter; everything else is routed here."""
import sys, math
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
SD = "/Stepper Driver/"
def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def net(n):
    ni = b.FindNet(n)
    assert ni is not None, n
    return ni
def near(p, x, y, tol=0.03): return abs(ToMM(p.x) - x) < tol and abs(ToMM(p.y) - y) < tol

# ---------------------------------------------------------------- 1. remove the chip and its support parts
FPS = dict((f.GetReference(), f) for f in b.GetFootprints())   # look up once: proxies are lost after Remove()
ZONES = list(b.Zones()); TRACKS = list(b.GetTracks())
def FP(ref): return FPS[ref]
old = FP("U9")
old_path, old_sheet, old_file = old.GetPath(), old.GetSheetname(), old.GetSheetfile()
REMOVED = ["U9", "R57", "R60", "C48", "C45", "C47", "R58", "R59"]
for ref in REMOVED:
    b.Remove(FP(ref))

LOCAL = [n for n in ["Net-(U9-5VOUT)", "Net-(U9-BRA)", "Net-(U9-BRB)", "Net-(U9-CPI)", "Net-(U9-CPO)", "Net-(U9-VCP)", "Net-(U9-VREF)",
                     SD + "OA1", SD + "OA2", SD + "OB1", SD + "OB2", SD + "MS1", SD + "MS2"]]
BOX = (147.0, 163.3, 43.0, 51.0)   # old U9 area
def inbox(p): return BOX[0] < ToMM(p.x) < BOX[1] and BOX[2] < ToMM(p.y) < BOX[3]
SEGS = {   # explicit segments to delete: net -> [(layer, x1, y1, x2, y2)]
    "Net-(D50-A1)": [("F.Cu", 158.93, 34.98, 162.22, 34.98), ("F.Cu", 158.50, 35.40, 158.93, 34.98), ("F.Cu", 162.22, 34.98, 163.50, 36.25),
                     ("F.Cu", 161.31, 35.24, 161.05, 34.98), ("F.Cu", 162.31, 35.24, 161.31, 35.24),
                     ("B.Cu", 159.95, 34.75, 161.83, 34.75), ("B.Cu", 161.83, 34.75, 162.31, 35.24), ("B.Cu", 159.95, 34.55, 159.95, 34.75)],
    "Net-(D51-A2)": [("F.Cu", 146.10, 41.25, 146.10, 35.85), ("F.Cu", 146.10, 35.85, 147.12, 34.83), ("F.Cu", 146.50, 43.71, 146.50, 41.65),
                     ("F.Cu", 147.79, 45.00, 146.50, 43.71), ("F.Cu", 146.50, 41.65, 146.10, 41.25),
                     ("In1.Cu", 150.15, 33.06, 149.34, 33.86), ("In1.Cu", 150.15, 26.35, 150.15, 33.06), ("In1.Cu", 153.90, 22.60, 150.15, 26.35)],
    "Net-(D50-A2)": [("In1.Cu", 158.40, 31.27, 158.40, 25.10), ("In1.Cu", 158.40, 25.10, 160.90, 22.60)],
    "Net-(D51-A1)": [("In1.Cu", 157.40, 27.38, 157.40, 22.60), ("In1.Cu", 153.50, 31.28, 157.40, 27.38)],
    "+5V": [("In1.Cu", 144.87, 40.34, 151.32, 40.34), ("In1.Cu", 143.00, 42.22, 144.87, 40.34), ("In1.Cu", 142.21, 42.82, 142.65, 42.82), ("In1.Cu", 142.65, 42.82, 142.85, 42.62),
            ("In1.Cu", 142.85, 42.62, 143.00, 42.48), ("In1.Cu", 143.00, 42.48, 143.00, 42.22), ("In1.Cu", 151.32, 40.34, 151.64, 40.66),
            ("In1.Cu", 151.64, 40.66, 158.29, 40.66), ("In1.Cu", 158.29, 40.66, 167.16, 49.53)],
    "TMC2209_TX": [("F.Cu", 156.27, 49.31, 156.27, 49.67), ("F.Cu", 156.27, 49.67, 156.90, 50.30)],
}
VIAS = {   # vias to delete: net -> [(x, y)]
    "GND": [(147.90, 40.90), (147.90, 41.70), (147.90, 42.50), (161.65, 40.95), (161.65, 41.73), (161.65, 42.52), (144.65, 41.55),
            (142.30, 42.15), (143.50, 40.65), (143.50, 42.75), (160.97, 30.70), (161.55, 32.35), (162.95, 46.55),
            (152.00, 40.05), (157.50, 40.05)],   # last two: lowest of three GND vias at D55 / D54, in the way of the moved +5V track,
    "+12V": [(151.55, 43.55), (152.75, 44.40), (152.10, 43.20), (152.70, 43.80), (152.10, 44.00), (150.95, 43.15), (150.95, 43.95),
             (156.85, 43.80), (156.70, 44.45)],
}
log = {"tracks": 0, "vias": 0, "zones": 0}
found = set()
for t in TRACKS:
    n = t.GetNetname(); via = t.GetClass() == "PCB_VIA"
    kill = False
    if n in LOCAL:
        kill = True
    elif via:
        for (x, y) in VIAS.get(n, []):
            if near(t.GetPosition(), x, y): kill = True; found.add((n, x, y))
    else:
        ln = b.GetLayerName(t.GetLayer())
        for s in SEGS.get(n, []):
            if s[0] == ln and ((near(t.GetStart(), s[1], s[2]) and near(t.GetEnd(), s[3], s[4])) or (near(t.GetStart(), s[3], s[4]) and near(t.GetEnd(), s[1], s[2]))):
                kill = True; found.add((n,) + s)
        if n in ("GND", "+3.3V", "TMC2209_EN", "TMC2209_STEP", "TMC2209_DIR", "TMC2209_DIAG") and ln == "F.Cu" and inbox(t.GetStart()) and inbox(t.GetEnd()):
            kill = True
    if kill:
        b.Remove(t); log["vias" if via else "tracks"] += 1
want = sum(len(v) for v in SEGS.values()) + sum(len(v) for v in VIAS.values())
assert len(found) == want, "expected %d listed items, matched %d" % (want, len(found))

# F.Cu zones that only served U9's pads
for z in ZONES:
    bb = z.GetBoundingBox(); l, t_ = ToMM(bb.GetLeft()), ToMM(bb.GetTop())
    if z.GetNetname() in (SD + "OA1", SD + "OA2", SD + "OB1", SD + "OB2") or (z.GetNetname() == "+12V" and z.IsOnLayer(pcbnew.F_Cu) and 149.5 < l < 150.5 and 42.5 < t_ < 43.5):
        b.Remove(z); log["zones"] += 1
    elif z.GetNetname() in ("Net-(D50-A2)", "Net-(D51-A1)") and z.IsOnLayer(pcbnew.F_Cu):
        o = z.Outline()                      # filter "fingers": end them above the new pin row
        for i in range(o.TotalVertices()):
            v = o.CVertex(i)
            if ToMM(v.y) > 39.95: o.SetVertex(i, VECTOR2I(v.x, FromMM(39.95)))
        z.SetNeedRefill(True)
assert log["zones"] == 5, log

# ---------------------------------------------------------------- 2. the module socket footprint
PINS = [  # number, name, local x, local y (BTT top view: EN top-left, VM top-right), net
    ("1", "EN", 0, 0, "TMC2209_EN"), ("2", "MS1", 0, 2.54, SD + "MS1"), ("3", "MS2", 0, 5.08, SD + "MS2"), ("4", "RX/PDN_UART", 0, 7.62, "TMC2209_TX"),
    ("5", "TX", 0, 10.16, None), ("6", "CLK", 0, 12.70, "GND"), ("7", "STEP", 0, 15.24, "TMC2209_STEP"), ("8", "DIR", 0, 17.78, "TMC2209_DIR"),
    ("9", "GND", 12.7, 17.78, "GND"), ("10", "VIO", 12.7, 15.24, "+3.3V"), ("11", "B2", 12.7, 12.70, SD + "OB2"), ("12", "B1", 12.7, 10.16, SD + "OB1"),
    ("13", "A1", 12.7, 7.62, SD + "OA1"), ("14", "A2", 12.7, 5.08, SD + "OA2"), ("15", "GND", 12.7, 2.54, "GND"), ("16", "VM", 12.7, 0, "+12V"),
    ("17", "INDEX", 2.54, 0, None), ("18", "DIAG", 5.08, 0, "TMC2209_DIAG")]
fp = pcbnew.FOOTPRINT(b)
fp.SetFPID(pcbnew.LIB_ID("brineomatic_local", "BTT_TMC2209_V1.3_Socket"))
fp.SetReference("U9"); fp.SetValue("BTT TMC2209 V1.3 module (socketed)")
fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
for num, name, x, y, n in PINS:
    pad = pcbnew.PAD(fp)
    pad.SetNumber(num); pad.SetPinFunction(name)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_RECT if num == "1" else pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.F_Cu, VECTOR2I(FromMM(1.7), FromMM(1.7)))
    pad.SetDrillSize(VECTOR2I(FromMM(1.0), FromMM(1.0)))
    pad.SetLayerSet(pcbnew.PAD.PTHMask())
    pad.SetPosition(P(x, y))
    fp.Add(pad)
def shape(layer, x1, y1, x2, y2, w, rect=True):
    s = pcbnew.PCB_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_RECT if rect else pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetLayer(layer); s.SetWidth(FromMM(w)); fp.Add(s)
shape(pcbnew.F_SilkS, -1.27, -1.27, 13.97, 19.05, 0.15)        # module outline 15.24 x 20.32
shape(pcbnew.F_Fab, -1.27, -1.27, 13.97, 19.05, 0.10)
# courtyards = the socket strips only (2.54 mm wide bodies); the module sits about 8.5 mm above the board
cy = pcbnew.PCB_SHAPE(fp); cy.SetShape(pcbnew.SHAPE_T_POLY); cy.SetLayer(pcbnew.F_CrtYd); cy.SetWidth(FromMM(0.05))
cy.SetPolyPoints([P(-1.27, -1.27), P(6.35, -1.27), P(6.35, 1.27), P(1.27, 1.27), P(1.27, 19.05), P(-1.27, 19.05)]); fp.Add(cy)
shape(pcbnew.F_CrtYd, 11.43, -1.27, 13.97, 19.05, 0.05)
shape(pcbnew.F_SilkS, -1.27, -0.3, -1.9, -0.3, 0.15, rect=False)    # EN / pin 1 tick
fp.SetPosition(P(0, 0))
b.Add(fp)
fp.SetOrientationDegrees(-90)                       # 90 deg clockwise on screen
en = [p for p in fp.Pads() if p.GetNumber() == "1"][0].GetPosition()
fp.Move(VECTOR2I(FromMM(160.90) - en.x, FromMM(28.70) - en.y))
fp.SetPath(old_path); fp.SetSheetname(old_sheet); fp.SetSheetfile(old_file)
fp.Reference().SetPosition(P(152.0, 26.9)); fp.Reference().SetTextAngleDegrees(0)
fp.Value().SetVisible(False)
EXPECT = {"1": (160.90, 28.70), "8": (143.12, 28.70), "16": (160.90, 41.40), "9": (143.12, 41.40), "11": (148.20, 41.40), "14": (155.82, 41.40),
          "17": (160.90, 31.24), "18": (160.90, 33.78)}
for pad in fp.Pads():
    n = dict((q[0], q[4]) for q in PINS)[pad.GetNumber()]
    if n: pad.SetNet(net(n))
    if pad.GetNumber() in EXPECT:
        assert near(pad.GetPosition(), *EXPECT[pad.GetNumber()], tol=0.01), (pad.GetNumber(), ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y))

# ---------------------------------------------------------------- 3. parts that move (same nets, new place)
MOVES = {"FB4": (151.38, 43.70, 0), "FB3": (153.92, 45.30, 0), "D53": (144.75, 36.60, 180), "C55": (164.20, 46.20, 180), "FB5": (148.27, 45.00, 180),
         "TP45": (163.50, 38.30, None), "C54": (148.60, 48.90, 180), "C44": (144.40, 39.20, 180), "R1": (159.185, 26.13, 0), "R2": (154.995, 26.13, 180),
         "C46": (148.55, 37.85, None), "C49": (161.00, 37.85, None)}   # C46/C49: 0.3 mm north, clear of the socket strip
for ref, (x, y, rot) in MOVES.items():
    f = FP(ref)
    f.SetPosition(P(x, y))
    if rot is not None: f.SetOrientationDegrees(rot)
def padpos(ref, num):
    for p in FP(ref).Pads():
        if p.GetNumber() == num: return ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)
CHECK = {("FB4", "1"): (150.59, 43.70), ("FB3", "2"): (154.71, 45.30), ("D53", "1"): (146.15, 36.60), ("C55", "2"): (163.42, 46.20), ("FB5", "1"): (149.06, 45.00),
         ("C54", "2"): (147.82, 48.90), ("C44", "1"): (145.18, 39.20), ("R1", "1"): (158.36, 26.13), ("R2", "1"): (155.82, 26.13)}
for (ref, num), (x, y) in CHECK.items():
    px, py = padpos(ref, num)
    assert abs(px - x) < 0.03 and abs(py - y) < 0.03, (ref, num, px, py)

# ---------------------------------------------------------------- 4. new copper
LAY = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu}
def route(n, layer, w, pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(x1, y1)); t.SetEnd(P(x2, y2)); t.SetWidth(FromMM(w)); t.SetLayer(LAY[layer]); t.SetNet(net(n)); b.Add(t)
def via(n, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetWidth(pcbnew.F_Cu, FromMM(0.45)); v.SetDrill(FromMM(0.3)); v.SetNet(net(n)); b.Add(v)
# module motor pins -> ferrites (raw outputs)
route(SD + "OB2", "F", 0.6, [(148.20, 41.40), (148.20, 44.20), (149.00, 45.00), padpos("FB5", "1")])
route(SD + "OB1", "F", 0.6, [(150.74, 41.40), (150.74, 43.00), padpos("FB4", "1")])
route(SD + "OA1", "F", 0.6, [(153.28, 41.40), (153.28, 44.60), padpos("FB3", "1")])
route(SD + "OA2", "F", 0.6, [(155.82, 41.40), (155.82, 44.30), (156.52, 45.00), padpos("FB2", "1")])
# ferrites -> filter nodes, passing between the socket pins
route("Net-(D51-A1)", "F", 0.4, [padpos("D55", "1"), (153.30, 40.05), (152.01, 40.05), (152.01, 43.20), padpos("FB4", "2")])
route("Net-(D50-A2)", "F", 0.4, [padpos("D54", "2"), (155.72, 39.75), (154.55, 40.50), (154.55, 44.70), padpos("FB3", "2")])
route("Net-(D51-A2)", "F", 0.3, [padpos("FB5", "2"), (146.90, 44.42), (146.90, 37.60)])      # 0.3 mm between VIO / B2 pins and past the +12V via at 147.5,38.55
route("Net-(D51-A2)", "F", 0.4, [(146.90, 37.60), (146.90, 35.63), (147.70, 34.83), padpos("C56", "1")])
route("Net-(D51-A2)", "F", 0.4, [padpos("D53", "1"), (146.90, 36.60)])
route("+12V", "F", 0.3, [(147.50, 38.55), (148.30, 39.30)])                                  # C46 pad to its via (pour is squeezed by the track above)
route("Net-(D50-A1)", "F", 0.5, [padpos("D50", "1"), (158.80, 35.10), (162.17, 35.10), (162.31, 35.24), (163.50, 36.43)])
route("Net-(D50-A1)", "F", 0.5, [padpos("C55", "2"), (162.55, 45.00)])
via("Net-(D50-A1)", 163.50, 38.30)                                   # test point TP45 on the back
# filter nodes -> J21, between the control-row pins (0.25 -> 0.40 mm)
route("Net-(D50-A2)", "In1", 0.4, [(158.40, 31.27), (159.63, 30.04), (159.63, 26.40), (160.90, 25.13), (160.90, 22.60)])
route("Net-(D51-A1)", "In1", 0.4, [(153.50, 31.28), (154.55, 30.23), (154.55, 27.30), (157.40, 24.45), (157.40, 22.60)])
route("Net-(D51-A2)", "In1", 0.4, [(149.34, 33.86), (149.90, 33.86), (150.30, 33.46), (150.30, 32.60), (149.47, 31.77), (149.47, 27.30), (153.90, 22.87), (153.90, 22.60)])
# +5V inner track moved clear of the pin row
route("+5V", "In1", 0.25, [(142.21, 42.82), (141.75, 42.36), (141.75, 40.56), (142.31, 40.00), (159.63, 40.00), (159.63, 42.00), (167.16, 49.53)])
# MS1 / MS2 pull-downs
route(SD + "MS1", "F", 0.25, [padpos("R1", "1"), (158.36, 28.70)])
route(SD + "MS2", "F", 0.25, [padpos("R2", "1"), (155.82, 28.70)])
# the pin row cuts the inner planes: re-link the +12V plane island under C46 and give C51 its ground via back
route("+12V", "In2", 0.4, [(149.47, 40.20), (149.47, 42.70)])
route("+12V", "In2", 0.4, [(157.09, 40.20), (157.09, 42.70)])
via("GND", 162.20, 43.50)
# logic supply decoupling at the VIO pin
route("+3.3V", "F", 0.3, [(145.66, 41.40), padpos("C44", "1")])
# GND pin between the +12V and motor copper: tie it to the TVS ground pad above it
route("GND", "F", 0.4, [(158.36, 41.40), padpos("D54", "1")])

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
print("removed parts", REMOVED, log, "| moved", sorted(MOVES), "| saved", dst)
