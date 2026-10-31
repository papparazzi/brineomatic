"""Delete zones on nets that no longer have pads, then tracks/vias that DRC reports as dangling (repeat).
usage: pcb_cleanup.py <pcb> <drc_json>   (drc_json produced by kicad-cli on the same file; run in a loop by the caller)"""
import sys, json
import pcbnew
pcb, drc = sys.argv[1:3]
b = pcbnew.LoadBoard(pcb)
want = set()
for v in json.load(open(drc))['violations']:
    if v['type'] in ('track_dangling', 'via_dangling'):
        for i in v['items']:
            want.add(i['uuid'])
padnets = {p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
dead_tracks = [t for t in b.GetTracks() if t.m_Uuid.AsString() in want]
dead_zones = [z for z in b.Zones() if z.GetNetname() and z.GetNetname() not in padnets]
for t in dead_tracks:
    b.Remove(t)
for z in dead_zones:
    b.Remove(z)
b.Save(pcb)
print('removed tracks', len(dead_tracks), 'zones', len(dead_zones))
