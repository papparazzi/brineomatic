"""Rev D 'fewer extended parts' schematic pass: usage edit_swaps2.py <kicad_dir>"""
import sys, glob
from kiutils.schematic import Schematic
kd = sys.argv[1]
V2, V3, V4 = ('Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical', 'Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical', 'Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical')
S = {}
for r in ('D13', 'D21', 'D22', 'D25', 'D28', 'D31', 'D39', 'D46'):
    S[r] = dict(value='RED', lcsc='C2286')                       # KT-0603R, Basic, same 0603 footprint
for r in ('Q1', 'Q2', 'Q4', 'Q5', 'Q6', 'Q7'):
    S[r] = dict(value='AO3400A', lcsc='C20917', desc='30V 5.7A N-channel MOSFET, SOT-23')
S['D18'] = dict(value='1N4148W', lcsc='C81598', desc='75V 0.15A switching diode, SOD-123')
S['C21'] = dict(lcsc='C3342'); S['C23'] = dict(lcsc='C3342')       # RVT1C221M0607, 220uF/16V 6.3x7.7, fee-free
S['C57'] = dict(value='47uF / 50v', lcsc='C3349')                   # RVT1H470M0607, 6.3x7.7, fee-free
for r in ('J3', 'J18'): S[r] = dict(lcsc='C2319', fp=V2)
for r in ('J4', 'J5', 'J11', 'J22', 'J23'): S[r] = dict(lcsc='C2320', fp=V3, value='~')
S['J21'] = dict(lcsc='C2321', fp=V4)
DELETE = {'J24'}                                                    # loose 3.5 mm 3-pin plug of J23
done = set()
for f in glob.glob(kd + '/*.kicad_sch'):
    s = Schematic.from_file(f); ch = False
    keep = []
    for x in s.schematicSymbols:
        pr = {p.key: p for p in x.properties}; r = pr['Reference'].value
        if r in DELETE:
            ch = True; done.add(r); continue
        if r in S:
            c = S[r]; done.add(r); ch = True
            if 'value' in c: pr['Value'].value = c['value']
            if 'lcsc' in c: pr['LCSC'].value = c['lcsc']
            if 'fp' in c: pr['Footprint'].value = c['fp']
            if 'desc' in c and 'Description' in pr: pr['Description'].value = c['desc']
        keep.append(x)
    s.schematicSymbols = keep
    if ch: s.to_file(f)
print('missing', sorted((set(S) | DELETE) - done))
