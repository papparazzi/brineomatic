"""Swap footprints for the Rev D 'fewer extended parts' pass using KiCad library footprints (inserted into a temp copy of the
board so pcbnew can copy them).  Then re-sync pad nets from the netlist.
usage: pcb_swap2.py <in.kicad_pcb> <netlist.xml> <out.kicad_pcb>"""
import sys, re, os, uuid, xml.etree.ElementTree as ET
import pcbnew
inp, xmlf, outp = sys.argv[1:4]
FPD = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
SWAP = {  # ref -> (lib, footprint)
    'J3': ('Connector_JST', 'JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical'), 'J18': ('Connector_JST', 'JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical'),
    'J4': ('Connector_JST', 'JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical'), 'J5': ('Connector_JST', 'JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical'),
    'J11': ('Connector_JST', 'JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical'), 'J22': ('Connector_JST', 'JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical'),
    'J23': ('Connector_JST', 'JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical'),
    'J21': ('Connector_JST', 'JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical'),
}
if len(sys.argv) > 4:
    exec(open(sys.argv[4]).read())      # optional override of SWAP
txt = open(inp).read()
need = sorted(set(SWAP.values()))
blocks = []
for i, (lib, name) in enumerate(need):
    m = open(f'{FPD}/{lib}.pretty/{name}.kicad_mod').read()
    m = m.replace(f'(footprint "{name}"', f'(footprint "{lib}:{name}"', 1)
    m = re.sub(r'(\(layer "F\.Cu"\))', r'\1\n\t(at 0 0)', m, 1)
    m = m.replace('"REF**"', f'"TPL{i}"', 1)
    blocks.append(m)
tmp = outp + '.tpl.kicad_pcb'
open(tmp, 'w').write(txt.rstrip()[:-1] + '\n' + '\n'.join(blocks) + '\n)\n')
b = pcbnew.LoadBoard(tmp)
fps = {f.GetReference(): f for f in b.GetFootprints()}
tpl = {need[i]: fps[f'TPL{i}'] for i in range(len(need))}
new = {}
for r, key in SWAP.items():
    old = fps[r]
    n = pcbnew.FOOTPRINT(tpl[key]); n.SetReference(r)
    n.SetOrientationDegrees(old.GetOrientationDegrees()); n.SetPosition(old.GetPosition())
    new[r] = n
for r in SWAP: b.Remove(fps[r])
for i in range(len(need)): b.Remove(fps[f'TPL{i}'])
for n in new.values(): b.Add(n)
root = ET.parse(xmlf).getroot()
comps = {c.get('ref'): c for c in root.find('components')}
pin_net = {}
for n in root.find('nets'):
    for nd in n:
        if nd.tag == 'node': pin_net[(nd.get('ref'), nd.get('pin'))] = n.get('name')
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
b.Save(outp)
os.remove(tmp)
t = open(outp).read(); seen = set()
def fix(m):
    u = m.group(2)
    if u in seen: u = str(uuid.uuid4())
    seen.add(u); return m.group(1) + u + m.group(3)
open(outp, 'w').write(re.sub(r'(\(uuid ")([0-9a-f-]{36})(")', fix, t))
print('swapped', sorted(SWAP))
