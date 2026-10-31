"""Rev D PCB step 1b: assign every pad's net from the schematic netlist.  pcb_sync_nets.py <in> <netlist.xml> <out>"""
import sys, xml.etree.ElementTree as ET
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
have = {f.GetReference(): f for f in b.GetFootprints()}

def get_net(name):
    ni = b.FindNet(name)
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni)
    return ni
unmatched = []
for ref, f in have.items():
    if ref not in comps:
        continue
    for pad in f.Pads():
        net = pin_net.get((ref, pad.GetNumber()))
        if net:
            pad.SetNet(get_net(net))
        else:
            pad.SetNetCode(0)
        if net is None and pad.GetNumber():
            unmatched.append((ref, pad.GetNumber()))
# +24V -> +12V rename on the board so zones/tracks follow
old = b.FindNet('+24V')
if old is not None:
    old.SetNetname('+12V')
# value updates
for ref, c in comps.items():
    if ref in have:
        v = c.findtext('value')
        if v and have[ref].GetValue() != v:
            have[ref].SetValue(v)
b.BuildConnectivity()
b.Save(outp)
print('nets done')
print('pads without net (non-NC):', unmatched[:20], len(unmatched))

# copied footprints share KIIDs (and pad/graphic KIIDs) with their templates: regenerate duplicates
import re, uuid
txt = open(outp).read()
seen = set()
def fix(m):
    u = m.group(2)
    if u in seen:
        u = str(uuid.uuid4())
    seen.add(u)
    return m.group(1) + u + m.group(3)
txt = re.sub(r'(\(uuid ")([0-9a-f-]{36})(")', fix, txt)
open(outp, 'w').write(txt)
print('uuids made unique:', len(seen))
