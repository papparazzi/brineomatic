"""Rev D step 25 (independent review, major M2): the 12 V eFuse U3 (TPS16630PWPR) placed and routed between the reverse-polarity P-FETs
and the +12V rail. Run after sch_add_efuse.py; the step-25 netlist gives the new parts, their fields and their symbol links.
  1. U3 sits below the MOSFETs where the +12V area of step 24 was (that area, its 17 vias and the In1 TMC2209_DIAG detour through them
     are deleted; DIAG now runs straight under U3 on In1).
  2. Input: the MOSFET-source areas (top layer) are now net PFET_OUT and no longer touch +12V; their 14 vias go to a new PFET_OUT area
     on the bottom layer, which also takes D56's via and joins Q9's source to Q10's. The Q10 area runs on to U3's IN pins 1-3; P_IN,
     the UVLO/OVP divider R72-R74 (left of U3) and C63 (above it) tap it.
  3. Output: U3's OUT pins 18-20 and C22 share a new +12V area with five vias to the inner +12V plane (In2). TP41 (bottom test pad)
     moves onto one of those vias.
  4. ILIM R76, MODE R75 (0R) and IMON R77 right of U3; dVdT C15 below it; exposed pad with 14 vias to GND.
  5. PGOOD: from U3 pin 16 through a via and the bottom layer to the existing track to the buck enable (U2 pin 3); R22 (24k pull-up)
     moves to the right of the resistor column and joins the same bottom-layer track.
  6. D49 (SS34, output Schottky) moves to the free space between Q7 and F1 with its own +12V area and vias; the "FUSE 5x20" label moves
     to the right of F1. C22 moves 1 mm to the right. D20-A's via moves 0.2 mm so that R74 fits.
usage: pcb_add_efuse.py <in.kicad_pcb> <step-25 netlist .xml> <out.kicad_pcb>      (KiCad 10 Python)"""
import sys, os, xml.etree.ElementTree as ET
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
FPS = dict((f.GetReference(), f) for f in b.GetFootprints())
PS = "/Power Supply/"
P12, GND, PG, PFO, DIAG = "+12V", "GND", "PGOOD", PS + "PFET_OUT", "TMC2209_DIAG"
FPLIB = os.environ.get('KICAD10_FOOTPRINT_DIR', 'C:/Users/sascha/AppData/Local/Programs/KiCad/10.0/share/kicad/footprints') + '/'   # KiCad's library


def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def at(p, x, y): return abs(ToMM(p.x) - x) < 0.01 and abs(ToMM(p.y) - y) < 0.01
def pad(ref, num): return [p for p in FPS[ref].Pads() if p.GetNumber() == num][0]
def seg(t, a, c): return (at(t.GetStart(), *a) and at(t.GetEnd(), *c)) or (at(t.GetStart(), *c) and at(t.GetEnd(), *a))


def net(name):
    n = b.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n)
    return n


def track(name, layer, w, *pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(net(name)); b.Add(t)


def via(name, x, y, dia):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetWidth(FromMM(dia)); v.SetDrill(FromMM(0.3)); v.SetNet(net(name)); b.Add(v)


def zone_outline(z, pts):
    o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
    for x, y in pts: o.Append(FromMM(x), FromMM(y))


def new_zone(name, layer, prio, pts):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net(name)); z.SetAssignedPriority(prio)
    z.SetLocalClearance(FromMM(0.25)); z.SetMinThickness(FromMM(0.25)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); zone_outline(z, pts); b.Add(z)


# ---- the step-25 netlist: new parts with fields and symbol links, and every pin's net
root = ET.parse(sys.argv[2]).getroot()
COMP, PIN = {}, {}
for c in root.find('components'):
    COMP[c.get('ref')] = c
for n in root.find('nets'):
    for nd in n.findall('node'):
        PIN[(nd.get('ref'), nd.get('pin'))] = n.get('name')

# ---- starting state (step 24)
assert 'U3' not in FPS and 'R76' not in FPS and b.FindNet(PFO) is None
for ref, x, y in (("Q9", 139.0, 54.5), ("Q10", 139.0, 60.5), ("D56", 143.8, 58.0), ("R78", 143.8, 62.0), ("C22", 148.9, 64.6),
                  ("D49", 148.8, 68.1), ("R22", 141.849, 69.6), ("TP41", 146.4, 67.6)):
    assert at(FPS[ref].GetPosition(), x, y), ref
for ref, num in (("Q9", "2"), ("Q10", "2"), ("D56", "1")):
    assert pad(ref, num).GetNetname() == P12 and PIN[(ref, num)] == PFO
ZP = [z for z in b.Zones() if z.GetNetname() == P12 and z.GetAssignedPriority() in (12, 14)]
Z12 = [z for z in ZP if z.GetAssignedPriority() == 12]
Z9 = [z for z in ZP if z.GetAssignedPriority() == 14 and z.Outline().BBox().GetTop() < FromMM(55)]
Z10 = [z for z in ZP if z.GetAssignedPriority() == 14 and z.Outline().BBox().GetTop() > FromMM(60)]
assert len(Z12) == 1 and len(Z9) == 1 and len(Z10) == 1 and Z12[0].GetLayerSet().Contains(pcbnew.B_Cu)
TR = list(b.GetTracks())
VIAS = [t for t in TR if t.GetClass() == "PCB_VIA"]


def in_zone(z, v): return z.Outline().Contains(v.GetPosition())


# ---- 1. delete: the +12V area where U3 goes (and its vias), the DIAG detour, the old PGOOD track to R22, vias that the new parts cover
kill = [v for v in VIAS if v.GetNetname() == P12 and in_zone(Z12[0], v)]
assert len(kill) == 17, len(kill)
DIAG_KEEP = (((147.725, 62.741), (153.974, 56.493)), ((140.696, 67.368), (129.637, 78.427)))
dk = [t for t in TR if t.GetNetname() == DIAG and t.GetLayer() == pcbnew.In1_Cu and t.GetClass() == "PCB_TRACK"
      and ToMM(t.GetStart().x) < 148 and ToMM(t.GetStart().y) > 62.5 and not any(seg(t, a, c) for a, c in DIAG_KEEP)
      and max(ToMM(t.GetStart().x), ToMM(t.GetEnd().x)) > 140.69]
assert len(dk) == 19, len(dk)
kill += dk
pg = [t for t in TR if t.GetNetname() == PG and any(seg(t, a, c) for a, c in (((141.024, 69.6), (138.5, 69.6)), ((138.5, 69.6), (138.249, 69.349)),
                                                                                ((138.249, 69.349), (136.398, 71.2))))]
assert len(pg) == 3
kill += pg
GVIA = ((149.3, 63.8), (149.3, 64.6), (149.3, 65.4), (151.8, 64.4), (151.8, 65.7),      # under C22's new place
        (149.3, 66.7), (149.1, 68.1), (149.2, 69.6), (152.3, 66.8), (152.5, 68.1), (152.3, 69.6),   # D49's old place: R75-R77, R22
        (142.3, 61.7))                                                                    # C63 (R78's ground via; replaced below)
gv = [v for v in VIAS if v.GetNetname() == GND and any(at(v.GetPosition(), *q) for q in GVIA)]
assert len(gv) == len(GVIA), len(gv)
kill += gv
kill += [t for t in TR if t.GetNetname() == GND and t.GetClass() == "PCB_TRACK" and seg(t, (143.8, 61.2), (142.3, 61.7))]
d20 = [t for t in TR if t.GetNetname() == "Net-(D20-A)" and (seg(t, (135.125, 69.1), (136.1, 69.1)) or seg(t, (135.9, 68.9), (136.1, 69.1))
                                                           or (t.GetClass() == "PCB_VIA" and at(t.GetPosition(), 136.1, 69.1)))]
assert len(d20) == 3
kill += d20
assert len(kill) == 17 + 19 + 3 + 12 + 1 + 3
for t in kill: b.Remove(t)
b.Remove(Z12[0])
old_pg = [t for t in b.GetTracks() if t.GetNetname() == PG and seg(t, (136.398, 71.2), (125.3, 71.2))]
assert len(old_pg) == 1
old_pg[0].SetStart(P(135.2, 71.2))        # the PGOOD track to U2 now starts at the via that brings it up from the bottom layer

# ---- 2. input side: sources, D56 and their vias on PFET_OUT
for ref, num in (("Q9", "2"), ("Q10", "2"), ("D56", "1")): pad(ref, num).SetNet(net(PFO))
p9 = [v for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == P12 and in_zone(Z9[0], v)]
p10 = [v for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == P12 and in_zone(Z10[0], v)]
assert len(p9) == 6 and len(p10) == 8, (len(p9), len(p10))
d56 = [t for t in b.GetTracks() if t.GetNetname() == P12 and ((t.GetClass() == "PCB_VIA" and at(t.GetPosition(), 142.8, 59.6)) or seg(t, (143.8, 59.6), (142.8, 59.6)))]
assert len(d56) == 2
for t in p9 + p10 + d56: t.SetNet(net(PFO))
for z in (Z9[0], Z10[0]): z.SetNet(net(PFO))
zone_outline(Z9[0], ((136.4, 54.55), (138.85, 54.55), (138.85, 58.85), (136.4, 58.85)))          # no longer joins the TP15 pour
zone_outline(Z10[0], ((136.4, 60.6), (138.85, 60.6), (138.85, 61.65), (141.4, 61.65), (141.4, 62.35), (142.9, 62.35), (142.9, 63.55),
                      (141.35, 63.55), (141.35, 65.85), (136.4, 65.85)))                           # down to U3 pins 1-3, C63, R72
new_zone(PFO, pcbnew.B_Cu, 14, ((136.6, 55.3), (143.3, 55.3), (143.3, 65.0), (136.6, 65.0)))    # joins Q9's and Q10's vias and D56
for x in (136.9, 137.8, 138.7): via(PFO, x, 64.5, 0.6)

# ---- new footprints from the KiCad library, linked to their symbols

def place(ref, x, y, rot, refpos=None, refrot=0):      # refpos None: reference hidden (no free silkscreen spot)
    c = COMP[ref]
    lib, name = c.findtext('footprint').split(':')
    fp = pcbnew.FootprintLoad(FPLIB + lib + '.pretty', name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    for f in list(fp.GetFields()):
        if f.GetName() not in ('Reference', 'Value', 'Datasheet', 'Description'): fp.Remove(f)
    fp.SetReference(ref); fp.SetValue(c.findtext('value'))
    fields = dict((f.get('name'), f.text or '') for f in c.find('fields'))      # as the schematic has them (Datasheet '~' arrives as '')
    for k, v in fields.items():
        if k in ('Footprint', 'Reference', 'Value'): continue
        fp.SetField(k, v); f = fp.GetField(k); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
    sp = c.find('sheetpath')
    fp.SetPath(pcbnew.KIID_PATH(sp.get('tstamps') + c.findtext('tstamps')))
    fp.SetSheetname(sp.get('names')); fp.SetSheetfile(dict((p.get('name'), p.get('value')) for p in c.findall('property'))['Sheetfile'])
    b.Add(fp)
    fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
    for p in fp.Pads():
        if p.GetNumber(): p.SetNet(net(PIN[(ref, p.GetNumber())]))
    r = fp.Reference(); r.SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); r.SetTextThickness(FromMM(0.15))   # the board's size
    if refpos:
        r.SetPosition(P(*refpos)); r.SetTextAngleDegrees(refrot)
    else:
        r.SetVisible(False)
    FPS[ref] = fp
    return fp


U3X, U3Y = 143.3, 67.2          # left pins x 139.65-141.225, right pins x 145.375-146.95; pin k (1-10) at y 64.275 + 0.65 (k - 1)
place('U3', U3X, U3Y, 0, (143.3, 71.4))
place('C63', 142.2, 62.1, 90, (141.1, 62.0), 90)
place('R72', 137.5, 66.25, 0)
place('R73', 137.5, 67.85, 180)
place('R74', 137.5, 69.65, 0)
place('C15', 140.4, 71.55, 0)
place('R77', 149.1, 67.2, 0)
place('R75', 149.1, 68.8, 0)
place('R76', 149.1, 70.4, 0)
for ref, num, n in (('U3', '1', PFO), ('U3', '18', P12), ('U3', '16', PG), ('U3', '21', GND), ('R72', '1', PFO), ('R73', '1', PS + 'EF_UVLO'),
                    ('R74', '2', GND), ('C15', '1', 'Net-(U3-dVdT)'), ('R76', '1', 'Net-(U3-ILIM)'), ('C63', '1', PFO)):
    assert pad(ref, num).GetNetname() == n, (ref, num, pad(ref, num).GetNetname())
assert at(pad('U3', '1').GetPosition(), 140.4375, 64.275) and at(pad('U3', '20').GetPosition(), 146.1625, 64.275)

# left of U3: P_IN, UVLO, OVP, GND, dVdT
track(PFO, pcbnew.F_Cu, 0.25, (140.1, 67.525), (139.2, 67.525), (139.2, 65.45))                     # P_IN (pin 6) up to the PFET_OUT area
track(PFO, pcbnew.F_Cu, 0.3, (136.675, 66.25), (136.675, 65.4))                                      # R72 to the PFET_OUT area
track(PS + "EF_UVLO", pcbnew.F_Cu, 0.25, (140.1, 68.175), (138.325, 68.175))                          # pin 7 - R73
track(PS + "EF_UVLO", pcbnew.F_Cu, 0.25, (138.325, 66.25), (138.325, 67.85))                          # R72 - R73
track(PS + "EF_OVP", pcbnew.F_Cu, 0.2, (140.1, 68.825), (136.675, 68.825))                            # pin 8, between R73 and R74
track(PS + "EF_OVP", pcbnew.F_Cu, 0.25, (136.675, 67.85), (136.675, 69.65))                           # R73 - R74
track(GND, pcbnew.F_Cu, 0.3, (138.325, 69.65), (138.325, 69.475), (142.0, 69.475))                     # R74 and pin 9 to the exposed pad
track("Net-(U3-dVdT)", pcbnew.F_Cu, 0.25, (140.1, 70.125), (139.625, 70.6), (139.625, 71.55))          # pin 10 - C15
track(GND, pcbnew.F_Cu, 0.3, (141.175, 71.55), (141.9, 70.825), (141.9, 70.3))                         # C15 - exposed pad
# C63 and R78 to ground through one via between them (replaces R78's via under C63)
track(GND, pcbnew.F_Cu, 0.3, (143.8, 61.175), (142.2, 61.325)); via(GND, 142.95, 61.25, 0.6)
# R24's ground pad lost its top-layer path to the ground pour (the divider sits there now): own via
via(GND, 135.75, 67.3, 0.45)
# D20-A: its via moves 0.2 mm left so that R74 fits; the bottom-layer track already ends there
track("Net-(D20-A)", pcbnew.F_Cu, 0.25, (135.125, 69.1), (135.7, 69.1), (135.9, 68.9)); via("Net-(D20-A)", 135.9, 68.9, 0.45)

# right of U3: ILIM, MODE, IMON to R76/R75/R77, their ground side to two vias
track("Net-(U3-ILIM)", pcbnew.F_Cu, 0.25, (146.5, 70.125), (148.275, 70.125))
track("Net-(U3-MODE)", pcbnew.F_Cu, 0.2, (146.5, 69.475), (147.5, 69.475), (148.0, 68.975))
track("Net-(U3-IMON)", pcbnew.F_Cu, 0.2, (146.5, 68.175), (147.35, 68.175), (148.0, 67.525))
track(GND, pcbnew.F_Cu, 0.3, (149.925, 67.2), (150.8, 66.8))
track(GND, pcbnew.F_Cu, 0.3, (149.925, 68.8), (150.8, 69.6), (149.925, 70.4))

# exposed pad: 14 vias to the ground planes, clear of the In1 tracks RX and DIAG that cross under U3 (x + y = 207.29 and 208.07)
for x in (142.35, 143.3, 144.25):
    for y in (66.7, 67.75, 68.8, 69.85): via(GND, x, y, 0.6)
via(GND, 144.4, 65.6, 0.6); via(GND, 144.45, 64.55, 0.6)
# DIAG on In1: straight from the kept segment at (147.725, 62.741) under U3 to the kept diagonal at (140.696, 67.368)
track(DIAG, pcbnew.In1_Cu, 0.2, (147.725, 62.741), (145.327, 62.741), (140.696, 67.368))

# ---- 3. output side: OUT pins and C22 on a new +12V area with five vias to In2; TP41 on one of them
FPS['C22'].SetPosition(P(149.9, 64.6))
new_zone(P12, pcbnew.F_Cu, 14, ((144.5, 62.65), (149.05, 62.65), (149.05, 65.9), (145.25, 65.9), (145.25, 63.7), (144.5, 63.7)))
for x, y in ((145.6, 63.4), (146.5, 63.4), (147.4, 63.4), (147.425, 64.45), (147.425, 65.35)): via(P12, x, y, 0.6)
FPS['TP41'].SetPosition(P(147.425, 64.45))
for x, y in ((152.25, 63.9), (152.25, 65.3)): via(GND, x, y, 0.45)                                    # C22's ground pad

# ---- 5. PGOOD: U3 pin 16 -> via -> bottom layer -> via at (135.2, 71.2) -> the existing track to U2; R22 joins on the bottom layer
FPS['R22'].SetPosition(P(151.72, 67.6)); FPS['R22'].SetOrientationDegrees(270)
assert pad('R22', '1').GetNetname() == P12 and at(pad('R22', '1').GetPosition(), 151.72, 66.775)
track(PG, pcbnew.F_Cu, 0.25, (146.5, 66.875), (146.95, 66.875), (147.45, 66.375)); via(PG, 147.45, 66.375, 0.45)
track(PG, pcbnew.B_Cu, 0.25, (147.45, 66.375), (147.45, 70.6))
track(PG, pcbnew.B_Cu, 0.25, (151.72, 69.3), (151.72, 70.6), (147.45, 70.6), (135.8, 70.6), (135.2, 71.2)); via(PG, 135.2, 71.2, 0.45)
track(PG, pcbnew.F_Cu, 0.25, (151.72, 68.425), (151.72, 69.3)); via(PG, 151.72, 69.3, 0.45)
track(P12, pcbnew.F_Cu, 0.3, (151.72, 66.775), (151.72, 65.95)); via(P12, 151.72, 65.95, 0.45)
via(GND, 152.35, 70.9, 0.45)

# ---- 6. D49 between Q7 and F1, cathode up on a small +12V area with three vias; the fuse label goes to the right of F1
FPS['D49'].SetPosition(P(150.0, 75.1)); FPS['D49'].SetOrientationDegrees(270)
assert pad('D49', '1').GetNetname() == P12 and at(pad('D49', '1').GetPosition(), 150.0, 73.1)
new_zone(P12, pcbnew.F_Cu, 14, ((148.3, 71.7), (151.8, 71.7), (151.8, 74.6), (148.3, 74.6)))
for x, y in ((148.75, 73.0), (148.75, 73.9), (151.3, 73.0)): via(P12, x, y, 0.6)
for x, y in ((148.75, 77.1), (151.3, 77.1)): via(GND, x, y, 0.45)
lbl = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT' and d.GetText() == 'FUSE\n5x20']
assert len(lbl) == 1 and at(lbl[0].GetPosition(), 150.2, 76.3)
lbl[0].SetText('FUSE 5x20'); lbl[0].SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); lbl[0].SetTextThickness(FromMM(0.15))
lbl[0].SetPosition(P(152.375, 75.0))     # one line between D49 and F1 (right of F1 is the 24 V warning, below it F1's pad and FID2)

# ---- silkscreen: references that the new parts cover move or are hidden (the board already hides 72, e.g. R69-R71 next to U3)
for ref, pos, ang in (('Q10', (136.5, 59.6), 90), ('C22', (150.0, 63.15), 0), ('D49', (150.0, 75.1), 0), ('R22', (151.75, 70.2), 0)):
    r = FPS[ref].Reference(); r.SetPosition(P(*pos)); r.SetTextAngleDegrees(ang)
for ref in ('C18', 'R24', 'D46'): FPS[ref].Reference().SetVisible(False)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[3], b, True)      # True: leave the .kicad_pro alone (otherwise pcbnew rewrites it with default settings)
print("deleted %d tracks/vias and the +12V area under U3; added U3, C15, C63, R72-R77" % len(kill))
