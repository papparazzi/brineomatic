"""Rev D PCB step 1a (structure; phase 2 = pcb_sync_nets.py): bring kicad_pcb in line with the schematic netlist (no routing).
 - deletes footprints that are no longer in the netlist, adds new ones (stock KiCad libs + local socket footprint)
 - rewrites every pad's net from the schematic XML netlist
 - widens the outline to the west and places the ESP32-S3-DevKitC-1 sockets there
Run with KiCad's bundled python:  pcb_sync.py <in.kicad_pcb> <netlist.xml> <out.kicad_pcb>"""
import sys, os, xml.etree.ElementTree as ET
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm

inp, xmlf, outp = sys.argv[1:4]
b = pcbnew.LoadBoard(inp)
OLD_EDGE = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and max(d.GetStart().x, d.GetEnd().x) < mm(70)]
FPLIB = os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')

# ---------------------------------------------------------------- netlist
root = ET.parse(xmlf).getroot()
comps = {c.get('ref'): c for c in root.find('components')}
pin_net = {}
for n in root.find('nets'):
    name = n.get('name')
    for nd in n:
        if nd.tag == 'node':
            pin_net[(nd.get('ref'), nd.get('pin'))] = name

# ---------------------------------------------------------------- footprints: remove / add
have = {f.GetReference(): f for f in b.GetFootprints()}
orig_refs = set(have)
real = {r for r in comps}
TMPL = {'Package_TO_SOT_SMD:SOT-23': 'Q2', 'Resistor_SMD:R_0603_1608Metric': 'R28',
        'Diode_SMD:D_SOD-123': 'D20', 'Diode_SMD:D_SMA': 'D49'}
tmpl_fp = {k: pcbnew.FOOTPRINT(have[v]) for k, v in TMPL.items()}   # copies taken before anything is removed


for r, f in list(have.items()):
    if r not in real and not r.startswith(('H', 'FID', 'SYM')):
        b.Remove(f)
        del have[r]
removed_fp = sorted(orig_refs - set(have))


_io = pcbnew.PCB_IO_KICAD_SEXPR()


def add(ref, lib, name, x, y, rot=0):
    fp = pcbnew.FOOTPRINT(tmpl_fp[lib + ':' + name])
    fp.SetReference(ref)
    fp.SetPosition(VECTOR2I(mm(x), mm(y)))
    fp.SetOrientationDegrees(rot)
    b.Add(fp)
    have[ref] = fp
    return fp


NEW = {  # ref: (lib, footprint, x, y, rot)
    'Q9': ('Package_TO_SOT_SMD', 'SOT-23', 139.0, 57.0, 0),
    'Q10': ('Package_TO_SOT_SMD', 'SOT-23', 139.0, 64.0, 0),
    'R78': ('Resistor_SMD', 'R_0603_1608Metric', 146.0, 67.0, 90),
    'D56': ('Diode_SMD', 'D_SOD-123', 144.0, 69.5, 0),
    'D57': ('Diode_SMD', 'D_SMA', 40.0, 90.0, 0),
}
for r, (lib, name, x, y, rot) in NEW.items():
    if r not in have:
        add(r, lib, name, x, y, rot)

# ---------------------------------------------------------------- DevKitC socket footprint
J1 = ['2', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '15', '16', '17', '18', '19', '20', '21', '22', '42', '1']
J3 = ['40', '37', '36', '39', '38', '35', '34', '33', '32', '31', '30', '29', '28', '27', '26', '25', '24', '23', '14', '13', '41', '1']
# Espressif v1.1 user guide GPIO per header pin (J1 pin 1..22 / J3 pin 1..22)
G1 = ['3V3', '3V3', 'RST', '4', '5', '6', '7', '15', '16', '17', '18', '8', '3', '46', '9', '10', '11', '12', '13', '14', '5V', 'GND']
G3 = ['GND', '43', '44', '1', '2', '42', '41', '40', '39', '38', '37', '36', '35', '0', '45', '48', '47', '21', '20', '19', 'GND', 'GND']
sch_pin = {}
for nd in [n for net in root.find('nets') for n in net if n.tag == 'node' and n.get('ref') == 'U5']:
    sch_pin[nd.get('pin')] = nd.get('pinfunction')
for pads, gp in ((J1, G1), (J3, G3)):
    for num, g in zip(pads, gp):
        fn = sch_pin.get(num)
        if fn is None:
            continue                       # pin 42 (5V) has no pinfunction in an older xml; checked below
        if g.isdigit():
            assert fn.split('_')[0] in ('IO' + g,) or fn.startswith(('IO' + g + '_', 'TXD0', 'RXD0', 'USB_D')), (num, g, fn)
        elif g == '3V3':
            assert fn.startswith('3V3'), (num, g, fn)
        elif g == 'RST':
            assert fn.startswith('EN'), (num, g, fn)
        elif g == 'GND':
            assert fn.startswith('GND'), (num, g, fn)
tx = {'43': 'TXD0', '44': 'RXD0', '19': 'USB_D-', '20': 'USB_D+'}
for pads, gp in ((J1, G1), (J3, G3)):
    for num, g in zip(pads, gp):
        if g in tx:
            assert sch_pin[num].startswith(tx[g]), (num, g, sch_pin[num])

X0, Y0 = 38.0, 33.7            # J1 pin-1 centre; J3 column is 22.86 mm to the right
if 'U5' in have:
    b.Remove(have['U5'])
fp = pcbnew.FOOTPRINT(b)
fp.SetReference('U5'); fp.SetValue('ESP32-S3-DevKitC-1')
fp.SetFPID(pcbnew.LIB_ID('brineomatic_local', 'ESP32-S3-DevKitC-1_Sockets'))
for col, pads in ((0, J1), (1, J3)):
    for i, num in enumerate(pads):
        p = pcbnew.PAD(fp)
        p.SetNumber(num); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE if not (i == 0) else pcbnew.PAD_SHAPE_RECT)
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p.SetSize(VECTOR2I(mm(1.7), mm(1.7))); p.SetDrillSize(VECTOR2I(mm(1.0), mm(1.0)))
        p.SetLayerSet(p.PTHMask())
        p.SetPosition(VECTOR2I(mm(col * 22.86), mm(i * 2.54)))
        fp.Add(p)
# silkscreen: board outline of the dev board (25.4 x 62.9), USB at the bottom (pin 22 end)
def silk(x1, y1, x2, y2, layer=pcbnew.F_SilkS):
    s = pcbnew.PCB_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer)
    s.SetStart(VECTOR2I(mm(x1), mm(y1))); s.SetEnd(VECTOR2I(mm(x2), mm(y2))); s.SetWidth(mm(0.15)); fp.Add(s)
bx0, bx1, by0, by1 = -1.27, 24.13, -4.78, 58.12
for a in ((bx0, by0, bx1, by0), (bx1, by0, bx1, by1), (bx1, by1, bx0, by1), (bx0, by1, bx0, by0)):
    silk(*a)
t = pcbnew.PCB_TEXT(fp); t.SetText('ESP32-S3-DevKitC-1  USB end'); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(VECTOR2I(mm(11.43), mm(55.5)))
t.SetTextSize(VECTOR2I(mm(1.0), mm(1.0))); fp.Add(t)
fp.SetPosition(VECTOR2I(mm(X0), mm(Y0)))
b.Add(fp); have['U5'] = fp

# ---------------------------------------------------------------- outline: extend west to x=34
XL = 34.0
for d in OLD_EDGE:
    b.Remove(d)
def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(VECTOR2I(mm(x1), mm(y1))); s.SetEnd(VECTOR2I(mm(x2), mm(y2))); s.SetWidth(mm(0.1)); b.Add(s)
def arc(cx, cy, sx, sy, ex, ey):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetCenter(VECTOR2I(mm(cx), mm(cy))); s.SetStart(VECTOR2I(mm(sx), mm(sy))); s.SetEnd(VECTOR2I(mm(ex), mm(ey))); s.SetWidth(mm(0.1)); b.Add(s)
R = 3.0
seg(XL + R, 29.0, 66.0, 29.0)
seg(XL + R, 92.5, 66.0, 92.5)
seg(XL, 29.0 + R, XL, 92.5 - R)
arc(XL + R, 29.0 + R, XL, 29.0 + R, XL + R, 29.0)
arc(XL + R, 92.5 - R, XL + R, 92.5, XL, 92.5 - R)

b.Save(outp)
print('phase1 removed', removed_fp)
