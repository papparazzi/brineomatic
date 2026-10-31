"""Replace the JST-PH sensor/stepper connectors by 3.5 mm pluggable screw terminals (KiCad Phoenix MC footprints) and
delete the old escape tracks so the nets can be re-routed.  usage: pcb_screw.py <in.kicad_pcb> <netlist.xml> <out.kicad_pcb>"""
import sys, re, os, uuid, xml.etree.ElementTree as ET
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
inp, xmlf, outp = sys.argv[1:4]
FPD = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
LIB = 'Connector_Phoenix_MC'
NAME = {2: 'PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal', 3: 'PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal', 4: 'PhoenixContact_MC_1,5_4-G-3.5_1x04_P3.50mm_Horizontal'}
# ref -> (pins, pad1 x, pad1 y, rotation)
Y = 31.6
PL = {'J4': (3, 79.65, Y, 180), 'J11': (3, 90.4, Y, 180), 'J3': (2, 97.45, Y, 180), 'J18': (2, 104.45, Y, 180),
      'J22': (3, 123.1, Y, 180), 'J5': (3, 133.7, Y, 180), 'J21': (4, 160.0, Y, 180), 'J23': (3, 88.95, 87.5, 0)}
txt = open(inp).read()
need = sorted({PL[r][0] for r in PL})
blocks = []
for i, n in enumerate(need):
    m = open(f'{FPD}/{LIB}.pretty/{NAME[n]}.kicad_mod').read()
    m = m.replace(f'(footprint "{NAME[n]}"', f'(footprint "{LIB}:{NAME[n]}"', 1)
    m = re.sub(r'(\(layer "F\.Cu"\))', r'\1\n\t(at 0 0)', m, 1)
    m = m.replace('"REF**"', f'"TPL{i}"', 1)
    blocks.append(m)
tmp = outp + '.tpl.kicad_pcb'
open(tmp, 'w').write(txt.rstrip()[:-1] + '\n' + '\n'.join(blocks) + '\n)\n')
b = pcbnew.LoadBoard(tmp)
fps = {f.GetReference(): f for f in b.GetFootprints()}
tpl = {n: fps[f'TPL{i}'] for i, n in enumerate(need)}
netnames = set()
for r in PL:
    for p in fps[r].Pads():
        if p.GetNetname(): netnames.add(p.GetNetname())
dead = []
for t in b.GetTracks():
    x, y = pcbnew.ToMM(t.GetX()), pcbnew.ToMM(t.GetY())
    if t.GetNetname() in netnames and y < 36.2 and 66 < x < 167 and t.GetNetname() not in ('GND', '+12V', '+5V', '+3.3V'):
        dead.append(t)
new = {}
for r, (n, x, y, a) in PL.items():
    f = pcbnew.FOOTPRINT(tpl[n]); f.SetReference(r); f.SetOrientationDegrees(a); f.SetPosition(VECTOR2I(mm(x), mm(y))); new[r] = f
for t in dead: b.Remove(t)
for r in PL: b.Remove(fps[r])
for i in range(len(need)): b.Remove(fps[f'TPL{i}'])
for f in new.values(): b.Add(f)
root = ET.parse(xmlf).getroot()
comps = {c.get('ref'): c for c in root.find('components')}
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
print('replaced', sorted(PL), 'deleted tracks', len(dead))
