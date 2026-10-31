"""Add a 14 mm strip on the top edge of the board and put the 3.5 mm screw terminals there (entry face at the edge);
keep every existing circuit where it is.  J23 returns to its Rev-C1 position at the bottom edge.
usage: pcb_screw2.py <in.kicad_pcb> <netlist.xml> <out.kicad_pcb>"""
import sys, re, os, uuid, xml.etree.ElementTree as ET
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
inp, xmlf, outp = sys.argv[1:4]
FPD = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'); LIB = 'Connector_Phoenix_MC'
NAME = {2: 'PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal', 3: 'PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal', 4: 'PhoenixContact_MC_1,5_4-G-3.5_1x04_P3.50mm_Horizontal'}
YT = 22.6
LEFT = {2: 6.5, 3: 10.0, 4: 13.5}; RIGHT = 3.2
PL = {}; xx = 71.5
for r, n in (('J4', 3), ('J11', 3), ('J3', 2), ('J18', 2), ('J22', 3), ('J5', 3), ('J21', 4)):
    xx += LEFT[n]; PL[r] = (n, round(xx, 2), YT, 180); xx += RIGHT + 1.2
PL['J23'] = (3, 88.95, 87.5, 0)
print('right edge of last terminal', xx)
b0 = pcbnew.LoadBoard(inp)
OLD_EDGE = [d for d in b0.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
b = b0
txt = open(inp).read()
# --- templates via temp board
need = sorted({PL[r][0] for r in PL}); blocks = []
for i, n in enumerate(need):
    m = open(f'{FPD}/{LIB}.pretty/{NAME[n]}.kicad_mod').read()
    m = m.replace(f'(footprint "{NAME[n]}"', f'(footprint "{LIB}:{NAME[n]}"', 1)
    m = re.sub(r'(\(layer "F\.Cu"\))', r'\1\n\t(at 0 0)', m, 1); m = m.replace('"REF**"', f'"TPL{i}"', 1); blocks.append(m)
tmp = outp + '.tpl.kicad_pcb'
open(tmp, 'w').write(txt.rstrip()[:-1] + '\n' + '\n'.join(blocks) + '\n)\n')
b = pcbnew.LoadBoard(tmp)
OLD_EDGE = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
fps = {f.GetReference(): f for f in b.GetFootprints()}
tpl = {n: fps[f'TPL{i}'] for i, n in enumerate(need)}
old_names = {r: [p.GetNetname() for p in fps[r].Pads()] for r in PL}
dead = [t for t in b.GetTracks() if t.GetNetname() in ('Net-(D44-A1)', 'Net-(D44-A2)') and 84 < pcbnew.ToMM(t.GetX()) < 98 and 76 < pcbnew.ToMM(t.GetY()) < 92 and t.GetClass() == 'PCB_TRACK' and pcbnew.ToMM(t.GetY()) > 83]
new = {}
for r, (n, x, y, a) in PL.items():
    f = pcbnew.FOOTPRINT(tpl[n]); f.SetReference(r); f.SetOrientationDegrees(a); f.SetPosition(VECTOR2I(mm(x), mm(y))); new[r] = f
for t in dead: b.Remove(t)
for r in PL: b.Remove(fps[r])
for i in range(len(need)): b.Remove(fps[f'TPL{i}'])
for f in new.values(): b.Add(f)
for d in OLD_EDGE: b.Remove(d)
def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(VECTOR2I(mm(x1), mm(y1))); s.SetEnd(VECTOR2I(mm(x2), mm(y2))); s.SetWidth(mm(0.1)); b.Add(s)
def arc(cx, cy, sx, sy, ex, ey):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetCenter(VECTOR2I(mm(cx), mm(cy))); s.SetStart(VECTOR2I(mm(sx), mm(sy))); s.SetEnd(VECTOR2I(mm(ex), mm(ey))); s.SetWidth(mm(0.1)); b.Add(s)
X0, X1, Y0, Y1, R = 34.0, 169.0, 12.0, 96.5, 3.0
seg(X0 + R, Y0, X1 - R, Y0); seg(X0 + R, Y1, X1 - R, Y1); seg(X0, Y0 + R, X0, Y1 - R); seg(X1, Y0 + R, X1, Y1 - R)
arc(X0 + R, Y0 + R, X0, Y0 + R, X0 + R, Y0); arc(X1 - R, Y0 + R, X1 - R, Y0, X1, Y0 + R)
arc(X0 + R, Y1 - R, X0 + R, Y1, X0, Y1 - R); arc(X1 - R, Y1 - R, X1, Y1 - R, X1 - R, Y1)
for r, dy in (('H1', -16.9), ('H3', 0.0), ('H2', 4.0), ('H4', 4.0)):
    f = {x.GetReference(): x for x in b.GetFootprints()}[r]; p = f.GetPosition(); f.SetPosition(VECTOR2I(p.x, p.y + mm(dy)))
root = ET.parse(xmlf).getroot(); comps = {c.get('ref'): c for c in root.find('components')}
pin_net = {}
for nn in root.find('nets'):
    for nd in nn:
        if nd.tag == 'node': pin_net[(nd.get('ref'), nd.get('pin'))] = nn.get('name')
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
    v = comps[r].findtext('value')
    if v and f.GetValue() != v: f.SetValue(v)
b.Save(outp); os.remove(tmp)
t = open(outp).read(); seen = set()
def fix(m):
    u = m.group(2)
    if u in seen: u = str(uuid.uuid4())
    seen.add(u); return m.group(1) + u + m.group(3)
open(outp, 'w').write(re.sub(r'(\(uuid ")([0-9a-f-]{36})(")', fix, t))
print('done; removed J23 tracks', len(dead))
