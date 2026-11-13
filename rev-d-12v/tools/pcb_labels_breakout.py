"""Rev D step 19 (on top of step 17, soldered TMC2209): silkscreen and breakout only, no net changes.
 - every dev-board pin labelled on the front; breakout solder pads (1.6 mm pad, 1.0 mm hole) beside every unused dev-board pin,
   plus one 3V3 and one GND pad; the breakout pads are extra pads of U5 with the same pad number, so the netlist is unchanged
 - board outline 3 mm wider on the west side to make room for the west label column
 - every sensor, servo, TDS and stepper plug labelled in the knockout style (white box, clear letters) with a per-pin legend
 - two dead track stubs removed
usage: pcb_labels_breakout.py <in.kicad_pcb> <out.kicad_pcb>      (KiCad 10 Python)"""
import sys, math
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
FPS = dict((f.GetReference(), f) for f in b.GetFootprints())      # look everything up before any Remove()
TRACKS = list(b.GetTracks()); DRAW = list(b.GetDrawings())
def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
WIDEN = 3.0

# ---------------------------------------------------------------- 1. outline: west edge 34.0 -> 31.0
n = 0
for d in DRAW:
    if d.GetLayer() != pcbnew.Edge_Cuts: continue
    s, e = d.GetStart(), d.GetEnd()
    if d.ShowShape() == "Arc" and min(ToMM(s.x), ToMM(e.x)) < 35: d.Move(VECTOR2I(FromMM(-WIDEN), 0)); n += 1
    elif d.ShowShape() == "Line":
        if abs(ToMM(s.x) - 34.0) < 0.01 and abs(ToMM(e.x) - 34.0) < 0.01: d.Move(VECTOR2I(FromMM(-WIDEN), 0)); n += 1
        elif abs(ToMM(s.x) - 37.0) < 0.01: d.SetStart(VECTOR2I(s.x - FromMM(WIDEN), s.y)); n += 1
        elif abs(ToMM(e.x) - 37.0) < 0.01: d.SetEnd(VECTOR2I(e.x - FromMM(WIDEN), e.y)); n += 1
assert n == 5, n

# ---------------------------------------------------------------- 2. dev-board pin names (Espressif ESP32-S3-DevKitC-1 v1.1 header order, top = antenna end)
WEST = ["3V3", "3V3", "RST", "4", "5", "6", "7", "15", "16", "17", "18", "8", "3", "46", "9", "10", "11", "12", "13", "14", "5V", "GND"]
EAST = ["GND", "TX", "RX", "1", "2", "42", "41", "40", "39", "38", "37", "36", "35", "0", "45", "48", "47", "21", "20", "19", "GND", "GND"]
XW, XE, Y0, PITCH = 38.00, 60.86, 33.70, 2.54
u5 = FPS["U5"]
padat = {}
for p in u5.Pads(): padat[(round(ToMM(p.GetPosition().x), 2), round(ToMM(p.GetPosition().y), 2))] = p
FREE_NETS = ("/ESP32-S3/EN", "/ESP32-S3/GPIO3", "/ESP32-S3/GPIO46", "/ESP32-S3/ESP_TXD0", "/ESP32-S3/ESP_RXD0", "/ESP32-S3/GPIO38", "/ESP32-S3/GPIO37",
             "/ESP32-S3/GPIO36", "/ESP32-S3/GPIO35", "/ESP32-S3/GPIO0_BOOT", "/ESP32-S3/GPIO45", "/ESP32-S3/ESP_USB+", "/ESP32-S3/ESP_USB-")
EXTRA = {("W", 0): "3V3", ("E", 0): "GND"}       # one supply and one ground pad for add-on wiring

def clear_of_everything(x, y, r, net, layers=None, skip=()):
    """smallest copper gap (mm) between a round shape at x,y and anything on another net (all copper layers unless given)"""
    best = 9.9
    for t in TRACKS:
        if t.GetNetname() == net: continue
        if t.GetClass() == "PCB_VIA":
            d = math.hypot(ToMM(t.GetPosition().x) - x, ToMM(t.GetPosition().y) - y) - ToMM(t.GetWidth(pcbnew.F_Cu)) / 2 - r
        else:
            if layers and t.GetLayer() not in layers: continue
            a, c = t.GetStart(), t.GetEnd(); ax, ay, cx, cy = ToMM(a.x), ToMM(a.y), ToMM(c.x), ToMM(c.y)
            dx, dy = cx - ax, cy - ay; L = dx * dx + dy * dy
            u = 0 if L == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
            d = math.hypot(x - (ax + u * dx), y - (ay + u * dy)) - ToMM(t.GetWidth()) / 2 - r
        best = min(best, d)
    for ref, fp in FPS.items():
        for p in fp.Pads():
            if p in skip or (p.GetNetname() == net and net): continue
            bb = p.GetBoundingBox()
            ddx = max(ToMM(bb.GetLeft()) - x, 0, x - ToMM(bb.GetRight())); ddy = max(ToMM(bb.GetTop()) - y, 0, y - ToMM(bb.GetBottom()))
            best = min(best, math.hypot(ddx, ddy) - r)
    return best

def text(s, x, y, h=1.0, w=None, th=0.15, layer=pcbnew.F_SilkS, ang=0, just="c", ko=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer); t.SetPosition(P(x, y))
    t.SetTextSize(VECTOR2I(FromMM(w or h), FromMM(h))); t.SetTextThickness(FromMM(th)); t.SetTextAngleDegrees(ang)
    t.SetHorizJustify({"l": pcbnew.GR_TEXT_H_ALIGN_LEFT, "r": pcbnew.GR_TEXT_H_ALIGN_RIGHT, "c": pcbnew.GR_TEXT_H_ALIGN_CENTER}[just])
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    if layer == pcbnew.B_SilkS: t.SetMirrored(True)
    t.SetIsKnockout(ko); b.Add(t); return t

breakout = []
for side, names, xpin, cands, sgn in (("W", WEST, XW, (35.0, 34.7, 34.4, 34.1, 33.6, 33.1, 40.54, 41.0, 41.5), -1), ("E", EAST, XE, (63.40, 63.9, 64.4, 64.9, 65.4, 65.9, 66.4, 66.9, 67.4, 58.32, 57.8, 57.3, 56.8, 56.3), 1)):   # last candidates of each list: inboard, under the dev board
    for i, name in enumerate(names):
        y = round(Y0 + i * PITCH, 2); pad = padat[(xpin, y)]
        xl = (XW - 4.1) if side == "W" else (XE + 3.85)          # label column when the row has no breakout pad... kept identical for all rows
        if pad.GetNetname() in FREE_NETS or (side, i) in EXTRA:
            px = None
            for dy in (0, -0.45, 0.45, -0.9, 0.9, -1.27, 1.27):                 # straight out first; otherwise nudge the pad to clear inner-layer tracks
                for cx in cands:
                    gap = clear_of_everything(cx, y + dy, 0.8, pad.GetNetname())
                    m = int(math.hypot(cx - xpin, dy) / 0.2)
                    trk = min(clear_of_everything(xpin + (cx - xpin) * k / m, y + dy * k / m, 0.125, pad.GetNetname(), layers=(pcbnew.F_Cu,), skip=(pad,)) for k in range(5, m + 1))
                    if gap >= 0.25 and trk >= 0.2: px = cx; break
                if px is not None: break
            assert px is not None, (side, name, y)
            ypad = y + dy
            q = pcbnew.PAD(u5); q.SetNumber(pad.GetNumber()); q.SetPinFunction(pad.GetPinFunction()); q.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            q.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE); q.SetSize(pcbnew.F_Cu, VECTOR2I(FromMM(1.6), FromMM(1.6))); q.SetDrillSize(VECTOR2I(FromMM(1.0), FromMM(1.0)))
            q.SetLayerSet(pcbnew.PAD.PTHMask()); q.SetPosition(P(px, ypad)); u5.Add(q); q.SetNet(pad.GetNet())
            t = pcbnew.PCB_TRACK(b); t.SetStart(P(xpin, y)); t.SetEnd(P(px, ypad)); t.SetWidth(FromMM(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNet(pad.GetNet()); b.Add(t)
            breakout.append((side, name, px, round(ypad, 2)))
            outboard = (px - xpin) * sgn > 0
            if outboard: xl = px + sgn * 1.15
            text(name, px + (sgn if outboard else -sgn) * 1.15, ypad, h=0.9, w=0.8, layer=pcbnew.B_SilkS, just=("r" if side == "E" else "l") if outboard else ("l" if side == "E" else "r"))   # same label on the back (mirrored text)
            if outboard: y = ypad
        text(name, xl, y, h=1.0, w=0.8, just="r" if side == "W" else "l")

# ---------------------------------------------------------------- 3. plug labels, knockout style
NAME = {"Product Flowmeter": "PROD FLOW", "Brine Flowmeter": "BRINE FLOW", "High Pressure Sensor": "HI PRES", "Low Pressure Sensor": "LO PRES",
        "Water Temperature": "WATER TEMP", "Motor Temperature": "MOTOR TEMP", "Stepper Driver": "STEPPER", "Brine TDS": "BRINE\nTDS", "Product TDS": "PROD\nTDS"}
SHEET = {"J4": "Product Flowmeter", "J11": "Brine Flowmeter", "J3": "High Pressure Sensor", "J18": "Low Pressure Sensor", "J22": "Water Temperature",   # from the schematic netlist
         "J5": "Motor Temperature", "J21": "Stepper Driver", "J6": "Servos", "J29": "Servos", "J1": "Brine TDS", "J28": "Product TDS", "J10": "Power Supply", "J23": "RS485",
         "J7": "Solenoid Driver 1", "J12": "Solenoid Driver 2", "J14": "Solenoid Driver 3", "J16": "Solenoid Driver 4", "J25": "Solenoid Driver 5"}
def legend(netname, ref, num):
    n = netname.split("/")[-1]
    if n == "GND": return "GND"
    if n in ("+5V", "5V_HIGH_POWER"): return "5V"
    if n == "+12V": return "12V"
    if n == "+3.3V": return "3V3"
    if ref == "J21": return {"Net-(D51-A2)": "B2", "Net-(D51-A1)": "B1", "Net-(D50-A2)": "A1", "Net-(D50-A1)": "A2"}[n]
    return "S"
OLD = {"PROD FLOW", "BRINE FLOW", "HI PRES", "LO PRES", "WATER\nTEMP", "MOTOR\nTEMP", "STEP\nPER", "BRINE", "PROD", "-", "+", "S"}
kill = [d for d in DRAW if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.F_SilkS and d.GetText() in OLD]
assert len(kill) == 21, len(kill)
done = []
for ref in sorted(FPS):
    fp = FPS[ref]
    if not ref.startswith("J") or ref == "J2": continue
    pads = sorted(fp.Pads(), key=lambda p: int(p.GetNumber()))
    xs = [ToMM(p.GetPosition().x) for p in pads]; ys = [ToMM(p.GetPosition().y) for p in pads]
    sheet = SHEET[ref]; rot = fp.GetOrientationDegrees()
    fp.Reference().SetVisible(False)                               # the function label replaces the J-number on the silkscreen
    if rot == 180:                                                # top edge: name under the plug, legend under the name
        cx = sum(xs) / len(xs)
        text(NAME[sheet].replace("\n", " "), cx, 26.45, h=1.2, th=0.2, ko=True)
        for p, x in zip(pads, xs): text(legend(p.GetNetname(), ref, p.GetNumber()), x, 28.35, h=0.9, w=0.8, th=0.16, ko=True)
        done.append(ref)
    elif rot == 90:                                               # east edge: name and legend west of the plug, turned 90 deg
        cy = sum(ys) / len(ys)
        if sheet == "Servos":
            for d in DRAW:
                if d.GetClass() == "PCB_TEXT" and d.GetText().startswith("SERVO") and abs(ToMM(d.GetPosition().y) - cy) < 1: d.SetIsKnockout(True); d.SetTextThickness(FromMM(0.2))
        else:
            text(NAME[sheet], 169.5, cy - 0.9, h=1.0, th=0.2, ang=90, ko=True)
        for p, y in zip(pads, ys): text(legend(p.GetNetname(), ref, p.GetNumber()), 172.2, y, h=0.9, w=0.8, th=0.16, ang=90, ko=True)     # clear of the footprint's pin-1 triangle
        done.append(ref)
    # relays (bottom edge): "RELAY n" stays as it is. There is no free silkscreen between the label, the flyback diodes and the plug
    # for a per-pin legend; pin 1 (left, marked by the footprint triangle) is +12V, pin 2 is the switched return.
print("plug labels:", done, "| unchanged (already knockout with legend): J10 POWER, J23 RS485; J2 I2C has its name only")

# ---------------------------------------------------------------- 4. dead stubs reported by DRC in step 17
STUB = [("+12V", 140.40, 42.40), ("Net-(U9-VREF)", 160.36, 47.36)]
gone = 0
for t in TRACKS:
    if t.GetClass() == "PCB_VIA": continue
    for net, x, y in STUB:
        if t.GetNetname() == net and any(abs(ToMM(q.x) - x) < 0.03 and abs(ToMM(q.y) - y) < 0.03 for q in (t.GetStart(), t.GetEnd())) and (net != "Net-(U9-VREF)" or ToMM(t.GetLength()) < 0.05):
            kill.append(t); gone += 1
assert gone == 2, gone
for k in kill: b.Remove(k)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
print("breakout pads:", [(s, n, x) for s, n, x, y in breakout])
