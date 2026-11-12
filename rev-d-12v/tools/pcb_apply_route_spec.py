"""Apply a stored routing spec (JSON list written by pcb_merge_routed_nets.py, hand-adjusted where noted in the change register)
and remove the stubs that the old U9 connections left behind.
usage: pcb_apply_route_spec.py <in.kicad_pcb> <spec.json> <out.kicad_pcb>"""
import sys, json
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
src, spec, out = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
TRACKS = list(b.GetTracks())
def near(p, x, y): return abs(ToMM(p.x) - x) < 0.03 and abs(ToMM(p.y) - y) < 0.03
STUBS = [("TMC2209_EN", "B.Cu", 143.10, 46.20, 139.95, 43.05), ("TMC2209_EN", "B.Cu", 147.15, 46.20, 143.10, 46.20), ("TMC2209_EN", "via", 147.15, 46.20),
         ("TMC2209_DIR", "B.Cu", 157.60, 46.61, 158.25, 45.96), ("TMC2209_DIR", "via", 158.25, 45.96), ("+3.3V", "via", 163.15, 50.95)]
n = 0
for t in TRACKS:
    for s in STUBS:
        if t.GetNetname() != s[0]: continue
        if s[1] == "via":
            hit = t.GetClass() == "PCB_VIA" and near(t.GetPosition(), s[2], s[3])
        else:
            hit = t.GetClass() != "PCB_VIA" and b.GetLayerName(t.GetLayer()) == s[1] and ((near(t.GetStart(), s[2], s[3]) and near(t.GetEnd(), s[4], s[5])) or (near(t.GetStart(), s[4], s[5]) and near(t.GetEnd(), s[2], s[3])))
        if hit: b.Remove(t); n += 1; break
assert n == len(STUBS), (n, len(STUBS))
for t in TRACKS:      # old EN track on the back: the new route leaves it at x 137.584, cut the rest off
    if t.GetNetname() == "TMC2209_EN" and t.GetClass() != "PCB_VIA" and near(t.GetStart(), 139.95, 43.05) and near(t.GetEnd(), 122.35, 43.05):
        t.SetStart(VECTOR2I(FromMM(137.584), FromMM(43.05))); n += 1
    elif t.GetNetname() == "TMC2209_EN" and t.GetClass() != "PCB_VIA" and near(t.GetEnd(), 139.95, 43.05) and near(t.GetStart(), 122.35, 43.05):
        t.SetEnd(VECTOR2I(FromMM(137.584), FromMM(43.05))); n += 1
assert n == len(STUBS) + 1, n
items = json.load(open(spec))
for it in items:
    net = b.FindNet(it["net"])
    if "via" in it:
        v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(FromMM(it["via"][0]), FromMM(it["via"][1]))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetWidth(pcbnew.F_Cu, FromMM(it["d"])); v.SetDrill(FromMM(it["drill"])); v.SetNet(net); b.Add(v)
    else:
        t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(FromMM(it["a"][0]), FromMM(it["a"][1]))); t.SetEnd(VECTOR2I(FromMM(it["b"][0]), FromMM(it["b"][1])))
        t.SetWidth(FromMM(it["w"])); t.SetLayer(b.GetLayerID(it["layer"])); t.SetNet(net); b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(out, b)
print("stubs removed", n, "| spec items", len(items))
