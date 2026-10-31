"""Rev D: sensor/stepper connectors -> 3.5 mm pluggable screw terminals.  usage: edit_swaps3.py <kicad_dir>"""
import sys, glob
from kiutils.schematic import Schematic
kd = sys.argv[1]
FP = {2: 'Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal', 3: 'Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal', 4: 'Connector_Phoenix_MC:PhoenixContact_MC_1,5_4-G-3.5_1x04_P3.50mm_Horizontal'}
LC = {2: 'C5188295', 3: 'C5188296', 4: 'C5188297'}
S = {'J3': 2, 'J18': 2, 'J4': 3, 'J5': 3, 'J11': 3, 'J22': 3, 'J23': 3, 'J21': 4}
done = set()
for f in glob.glob(kd + '/*.kicad_sch'):
    s = Schematic.from_file(f); ch = False
    for x in s.schematicSymbols:
        pr = {p.key: p for p in x.properties}; r = pr['Reference'].value
        if r in S:
            n = S[r]; pr['Footprint'].value = FP[n]; pr['LCSC'].value = LC[n]; pr['Value'].value = '3.5MM'; done.add(r); ch = True
    if ch: s.to_file(f)
print('missing', sorted(set(S) - done))
