"""Provisional placement of the new power-stage parts (old eFuse area). usage: pcb_place_power.py <pcb>"""
import sys, pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard(sys.argv[1])
P = {'Q9': (139.0, 54.5, 0), 'Q10': (139.0, 60.5, 0), 'D56': (143.5, 57.5, 90), 'R78': (143.5, 61.0, 90)}
fps = {f.GetReference(): f for f in b.GetFootprints()}
for r, (x, y, a) in P.items():
    fps[r].SetPosition(VECTOR2I(mm(x), mm(y))); fps[r].SetOrientationDegrees(a)
b.Save(sys.argv[1])
