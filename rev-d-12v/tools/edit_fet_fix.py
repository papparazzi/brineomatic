"""Fix of the reverse-polarity stage (found in review 29 Oct):
 * Q9/Q10 must have DRAIN on the battery side (PRE_24) and SOURCE on the load rail so the body diode blocks a reversed battery
   (mirror the symbols in x); the gate zener D56 then sits source-to-gate, i.e. on the +12V rail.
 * D19 is a BIDIRECTIONAL SMBJ16CA again, so a reversed battery does not conduct through it and blow F1.
usage: edit_fet_fix.py <kicad_dir> <symbols_dir>"""
import sys, copy
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from kiutils.schematic import Schematic
from kiutils.items.common import Position
from kiutils.items.schitems import LocalLabel
from schlib import ref, prune, R2
import uuid
kd = sys.argv[1]
f = kd + '/power_supply.kicad_sch'
s = Schematic.from_file(f)
T = {ref(x): x for x in s.schematicSymbols}
for r in ('Q9', 'Q10'):
    T[r].mirror = 'x'
d56 = T['D56']; d56.position = Position(X=165.1, Y=41.91, angle=270)
# old gate-clamp wiring: K was tied into the PRE_24 bus at y=48.26 via a stub, A had a label at y=59.69
s.graphicalItems = [g for g in s.graphicalItems if not (g.type == 'wire' and [(R2(p.X), R2(p.Y)) for p in g.points] in ([(165.1, 48.26), (165.1, 52.07)], [(165.1, 52.07), (165.1, 48.26)]))]
s.labels = [l for l in s.labels if not (R2(l.position.X) == 165.1 and R2(l.position.Y) == 59.69)]
l = LocalLabel(text='PFET_G', position=Position(X=165.1, Y=45.72, angle=270)); l.uuid = str(uuid.uuid4()); s.labels.append(l)
# the PRE_24 bus ended at 165.1 only to reach the old D56 stub: trim it back to the last FET
for g in s.graphicalItems:
    if g.type == 'wire':
        pts = [(R2(p.X), R2(p.Y)) for p in g.points]
        if sorted(pts) == [(133.35, 48.26), (165.1, 48.26)]:
            for p in g.points:
                if R2(p.X) == 165.1: p.X = 162.56
from kiutils.items.schitems import Junction
j = Junction(position=Position(X=165.1, Y=38.1)); j.uuid = str(uuid.uuid4()); s.junctions.append(j)
s.junctions = [j for j in s.junctions if not (R2(j.position.X) == 165.1 and R2(j.position.Y) == 48.26)]
# D19: bidirectional again
d19 = T['D19']
tvs = [x for x in s.libSymbols if x.libId == 'Device:D_TVS']
assert tvs, 'D_TVS lib symbol missing'
d19.libId = 'Device:D_TVS'
for p in d19.properties:
    if p.key == 'Value': p.value = 'SMBJ16CA'
    if p.key == 'LCSC': p.value = 'C19077572'
    if p.key == 'Description': p.value = '16V bidirectional TVS, SMB'
print(prune(s))
s.to_file(f)
