"""Dump connectivity islands (pads only) for nets as JSON.  usage: pcb_islands.py <pcb> <out.json> [net ...]"""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); c = b.GetConnectivity(); mm = pcbnew.ToMM
want = set(sys.argv[3:])
items = {}
for f in b.GetFootprints():
    for p in f.Pads():
        items.setdefault(p.GetNetname(), []).append(p)
for t in b.GetTracks():
    items.setdefault(t.GetNetname(), []).append(t)
out = {}
for net, its in items.items():
    if not net or (want and net not in want):
        continue
    key = lambda i: i.m_Uuid.AsString()
    parent = {key(i): key(i) for i in its}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    by = {key(i): i for i in its}
    for i in its:
        for j in list(c.GetConnectedItems(i)):
            if key(j) in parent:
                parent[find(key(i))] = find(key(j))
    comps = {}
    for k in parent:
        comps.setdefault(find(k), []).append(by[k])
    if len(comps) > 1:
        out[net] = [[[x.GetParentFootprint().GetReference() + '.' + x.GetNumber(), round(mm(x.GetX()), 3), round(mm(x.GetY()), 3), int(x.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)]
                     for x in cl if x.GetClass() == 'PAD'] for cl in comps.values()]
json.dump(out, open(sys.argv[2], 'w'))
print({k: len(v) for k, v in out.items()})
