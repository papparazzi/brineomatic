"""Generate JLCPCB BOM + CPL for Rev D from the schematic netlist and the PCB.  usage: make_jlc.py <netlist.xml> <pcb> <outdir>"""
import sys, csv, subprocess, collections, re, xml.etree.ElementTree as ET, os
xmlf, pcb, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
root = ET.parse(xmlf).getroot()
SKIP = ('TP', 'H', 'FID', 'SYM', 'U5')
groups = collections.defaultdict(list)
placed = set(); loose = []
fpn = {c.get('ref'): (c.findtext('footprint') or '') for c in root.find('components')}
for c in root.find('components'):
    r = c.get('ref')
    props = {p.get('name'): p.get('value') for p in c.iter('property')}
    fields = {f.get('name'): (f.text or '').strip() for f in c.iter('field')}
    fp = (c.findtext('footprint') or '').split(':')[-1]
    lc = fields.get('LCSC', '')
    if r.startswith(SKIP) or r.startswith('#') or 'dnp' in props or 'exclude_from_board' in props:
        continue
    if not fp:
        loose.append((r, c.findtext('value'), lc)); continue
    if not lc:
        print('NO LCSC', r, c.findtext('value')); continue
    short = fp.split('_')[0] if fp.startswith(('C_', 'R_', 'L_', 'LED_')) else fp
    groups[(lc, fp)].append(r)
    placed.add(r)
# one BOM line per LCSC (JLCPCB leaves duplicate-LCSC lines unselected): merge footprints for the same part code
bylc = collections.defaultdict(lambda: [[], set(), ''])
vals = {c.get('ref'): c.findtext('value') for c in root.find('components')}
for (lc, fp), refs in groups.items():
    bylc[lc][0] += refs; bylc[lc][1].add(fp)
rows = []
for lc, (refs, fps, _) in sorted(bylc.items(), key=lambda t: t[0]):
    refs = sorted(refs, key=lambda s: (s.rstrip('0123456789'), int(''.join(ch for ch in s if ch.isdigit()) or 0)))
    rows.append([vals[refs[0]], ', '.join(refs), sorted(fps)[0], lc])
    if len(fps) > 1: print('MULTI FOOTPRINT', lc, fps)
rows.append(['Female header 1x22 2.54mm 8.5mm', 'U5A, U5B', 'PinSocket_1x22_P2.54mm_Vertical', 'C41376161'])   # sockets for the ESP32-S3-DevKitC-1 (dev board itself is NOT assembled)
with open(out + '/BOM-rev_d.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #']); w.writerows(rows)
subprocess.run([os.path.expanduser('~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'), 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'front', '-o', out + '/_pos.csv', pcb], capture_output=True)
n = 0
with open(out + '/_pos.csv') as f, open(out + '/CPL-rev_d.csv', 'w', newline='') as g:
    w = csv.writer(g); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in csv.DictReader(f):
        if r['Ref'] in placed:
            x = float(r['PosX'])
            m = re.search(r'_(\d)-G-3\.5', fpn.get(r['Ref'], ''))
            if m:   # 3.5 mm terminals: KiCad origin is pin 1, JLCPCB wants the centre of the pin row
                x += (-1 if float(r['Rot']) == 180 else 1) * (int(m.group(1)) - 1) * 1.75
            w.writerow([r['Ref'], '%.4fmm' % x, r['PosY'] + 'mm', 'Top', r['Rot']]); n += 1
os.remove(out + '/_pos.csv')
with open(out + '/CPL-rev_d.csv', 'a', newline='') as g:
    w = csv.writer(g)
    w.writerow(['U5A', '38.000000mm', '-60.370000mm', 'Top', '90']); w.writerow(['U5B', '60.860000mm', '-60.370000mm', 'Top', '90'])
print('BOM lines', len(rows), 'placed parts', len(placed), 'CPL rows', n, 'loose', len(loose))
json_ = [(r, v, l) for r, v, l in loose]
print('loose parts (not in BOM):', json_)

# variant with the cable-side screw plugs (C5188249 2P / C5188250 3P / C5188251 4P) placed on top of each terminal
import re
PL = {2: 'C5188249', 3: 'C5188250', 4: 'C5188251'}
pins = {c.get('ref'): int(re.search(r'_(\d)-G-3\.5', c.findtext('footprint') or '').group(1)) for c in root.find('components') if re.search(r'_(\d)-G-3\.5', c.findtext('footprint') or '')}
cpl = {r[0]: r for r in csv.reader(open(out + '/CPL-rev_d.csv'))}
bom = list(csv.reader(open(out + '/BOM-rev_d.csv')))
add = collections.defaultdict(list)
for r, n in sorted(pins.items()): add[n].append(r)
for n, refs in sorted(add.items()):
    bom.append(['%dP 3.5mm plug screw terminal' % n, ', '.join('P' + r for r in refs), 'Plug_%dP_3.5mm' % n, PL[n]])
with open(out + '/BOM-rev_d_with_plugs.csv', 'w', newline='') as f: csv.writer(f).writerows(bom)
with open(out + '/CPL-rev_d_with_plugs.csv', 'w', newline='') as f:
    w = csv.writer(f)
    for r in csv.reader(open(out + '/CPL-rev_d.csv')): w.writerow(r)
    for r in sorted(pins): w.writerow(['P' + r] + cpl[r][1:])
print('plug variant', {n: len(v) for n, v in add.items()})
