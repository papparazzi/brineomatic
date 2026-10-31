"""Hand-route the new reverse-polarity stage (Q9/Q10/D56/R78) cleanly.  usage: pcb_route_power.py <in.kicad_pcb> <out.kicad_pcb>
Q9/Q10 rotated 180 deg so sources (PRE_24) and gates face D56/R78/D19, drains (+12V) face west."""
import sys, pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard(sys.argv[1])
BOX = (130, 50, 152, 70)
def inbox(t):
    x, y = pcbnew.ToMM(t.GetX()), pcbnew.ToMM(t.GetY())
    return BOX[0] < x < BOX[2] and BOX[1] < y < BOX[3]
def at(t, x, y):
    return abs(pcbnew.ToMM(t.GetX()) - x) < 0.05 and abs(pcbnew.ToMM(t.GetY()) - y) < 0.05
OLD_VIAS = [(141.2, 55.45), (141.2, 61.45), (144.6, 55.85), (144.6, 63.02), (144.7, 61.4), (136.5, 60.5)]
dead = []
for t in b.GetTracks():
    if not inbox(t):
        continue
    isvia = t.GetClass() == 'PCB_VIA'
    n = t.GetNetname()
    if n.endswith(('PRE_24', 'PFET_G')) and not (isvia and pcbnew.ToMM(t.GetX()) < 138):
        dead.append(t)
    elif not isvia and n == '+12V':
        dead.append(t)
    elif isvia and any(at(t, *v) for v in OLD_VIAS):
        dead.append(t)
    elif isvia and n == 'GND' and 134 < pcbnew.ToMM(t.GetX()) < 137.6 and 59 < pcbnew.ToMM(t.GetY()) < 63:
        dead.append(t)
    elif (not isvia) and n == 'GND' and pcbnew.ToMM(t.GetLength()) < 1.0 and pcbnew.ToMM(t.GetX()) > 140:
        dead.append(t)
fps = {f.GetReference(): f for f in b.GetFootprints()}
nets = {n: b.FindNet(n) for n in ('+12V', 'GND', '/Power Supply/PRE_24', '/Power Supply/PFET_G')}
for t in dead:
    b.Remove(t)
for r, (x, y, a) in {'Q9': (139.0, 54.5, 180), 'Q10': (139.0, 60.5, 180), 'D56': (143.0, 57.2, 270), 'R78': (143.0, 60.3, 90)}.items():
    fps[r].SetPosition(VECTOR2I(mm(x), mm(y))); fps[r].SetOrientationDegrees(a)
if fps['Q10'].IsFlipped():
    pass
def trk(net, layer, w, *pts):
    for p, q in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(mm(p[0]), mm(p[1]))); t.SetEnd(VECTOR2I(mm(q[0]), mm(q[1])))
        t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(nets[net]); b.Add(t)
def via(net, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(0.45)); v.SetDrill(mm(0.2))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(nets[net]); b.Add(v)
F = pcbnew.F_Cu
PRE, G, P12, GND = '/Power Supply/PRE_24', '/Power Supply/PFET_G', '+12V', 'GND'
# Q10 is mirrored so its pad order is G (top) / S (bottom): see MIRROR_Q10 below
trk(PRE, F, 0.6, (139.94, 53.55), (144.7, 53.55), (145.7, 54.1))          # Q9.S -> C13 / PRE_24 copper
trk(PRE, F, 0.6, (139.94, 61.45), (148.9, 61.45))                          # Q10.S -> D19.1
trk(PRE, F, 0.4, (143.0, 53.55), (143.0, 55.55))                           # D56.1 up to the PRE track
trk(G, F, 0.25, (139.94, 55.45), (141.3, 55.45), (141.3, 60.3))            # gate bus
trk(G, F, 0.25, (139.94, 59.55), (141.3, 59.55))
trk(G, F, 0.25, (143.0, 58.85), (141.3, 58.85))                            # D56.2
trk(G, F, 0.25, (142.18, 60.3), (141.3, 60.3))                             # R78.1
trk(GND, F, 0.25, (143.82, 60.3), (144.9, 60.3)); via(GND, 144.9, 60.3)   # R78.2
trk(P12, F, 0.6, (138.06, 54.5), (134.8, 54.5))                            # drains
trk(P12, F, 0.6, (138.06, 60.5), (136.5, 60.5), (136.5, 54.5))
b.Save(sys.argv[2])
print('removed', len(dead))
