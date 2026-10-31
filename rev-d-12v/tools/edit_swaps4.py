"""Rev D: split the 2x03 servo/TDS pin headers J1, J6 into two 3-pin 3.5 mm screw terminals each.
J1 -> J1 (pins 1,3,5 of the old header) + J28 (pins 2,4,6); J6 -> J6 + J29.  Pin ends keep their old coordinates, so wires/labels stay attached.
usage: edit_swaps4.py <kicad_dir> <symbols_dir>"""
import sys, copy, glob, uuid
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib
kd, symd = sys.argv[1], sys.argv[2]
FP = 'Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal'
lib = {x.entryName: x for x in SymbolLib.from_file(symd + '/Connector_Generic.kicad_sym').symbols}
SPLIT = {'J1': 'J28', 'J6': 'J29'}
done = set()
for f in glob.glob(kd + '/*.kicad_sch'):
    s = Schematic.from_file(f); ch = False
    for x in list(s.schematicSymbols):
        pr = {p.key: p for p in x.properties}
        r = pr['Reference'].value
        if r not in SPLIT: continue
        assert x.libId == 'Connector_Generic:Conn_02x03_Odd_Even' and not x.mirror and (x.position.angle or 0) == 0
        if 'Connector_Generic:Conn_01x03' not in {l.libId for l in s.libSymbols}:
            z = copy.deepcopy(lib['Conn_01x03']); z.libId = 'Connector_Generic:Conn_01x03'; s.libSymbols.append(z)
        b = copy.deepcopy(x)                                   # terminal B (old pins 2,4,6, right-hand column)
        for sym, ref in ((x, r), (b, SPLIT[r])):
            sym.libId = 'Connector_Generic:Conn_01x03'
            sym.pins = {'1': str(uuid.uuid4()), '2': str(uuid.uuid4()), '3': str(uuid.uuid4())}
            for p in sym.properties:
                if p.key == 'Reference': p.value = ref
                if p.key == 'Value': p.value = '3.5MM'
                if p.key == 'Footprint': p.value = FP
                if p.key == 'LCSC': p.value = 'C5188296'
                if p.key == 'Description': p.value = '3-pin 3.5 mm pluggable screw terminal (S, +, -)'
            if not any(p.key == 'LCSC' for p in sym.properties):
                from kiutils.items.common import Property, Position, Effects
                np_ = copy.deepcopy([p for p in sym.properties if p.key == 'Footprint'][0]); np_.key = 'LCSC'; np_.value = 'C5188296'
                np_.id = max(p.id for p in sym.properties if p.id is not None) + 1; sym.properties.append(np_)
            for i in sym.instances:
                for pth in i.paths: pth.reference = ref
        b.uuid = str(uuid.uuid4())
        b.mirror = 'y'
        b.position.X = x.position.X + 2.54                    # pin ends land on the old right-hand column (x+7.62)
        for p in b.properties:
            if p.key in ('Reference', 'Value'): p.position.X += 10; p.position.Y += (4 if p.key == 'Reference' else 6.5)
        s.schematicSymbols.append(b)
        done.add(r); ch = True
    if ch: s.to_file(f)
print('split:', sorted(done))
