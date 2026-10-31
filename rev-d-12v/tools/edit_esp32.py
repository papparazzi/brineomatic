"""Rev D ESP32 sheet edit: replace the soldered ESP32-S3-WROOM module + USB/boot/LED/LDO support with
sockets for an ESP32-S3-DevKitC-1 (v1.1).  Run once, after edit_power.py, on the project kicad dir.
usage: edit_esp32.py <kicad_dir>"""
import sys, copy, uuid
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from kiutils.schematic import Schematic
from kiutils.items.common import Position
from kiutils.items.schitems import LocalLabel
from kiutils.symbol import SymbolPin
from schlib import ref, pin_positions, prune, R2

kd = sys.argv[1]
f = kd + '/esp32-s3.kicad_sch'
s = Schematic.from_file(f)
T = {ref(x): x for x in s.schematicSymbols}
REMOVE = set('''J19 SW1 SW2 U6 D37 D38 C38 C39 R43 R44 R45 R46 R47 R48 R49 R50 R52 R53 D40 U8 FB1 D36
TP27 TP28 TP29 J20 U7 C37 C40 C42 C43'''.split())
s.schematicSymbols = [x for x in s.schematicSymbols if ref(x) not in REMOVE]
s.noConnects = [n for n in s.noConnects if not (R2(n.position.X) == 66.04)]

# --- U5: module -> DevKitC-1 socket symbol (same pin numbers, so every existing label/wire stays)
LIB = 'brineomatic_local:ESP32-S3-DevKitC-1'
src = [l for l in s.libSymbols if l.libId == 'RF_Module:ESP32-S3-WROOM-1'][0]
new = copy.deepcopy(src); new.libId = LIB; new.entryName = 'ESP32-S3-DevKitC-1'
for u in new.units:
    u.entryName = 'ESP32-S3-DevKitC-1'
    for p in u.pins:
        if p.number == '2':
            p.electricalType = 'power_out'      # dev-board LDO output drives +3.3V
        if p.number in ('1', '40', '41'):
            p.electricalType = 'passive'
pin5v = SymbolPin(electricalType='power_in', graphicalStyle='line', position=Position(X=-5.08, Y=-27.94, angle=90),
                  length=2.54, name='5V', number='42')
pin5v.nameEffects = copy.deepcopy(new.units[2].pins[0].nameEffects); pin5v.numberEffects = copy.deepcopy(new.units[2].pins[0].numberEffects)
new.units[2].pins.append(pin5v)
for p in new.properties:
    if p.key == 'Value': p.value = 'ESP32-S3-DevKitC-1'
    if p.key == 'Footprint': p.value = 'brineomatic_local:ESP32-S3-DevKitC-1_Sockets'
    if p.key == 'Description': p.value = 'ESP32-S3-DevKitC-1 v1.1 plugged into 2x 1x22 2.54mm sockets (pad numbers = WROOM-1 module pin numbers)'
    if p.key == 'ki_fp_filters': p.value = 'ESP32?S3?DevKitC*'
s.libSymbols.append(new)
u5 = T['U5']; u5.libId = LIB
for p in u5.properties:
    if p.key == 'Value': p.value = 'ESP32-S3-DevKitC-1'
    if p.key == 'Footprint': p.value = 'brineomatic_local:ESP32-S3-DevKitC-1_Sockets'
    if p.key == 'Description': p.value = 'ESP32-S3-DevKitC-1 v1.1 dev board on 2x 1x22 sockets; supplied by user, not assembled'
    if p.key == 'LCSC': p.value = ''
u5.properties = [p for p in u5.properties if p.key != 'Position Offset']
u5.pins['42'] = str(uuid.uuid4())
if not any(l.libId == 'RF_Module:ESP32-S3-WROOM-1' for l in [x for x in s.schematicSymbols]):
    s.libSymbols = [l for l in s.libSymbols if l.libId != 'RF_Module:ESP32-S3-WROOM-1']

# --- series diode so the dev-board 5V pin is never back-fed by the USB port (Espressif: USB and 5V pin not together)
d = copy.deepcopy(T['D36']); d.uuid = str(uuid.uuid4())
for p in d.properties:
    if p.key == 'Reference': p.value = 'D57'
for i in d.instances:
    for q in i.paths: q.reference = 'D57'
d.pins = {k: str(uuid.uuid4()) for k in d.pins}
d.position = Position(X=60.96, Y=167.64, angle=0); d.mirror = None
s.schematicSymbols.append(d)
pins = dict(pin_positions(s, d))
print('D57 pins', pins)
k_pt = pins['1']; a_pt = pins['2']          # Diode:SS36 -> pin1 = K, pin2 = A


def label(text, pt, ang):
    l = LocalLabel(text=text, position=Position(X=pt[0], Y=pt[1], angle=ang)); l.uuid = str(uuid.uuid4()); s.labels.append(l)


label('ESP_5V', k_pt, 0)
label('ESP_5V', (83.82, 154.94), 270)                # U5 pin 42
pw = copy.deepcopy(T['#PWR053']); pw.uuid = str(uuid.uuid4()); pw.mirror = None
pw.position = Position(X=a_pt[0], Y=a_pt[1], angle=0)
for p in pw.properties:
    if p.key == 'Reference': p.value = '#PWR090'
for i in pw.instances:
    for q in i.paths: q.reference = '#PWR090'
pw.pins = {k: str(uuid.uuid4()) for k in pw.pins}
s.schematicSymbols.append(pw)
fl = copy.deepcopy(T['#FLG08']); fl.uuid = str(uuid.uuid4()); fl.mirror = None
fl.position = Position(X=83.82, Y=154.94, angle=0)
for p in fl.properties:
    if p.key == 'Reference': p.value = '#FLG09'
for i in fl.instances:
    for q in i.paths: q.reference = '#FLG09'
fl.pins = {k: str(uuid.uuid4()) for k in fl.pins}
s.schematicSymbols.append(fl)

log = prune(s)
print('pruned', len(log), log[:60])
# drop labels that no longer touch any wire end / pin (they belonged to removed parts)
def touched(pt):
    for x in s.schematicSymbols:
        if any(q == pt for _, q in pin_positions(s, x)): return True
    for w in s.graphicalItems:
        if w.type != 'wire': continue
        a, b = w.points
        if pt in ((R2(a.X), R2(a.Y)), (R2(b.X), R2(b.Y))): return True
        if a.X == b.X == pt[0] and min(a.Y, b.Y) < pt[1] < max(a.Y, b.Y): return True
        if a.Y == b.Y == pt[1] and min(a.X, b.X) < pt[0] < max(a.X, b.X): return True
    return False
for coll in (s.labels, s.hierarchicalLabels):
    for l in list(coll):
        if not touched((R2(l.position.X), R2(l.position.Y))):
            print('drop label', l.text, l.position.X, l.position.Y)
            coll.remove(l)
names = {}
for h in s.hierarchicalLabels:
    names.setdefault(h.text, []).append((h.position.X, h.position.Y))
print('hier labels', {k: v for k, v in names.items() if len(v) > 1 or k in ('LED_OUT',)})
s.to_file(f)
