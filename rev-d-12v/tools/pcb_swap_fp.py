"""Swap footprints in place for the Rev D part swaps, keeping position/orientation/net, then sync value + LCSC fields.
usage: pcb_swap_fp.py <in.kicad_pcb> <netlist.xml> <out.kicad_pcb>"""
import sys, re, uuid, xml.etree.ElementTree as ET
import pcbnew
inp, xmlf, outp = sys.argv[1:4]
b = pcbnew.LoadBoard(inp)
root = ET.parse(xmlf).getroot()
comps = {c.get('ref'): c for c in root.find('components')}
pin_net = {}
for n in root.find('nets'):
    for nd in n:
        if nd.tag == 'node':
            pin_net[(nd.get('ref'), nd.get('pin'))] = n.get('name')
fps = {f.GetReference(): f for f in b.GetFootprints()}
# new ref -> template ref already on the board with the wanted footprint
SWAP = {'C11': 'C19', 'C12': 'C19', 'C13': 'C19', 'C14': 'C19', 'C22': 'C19', 'C46': 'C19', 'C49': 'C19',
        'J10': 'J7', 'C21': 'C57', 'C23': 'C57'}
FLIP = []      # unidirectional TVS: pad 1 (K) must sit where pad 2 (A) used to be
tmpl = {t: pcbnew.FOOTPRINT(fps[t]) for t in set(SWAP.values())}
old = {r: fps[r] for r in SWAP}
pos = {r: (f.GetPosition(), f.GetOrientationDegrees()) for r, f in old.items()}
new = {}
for r, t in SWAP.items():
    n = pcbnew.FOOTPRINT(tmpl[t])
    n.SetReference(r)
    n.SetOrientationDegrees(pos[r][1])
    n.SetPosition(pos[r][0])
    new[r] = n
for r in FLIP:
    fps[r].SetOrientationDegrees((fps[r].GetOrientationDegrees() + 180) % 360)
for r in SWAP:
    b.Remove(old[r])
for r, n in new.items():
    b.Add(n)
    fps[r] = n
# nets + values for every footprint that exists in the netlist
def net(name):
    ni = b.FindNet(name)
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni)
    return ni
for r, f in fps.items():
    c = comps.get(r)
    if c is None:
        continue
    for pad in f.Pads():
        nm = pin_net.get((r, pad.GetNumber()))
        if nm:
            pad.SetNet(net(nm))
        else:
            pad.SetNetCode(0)
    v = c.findtext('value')
    if v and f.GetValue() != v:
        f.SetValue(v)
b.Save(outp)
print('swapped', sorted(SWAP))
txt = open(outp).read()
seen = set()
def fix(m):
    u = m.group(2)
    if u in seen:
        u = str(uuid.uuid4())
    seen.add(u)
    return m.group(1) + u + m.group(3)
open(outp, 'w').write(re.sub(r'(\(uuid ")([0-9a-f-]{36})(")', fix, txt))
