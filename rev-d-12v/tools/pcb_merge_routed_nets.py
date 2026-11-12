"""Copy only the newly autorouted tracks/vias of the named nets from a Freerouting result into the hand-edited board.
usage: pcb_merge_routed_nets.py <base.kicad_pcb> <routed.kicad_pcb> <out.kicad_pcb> <spec.json> NET [NET...]
Freerouting also drops micro-segments on unrelated nets; those are ignored here. The copied items are written to
<spec.json> so the routing is reproducible without rerunning the autorouter."""
import sys, json
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
base, routed, out, spec, nets = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], set(sys.argv[5:])
def key(b, t):
    v = t.GetClass() == "PCB_VIA"
    p = tuple(sorted([(round(ToMM(t.GetStart().x), 3), round(ToMM(t.GetStart().y), 3)), (round(ToMM(t.GetEnd().x), 3), round(ToMM(t.GetEnd().y), 3))]))
    return (t.GetNetname(), "via" if v else b.GetLayerName(t.GetLayer())) + p
a = pcbnew.LoadBoard(base); have = set(key(a, t) for t in a.GetTracks())
r = pcbnew.LoadBoard(routed)
items = []
for t in r.GetTracks():
    k = key(r, t)
    if t.GetNetname() in nets and k not in have:
        if k[1] == "via": items.append({"net": k[0], "via": [k[2][0], k[2][1]], "d": ToMM(t.GetWidth(pcbnew.F_Cu)), "drill": ToMM(t.GetDrill())})
        else: items.append({"net": k[0], "layer": k[1], "w": ToMM(t.GetWidth()), "a": list(k[2]), "b": list(k[3])})
json.dump(items, open(spec, "w"), indent=0)
for it in items:
    n = a.FindNet(it["net"])
    if "via" in it:
        v = pcbnew.PCB_VIA(a); v.SetPosition(VECTOR2I(FromMM(it["via"][0]), FromMM(it["via"][1]))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetWidth(pcbnew.F_Cu, FromMM(it["d"])); v.SetDrill(FromMM(it["drill"])); v.SetNet(n); a.Add(v)
    else:
        t = pcbnew.PCB_TRACK(a); t.SetStart(VECTOR2I(FromMM(it["a"][0]), FromMM(it["a"][1]))); t.SetEnd(VECTOR2I(FromMM(it["b"][0]), FromMM(it["b"][1])))
        t.SetWidth(FromMM(it["w"])); t.SetLayer(a.GetLayerID(it["layer"])); t.SetNet(n); a.Add(t)
pcbnew.ZONE_FILLER(a).Fill(a.Zones())
pcbnew.SaveBoard(out, a)
print("copied", len(items), "items for", sorted(nets))
