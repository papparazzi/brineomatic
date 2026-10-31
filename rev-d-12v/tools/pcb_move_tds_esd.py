"""Move the TDS ESD diodes D8, D41 next to their terminals J1, J28 (rot 0, signal pad east) and drop the old TDS tracks.  usage: in out"""
import sys, pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard(sys.argv[1])
POS = {'D8': (170.4, 53.1), 'D41': (170.4, 67.4)}
rm = [t for t in b.GetTracks() if t.GetNetname() in ('BRINE_TDS', 'PRODUCT_TDS')]
print('tracks/vias removed:', len(rm))
for f in b.GetFootprints():
    if f.GetReference() in POS:
        f.SetOrientationDegrees(0); f.SetPosition(VECTOR2I(mm(POS[f.GetReference()][0]), mm(POS[f.GetReference()][1])))
for t in rm: b.Remove(t)
b.Save(sys.argv[2])
