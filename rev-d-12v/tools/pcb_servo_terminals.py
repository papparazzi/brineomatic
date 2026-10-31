"""Replace the 2x3 headers J1, J6 by four 3-pin 3.5 mm terminals (J6, J29, J1, J28) in a new strip on the east edge (entry faces east).
usage: pcb_servo_terminals.py in.kicad_pcb netlist.xml out.kicad_pcb       (phase 1: footprints+outline)
       pcb_servo_terminals.py in.kicad_pcb netlist.xml out.kicad_pcb nets  (phase 2, fresh process: pad nets)"""
import sys, re, uuid, xml.etree.ElementTree as ET
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
inp, xmlf, outp = sys.argv[1:4]
XP = 176.0                      # x of the pad row
ORDER = ['J6', 'J29', 'J1', 'J28']
Y_TOP, PITCH = 14.5, 14.3       # courtyard top of the first terminal, pitch along y
root = ET.parse(xmlf).getroot(); comps = {c.get('ref'): c for c in root.find('components')}
pin_net = {}
for nn in root.find('nets'):
    for nd in nn:
        if nd.tag == 'node': pin_net[(nd.get('ref'), nd.get('pin'))] = nn.get('name')
PHASE2 = len(sys.argv) > 4 and sys.argv[4] == 'nets'
b = pcbnew.LoadBoard(inp)
if not PHASE2:
    pass
if not PHASE2:
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    tpl = fps['J4']                 # a 3-pin 3.5 mm terminal already on the board
    new = {}
    for i, r in enumerate(ORDER):
        f = pcbnew.FOOTPRINT(tpl); f.SetReference(r); f.SetOrientationDegrees(90)
        f.SetPosition(VECTOR2I(mm(XP), mm(0)))
        c = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
        y_off = mm(Y_TOP + i * PITCH) - c.GetY()          # put the courtyard top at the wanted y
        f.SetPosition(VECTOR2I(mm(XP), mm(0) + y_off)); new[r] = f
    rx = max(pcbnew.ToMM(f.GetCourtyard(pcbnew.F_CrtYd).BBox().GetRight()) for f in new.values())
    X0, X1, Y0, Y1, R = 34.0, round(rx + 2.05, 1), 12.0, 96.5, 3.0
    print('terminal courtyard right', rx, 'new east edge', X1)
    for r in ('J1', 'J6'): b.Remove(fps[r])
    for f in new.values(): b.Add(f)
    for d in [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]: b.Remove(d)
    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(VECTOR2I(mm(x1), mm(y1))); s.SetEnd(VECTOR2I(mm(x2), mm(y2))); s.SetWidth(mm(0.1)); b.Add(s)
    def arc(cx, cy, sx, sy, ex, ey):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(VECTOR2I(mm(cx), mm(cy))); s.SetStart(VECTOR2I(mm(sx), mm(sy))); s.SetEnd(VECTOR2I(mm(ex), mm(ey))); s.SetWidth(mm(0.1)); b.Add(s)
    seg(X0 + R, Y0, X1 - R, Y0); seg(X0 + R, Y1, X1 - R, Y1); seg(X0, Y0 + R, X0, Y1 - R); seg(X1, Y0 + R, X1, Y1 - R)
    arc(X0 + R, Y0 + R, X0, Y0 + R, X0 + R, Y0); arc(X1 - R, Y0 + R, X1 - R, Y0, X1, Y0 + R)
    arc(X0 + R, Y1 - R, X0 + R, Y1, X0, Y1 - R); arc(X1 - R, Y1 - R, X1, Y1 - R, X1 - R, Y1)
    b.Save(outp); sys.exit(0)
def net(name):
    ni = b.FindNet(name)
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni)
    return ni
for f in b.GetFootprints():
    r = f.GetReference()
    if r not in comps: continue
    for p in f.Pads():
        nm = pin_net.get((r, p.GetNumber()))
        if nm: p.SetNet(net(nm))
        else: p.SetNetCode(0)
b.Save(outp)
t = open(outp).read(); seen = set()
def fix(m):
    u = m.group(2)
    if u in seen: u = str(uuid.uuid4())
    seen.add(u); return m.group(1) + u + m.group(3)
open(outp, 'w').write(re.sub(r'(\(uuid ")([0-9a-f-]{36})(")', fix, t))
print('saved', outp)
