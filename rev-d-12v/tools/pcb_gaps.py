"""List connectivity islands (components) per net that still have >1 island.  usage: pcb_gaps.py <pcb> [net ...]"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); c = b.GetConnectivity(); mm = pcbnew.ToMM
want = sys.argv[2:]
items = {}
for f in b.GetFootprints():
    for p in f.Pads():
        items.setdefault(p.GetNetname(), []).append(p)
for t in b.GetTracks():
    items.setdefault(t.GetNetname(), []).append(t)
def desc(i):
    k = i.GetClass()
    if k == 'PAD':
        return 'pad %s.%s@(%.1f,%.1f)' % (i.GetParentFootprint().GetReference(), i.GetNumber(), mm(i.GetX()), mm(i.GetY()))
    if k == 'PCB_VIA':
        return 'via@(%.1f,%.1f)' % (mm(i.GetX()), mm(i.GetY()))
    return 'trk %s (%.1f,%.1f)-(%.1f,%.1f)' % (i.GetLayerName(), mm(i.GetStart().x), mm(i.GetStart().y), mm(i.GetEnd().x), mm(i.GetEnd().y))
for net, its in items.items():
    if want and net not in want:
        continue
    if not net:
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
        print('NET', net, len(comps), 'islands')
        for cl in sorted(comps.values(), key=len):
            ps = [x for x in cl if x.GetClass() == 'PAD']
            print('   %3d items; e.g. %s' % (len(cl), '; '.join(desc(x) for x in (ps[:3] or cl[:2]))))
