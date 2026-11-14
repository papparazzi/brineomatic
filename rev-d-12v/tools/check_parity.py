"""Schematic-to-board parity count without KiCad's report limit (kicad-cli's DRC lists at most 199 entries per type).
For every netlist part that belongs on the board: footprint present, value, footprint name, every netlist field against the
footprint's field (a Datasheet of '~' counts as empty), every pad's net. Footprints with no symbol are listed too.
usage: check_parity.py <pcb> <netlist.xml>      (KiCad 10 Python; netlist: kicad-cli sch export netlist --format kicadxml)"""
import sys, collections, xml.etree.ElementTree as ET
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); root = ET.parse(sys.argv[2]).getroot()
comp = {}
for c in root.find('components'):
    props = {p.get('name') for p in c.findall('property')}
    if 'exclude_from_board' not in props: comp[c.get('ref')] = c
pin = {}
for n in root.find('nets'):
    for nd in n.findall('node'): pin[(nd.get('ref'), nd.get('pin'))] = n.get('name')
fps = {f.GetReference(): f for f in b.GetFootprints()}
fields = collections.Counter(); parts = collections.defaultdict(list); nets = []; other = []
for ref, c in sorted(comp.items()):
    f = fps.get(ref)
    if f is None: other.append('no footprint for ' + ref); continue
    if f.GetValue() != c.findtext('value'): other.append('value %s: %r / %r' % (ref, f.GetValue(), c.findtext('value')))
    if f.GetFPIDAsString() != c.findtext('footprint'): other.append('footprint %s: %s / %s' % (ref, f.GetFPIDAsString(), c.findtext('footprint')))
    for fd in c.find('fields'):
        k, v = fd.get('name'), fd.text or ''
        if k == 'Footprint': continue
        fv = f.GetFieldText(k) if f.HasField(k) else None
        if (fv or '').strip() == '~': fv = ''
        if fv != v: fields[k] += 1; parts[ref].append(k)
    for p in f.Pads():
        if not p.GetNumber() or not p.IsOnCopperLayer(): continue
        want = pin.get((ref, p.GetNumber()))
        if want is not None and p.GetNetname() != want: nets.append('%s.%s %s / %s' % (ref, p.GetNumber(), p.GetNetname(), want))
for ref, f in sorted(fps.items()):
    if ref not in comp and not (f.GetAttributes() & pcbnew.FP_BOARD_ONLY): other.append('footprint without symbol: ' + ref)
print('differing fields: %d in %d footprints %s' % (sum(fields.values()), len(parts), dict(fields.most_common())))
print('pad nets differing: %d %s' % (len(nets), nets[:20]))
print('other: %d %s' % (len(other), other[:20]))
if len(sys.argv) > 3: print('fields differing on %s: %s' % (sys.argv[3], {r: parts[r] for r in sys.argv[3].split(',') if r in parts}))
