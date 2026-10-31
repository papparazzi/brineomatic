"""Rev D power-sheet edit (idempotence: run once on a pristine Rev-C1 copy).
 - removes eFuse stage (U3,Q3,Q8,R72-77,R21,C15,TP50-52,#PWR074) + its wires
 - adds 2x AO3401A reverse-polarity P-FETs (parallel), 10k gate pulldown, BZT52C10 gate clamp
 - D19 -> unidirectional SMBJ16A (K on PRE_24)
 - renames +24V power symbols to +12V
usage: edit_power.py <kicad_dir> <symbols_dir>"""
import sys, copy, uuid
from kiutils.schematic import Schematic
from kiutils.items.common import Position, Property
from kiutils.items.schitems import Connection, Junction, LocalLabel
from kiutils.symbol import SymbolLib
kd, symd = sys.argv[1], sys.argv[2]
f = kd + '/power_supply.kicad_sch'
s = Schematic.from_file(f)
R = lambda v: round(v, 2)
REMOVE = set('U3 Q3 Q8 R72 R73 R74 R75 R76 R77 R21 C15 TP50 TP51 TP52 #PWR074'.split())
def ref(sym): return [p.value for p in sym.properties if p.key == 'Reference'][0]
tmpl = {ref(x): x for x in s.schematicSymbols}
s.schematicSymbols = [x for x in s.schematicSymbols if ref(x) not in REMOVE]
KEEP_W = {(210.82,38.1,210.82,44.45),(210.82,49.53,210.82,54.61),(213.36,54.61,210.82,54.61),(195.58,36.83,195.58,38.1)}
def keepw(w):
    a, b = w.points
    t = (a.X,a.Y,b.X,b.Y); t2 = (b.X,b.Y,a.X,a.Y)
    if t in KEEP_W or t2 in KEEP_W: return True
    if not (125.7 <= min(a.X,b.X) and max(a.X,b.X) <= 210.9): return True
    if a.Y == b.Y == 76.2: return True
    if a.Y == b.Y == 38.1 and ((a.X,b.X)==(125.73,133.35) or (a.X,b.X)==(133.35,125.73) or min(a.X,b.X)>=176.5 or max(a.X,b.X)<=125.73): return True
    if max(a.Y,b.Y) > 77: return True
    if (a.X,a.Y,b.X,b.Y) in {(163.83,76.2,163.83,77.47)}: return True
    return False
n0 = sum(1 for g in s.graphicalItems if g.type == 'wire')
s.graphicalItems = [g for g in s.graphicalItems if g.type != 'wire' or keepw(g)]
print('wires removed', n0 - sum(1 for g in s.graphicalItems if g.type == 'wire'))
s.junctions = [j for j in s.junctions if not (125.7 <= j.position.X <= 207.1 and j.position.Y < 76 and (j.position.X, j.position.Y) != (195.58, 38.1))]
# library symbols
lib_fet = SymbolLib.from_file(symd + '/Transistor_FET.kicad_sym'); d = {x.entryName: x for x in lib_fet.symbols}
par = d['TP0610T']; ao = copy.deepcopy(par); ao.entryName = 'AO3401A'; ao.libId = 'Transistor_FET:AO3401A'
for u in ao.units: u.entryName = u.entryName.replace('TP0610T', 'AO3401A')
for p in ao.properties:
    src = {x.key: x.value for x in d['AO3401A'].properties}
    if p.key in src: p.value = src[p.key]
lib_dev = SymbolLib.from_file(symd + '/Device.kicad_sym'); dd = {x.entryName: x for x in lib_dev.symbols}
zen = copy.deepcopy(dd['D_Zener']); zen.libId = 'Device:D_Zener'
have = {x.libId for x in s.libSymbols}
for L in (ao, zen):
    if L.libId not in have: s.libSymbols.append(L)
def clone(t, newref, lib, x, y, ang, val, lcsc, fp=None):
    c = copy.deepcopy(t)
    c.libId = lib; c.position = Position(X=R(x), Y=R(y), angle=ang); c.uuid = str(uuid.uuid4())
    for p in c.properties:
        if p.key == 'Reference': p.value = newref
        elif p.key == 'Value': p.value = val
        elif p.key == 'LCSC': p.value = lcsc
        elif p.key == 'Footprint' and fp: p.value = fp
        p.position = Position(X=R(x + 2.54), Y=R(y), angle=0) if p.key in ('Reference',) else Position(X=R(x + 2.54), Y=R(y + 2.54), angle=0)
        if p.key not in ('Reference','Value'): p.effects.hide = True
    c.mirror = None
    for i in c.instances:
        for q in i.paths: q.reference = newref
    c.pins = {k: str(uuid.uuid4()) for k in c.pins}
    return c
py = 43.18
fets = []
for r, px in (('Q9', 144.78), ('Q10', 160.02)):
    q = clone(tmpl['Q8'], r, 'Transistor_FET:AO3401A', px, py, 0, 'AO3401A', 'C15127')
    q.properties = [p for p in q.properties]
    for p in q.properties:
        if p.key == 'Datasheet': p.value = 'http://www.aosmd.com/pdfs/datasheet/AO3401A.pdf'
        if p.key == 'Description': p.value = '-4.0A Id, -30V Vds, P-Channel MOSFET, SOT-23'
    s.schematicSymbols.append(q)
s.schematicSymbols.append(clone(tmpl['R28'], 'R78', 'Device:R_Small_US', 170.18, 60.96, 0, '10k', 'C25804'))
dz = clone(tmpl['D20'], 'D56', 'Device:D_Zener', 165.1, 55.88, 270, 'BZT52C10', 'C19077408', 'Diode_SMD:D_SOD-123')
for p in dz.properties:
    if p.key == 'Description': p.value = '10V 350mW Zener, SOD-123'
    if p.key == 'Datasheet': p.value = '~'
dz.properties = [p for p in dz.properties if not p.key.startswith('Sim.')]
s.schematicSymbols.append(dz)
# D19 -> unidirectional SMBJ16A, K (pin1) toward PRE_24
d19 = tmpl['D19']; d19.libId = 'Device:D_Zener'; d19.position.angle = 270
for p in d19.properties:
    if p.key == 'Value': p.value = 'SMBJ16A'
    if p.key == 'LCSC': p.value = 'C19077571'
    if p.key == 'Description': p.value = '16V unidirectional TVS, SMB'
def W(x1, y1, x2, y2):
    c = Connection(type='wire', points=[Position(X=R(x1), Y=R(y1)), Position(X=R(x2), Y=R(y2))]); c.uuid = str(uuid.uuid4()); s.graphicalItems.append(c)
def J(x, y):
    j = Junction(position=Position(X=R(x), Y=R(y))); j.uuid = str(uuid.uuid4()); s.junctions.append(j)
def LBL(t, x, y, ang=0):
    l = LocalLabel(text=t, position=Position(X=R(x), Y=R(y), angle=ang)); l.uuid = str(uuid.uuid4()); s.labels.append(l)
W(147.32, 38.1, 176.53, 38.1); J(147.32, 38.1); J(162.56, 38.1)
W(133.35, 38.1, 133.35, 48.26); W(133.35, 48.26, 165.1, 48.26); J(147.32, 48.26); J(162.56, 48.26); J(133.35, 38.1)
W(165.1, 48.26, 165.1, 52.07)
LBL('PFET_G', 139.7, 43.18, 180); LBL('PFET_G', 154.94, 43.18, 180)
LBL('PFET_G', 165.1, 59.69, 270); LBL('PFET_G', 170.18, 58.42, 90)
W(170.18, 63.5, 170.18, 76.2); J(170.18, 76.2)
# +24V -> +12V power symbols
lib_pwr = SymbolLib.from_file(symd + '/power.kicad_sym'); pp = {x.entryName: x for x in lib_pwr.symbols}
p12 = copy.deepcopy(pp['+12V']); p12.libId = 'power:+12V'
if 'power:+12V' not in {x.libId for x in s.libSymbols}: s.libSymbols.append(p12)
for x in s.schematicSymbols:
    if x.libId == 'power:+24V':
        x.libId = 'power:+12V'
        for p in x.properties:
            if p.key == 'Value': p.value = '+12V'
            if p.key == 'Description': p.value = 'Power symbol creates a global label with name "+12V"'
s.libSymbols = [x for x in s.libSymbols if not (x.libId == 'power:+24V' and not any(y.libId == 'power:+24V' for y in s.schematicSymbols))]
s.to_file(f)
for fn in ('solenoid_driver', 'pressure_sensor', 'tmc2209'):
    g = kd + f'/{fn}.kicad_sch'; t = Schematic.from_file(g)
    for x in t.schematicSymbols:
        if x.libId == 'power:+24V':
            x.libId = 'power:+12V'
            for p in x.properties:
                if p.key == 'Value': p.value = '+12V'
                if p.key == 'Description': p.value = 'Power symbol creates a global label with name "+12V"'
    if 'power:+12V' not in {x.libId for x in t.libSymbols}: t.libSymbols.append(copy.deepcopy(p12))
    t.libSymbols = [x for x in t.libSymbols if not (x.libId == 'power:+24V' and not any(y.libId == 'power:+24V' for y in t.schematicSymbols))]
    t.to_file(g)
print('done')
