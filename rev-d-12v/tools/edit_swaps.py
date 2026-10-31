"""Rev D schematic part swaps (fee-free parts, 12 V re-rating, connector standardisation).
usage: edit_swaps.py <kicad_dir> <symbols_dir>
Every row of SWAPS is documented with its vetting in docs/CHANGE_REGISTER.md."""
import sys, copy, glob
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib

kd, symd = sys.argv[1], sys.argv[2]
FP = {'C1206': 'Capacitor_SMD:C_1206_3216Metric', 'SMA': 'Diode_SMD:D_SMA'}
# ref -> dict(value=, lcsc=, footprint=, flip=True)
S = {}
for r in ('C3', 'C24', 'C18'):
    S[r] = dict(value='2.2nF', lcsc='C1604')
for r in ('C52', 'C53', 'C55', 'C56'):
    S[r] = dict(value='470pF / 50V', lcsc='C1620')
for r in ('C11', 'C12', 'C13', 'C14', 'C22', 'C46', 'C49'):
    S[r] = dict(value='10uF', lcsc='C13585', footprint=FP['C1206'])
for r in ('D1', 'D2', 'D10'):
    S[r] = dict(lcsc='C2925443')
for r in ('D15', 'D27', 'D30', 'D33', 'D48'):
    S[r] = dict(value='SMBJ16CA', lcsc='C19077572')
for r in ('D50', 'D51', 'D52', 'D53', 'D54', 'D55'):
    S[r] = dict(lcsc='C2990493')
for r in ('D14', 'D26', 'D29', 'D32', 'D47', 'D49'):   # flyback / rail clamp: 3 A load limit -> SS34 (3 A, 40 V) instead of SS54
    S[r] = dict(value='SS34', lcsc='C8678')
S['D44'] = dict(lcsc='C32677')
for r in ('D6', 'D24'):
    S[r] = dict(lcsc='C7420333')
for r in ('D4', 'D9', 'D35', 'D42'):
    S[r] = dict(value='BAV99', lcsc='C2500')
# D18 (B5819W buzzer flyback) stays: an SMA SS34 collides with the buzzer courtyard
S['R23'] = dict(lcsc='C23254')
S['R26'] = dict(value='12k', lcsc='C22790')
S['R27'] = dict(value='47k', lcsc='C25819')
S['U10'] = dict(value='SP3485EN', lcsc='C8963')
# connectors: J10 (5.08 mm power in) -> the 3.5 mm 2-pin used for the outputs; its loose plug J9 likewise
S['J10'] = dict(value='3.5MM', lcsc='C5188295', footprint='PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal', copy_from='J7')
S['J9'] = dict(value='3.5MM', lcsc='C5188249')
# J2 (JST-SH I2C header) stays: a PH-4 footprint does not fit among the sensor inputs

lib_dev = {x.entryName: x for x in SymbolLib.from_file(symd + '/Device.kicad_sym').symbols}
lib_con = {x.entryName: x for x in SymbolLib.from_file(symd + '/Connector_Generic.kicad_sym').symbols}
done = set()
sheets = {f: Schematic.from_file(f) for f in glob.glob(kd + '/*.kicad_sch')}
def ref(x): return [p.value for p in x.properties if p.key == 'Reference'][0]
src = {}
for sch in sheets.values():
    for x in sch.schematicSymbols:
        src[ref(x)] = (sch, x)
for f, sch in sheets.items():
    for x in sch.schematicSymbols:
        r = ref(x)
        if r not in S:
            continue
        c = S[r]; done.add(r)
        props = {p.key: p for p in x.properties}
        if 'value' in c: props['Value'].value = c['value']
        if 'lcsc' in c: props['LCSC'].value = c['lcsc']
        if 'copy_from' in c:
            props['Footprint'].value = [p.value for p in src[c['copy_from']][1].properties if p.key == 'Footprint'][0]
        elif 'footprint' in c:
            props['Footprint'].value = c['footprint']
        if c.get('unidir'):
            if 'Device:D_Zener' not in {l.libId for l in sch.libSymbols}:
                z = copy.deepcopy(lib_dev['D_Zener']); z.libId = 'Device:D_Zener'; sch.libSymbols.append(z)
            x.libId = 'Device:D_Zener'
            x.position.angle = ((x.position.angle or 0) + 180) % 360     # K (pin 1) must face the drain, A to GND
            props['Description'].value = '16V unidirectional TVS, SMB'
        if c.get('lib'):
            x.libId = c['lib']
            if c['lib'] not in {l.libId for l in sch.libSymbols}:
                z = copy.deepcopy(lib_con['Conn_01x04']); z.libId = c['lib']; sch.libSymbols.append(z)
            x.pins = {k: v for k, v in x.pins.items() if k != 'MP'}
print('not found:', sorted(set(S) - done))
for f, sch in sheets.items():
    sch.to_file(f)
