"""Widen sub-0.2 mm tracks, add +3.3V In2 patch under the socket strip, refill.  usage: pcb_finish.py <in> <out>"""
import sys, pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard(sys.argv[1])
n = 0
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK' and t.GetWidth() < mm(0.2):
        t.SetWidth(mm(0.2)); n += 1
z = pcbnew.ZONE(b)
z.SetLayer(pcbnew.In2_Cu); z.SetNet(b.FindNet('+3.3V')); z.SetAssignedPriority(9)
z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.2))
ol = z.Outline(); ol.NewOutline()
for x, y in ((34.8, 29.8), (62.0, 29.8), (62.0, 91.7), (34.8, 91.7)):
    ol.Append(mm(x), mm(y))
b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[2]); print('widened', n)
