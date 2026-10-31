"""Let every copper zone reach a new east board edge.  usage: pcb_widen_zones.py in out X1_mm"""
import sys, pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard(sys.argv[1]); X1 = float(sys.argv[3]); n = 0
for z in b.Zones():
    o = z.Outline()
    for i in range(o.OutlineCount()):
        ch = o.Outline(i)
        for k in range(ch.PointCount()):
            p = ch.CPoint(k)
            if pcbnew.ToMM(p.x) > 181.0: ch.SetPoint(k, VECTOR2I(mm(X1 - 0.3), p.y)); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2]); print('moved', n, 'zone vertices')
