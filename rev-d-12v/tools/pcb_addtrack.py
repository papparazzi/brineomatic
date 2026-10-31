"""Add a track/via spec to a board.  usage: pcb_addtrack.py <in> <out> <net> <spec.json>
spec = list of ["F"|"B", x1,y1,x2,y2,width] or ["via", x, y]"""
import sys, json, pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard(sys.argv[1]); net = b.FindNet(sys.argv[3])
for s in json.load(open(sys.argv[4])):
    if s[0] == 'via':
        v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(mm(s[1]), mm(s[2]))); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(net); b.Add(v)
    else:
        t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(mm(s[1]), mm(s[2]))); t.SetEnd(VECTOR2I(mm(s[3]), mm(s[4])))
        t.SetWidth(mm(s[5])); t.SetLayer(pcbnew.F_Cu if s[0] == 'F' else pcbnew.B_Cu); t.SetNet(net); b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[2])
