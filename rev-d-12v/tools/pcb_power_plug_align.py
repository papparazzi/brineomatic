"""Rev D step 23: power plug J10 moved 2.0 mm towards the board edge so that its front lines up with the other bottom-edge plugs.
Rev-C1 had a larger 5.08 mm terminal here whose front was at the same line as the others (y 95.55). The October swap to the 3.5 mm
part kept the old pin position, which left the smaller body 2.0 mm inside (front at y 93.55). No net change: the 2.0 mm wide supply
track is extended by 2.0 mm on the same layer; the GND pin stays in the ground pour. The POWER label moves with the plug.
usage: pcb_power_plug_align.py <in.kicad_pcb> <out.kicad_pcb>      (KiCad 10 Python)"""
import sys
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
FPS = dict((f.GetReference(), f) for f in b.GetFootprints()); DRAW = list(b.GetDrawings())
D = 2.0
j = FPS["J10"]
p1 = [p for p in j.Pads() if p.GetNumber() == "1"][0]
x, y, net = p1.GetPosition().x, p1.GetPosition().y, p1.GetNet()
assert abs(ToMM(y) - 85.5) < 0.01 and p1.GetNetname() == "Net-(J10-Pin_1)"
j.Move(VECTOR2I(0, FromMM(D)))
t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(x, y)); t.SetEnd(VECTOR2I(x, y + FromMM(D))); t.SetWidth(FromMM(2.0)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); b.Add(t)
n = 0
for d in DRAW:
    if d.GetClass() == "PCB_TEXT" and d.GetText().startswith("POWER"): d.Move(VECTOR2I(0, FromMM(D))); n += 1
assert n == 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print("J10 pins now at y %.2f" % ToMM(p1.GetPosition().y))
