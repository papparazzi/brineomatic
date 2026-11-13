"""Rev D step 22: no copper fill under the Wi-Fi antenna end of the dev board. No net change.
A rule area on all four copper layers, x 34.0-65.0, y 22.0-31.8 (KiCad mm): from 6.8 mm beyond the dev board's antenna edge (y 28.84)
down to 1.9 mm above the pin-1 row (y 33.70; any closer leaves copper slivers on the 3.3 V plane), 2.7 mm wider than the dev board on each side. Only fills are excluded; there are no
tracks or vias in that area. The 3V3 and GND pins at y 33.70 keep their plane connections from the south side.
usage: pcb_antenna_keepout.py <in.kicad_pcb> <out.kicad_pcb>      (KiCad 10 Python)"""
import sys
import pcbnew
from pcbnew import FromMM, VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
X0, X1, Y0, Y1 = 34.0, 65.0, 22.0, 31.8
z = pcbnew.ZONE(b)
z.SetIsRuleArea(True)
ls = pcbnew.LSET()
for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu): ls.AddLayer(l)
z.SetLayerSet(ls)
z.SetZoneName("WiFi antenna keep-out (no copper fill)")
for name, val in (("SetDoNotAllowZoneFills", True), ("SetDoNotAllowCopperPour", True), ("SetDoNotAllowTracks", False), ("SetDoNotAllowVias", False), ("SetDoNotAllowPads", False), ("SetDoNotAllowFootprints", False)):
    if hasattr(z, name): getattr(z, name)(val)
o = z.Outline(); o.NewOutline()
for x, y in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)): o.Append(FromMM(x), FromMM(y))
b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print("keep-out added", [n for n in ("SetDoNotAllowZoneFills", "SetDoNotAllowCopperPour") if hasattr(z, n)])
