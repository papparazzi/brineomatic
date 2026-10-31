"""Silkscreen for the east-edge terminals J6,J29,J1,J28 (pin letters S + - and a name); remove the labels of the old 2x3 headers.  usage: in out"""
import sys, pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard(sys.argv[1])
OLD = {'TDS', 'S  +  -', 'S + -', 'SERVOS', '2\n1'}
rm = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT' and d.GetLayerName() == 'F.Silkscreen' and d.GetText() in OLD
      and 95 < pcbnew.ToMM(d.GetPosition().x) < 150 and 30 < pcbnew.ToMM(d.GetPosition().y) < 45]
print('old labels removed', [d.GetText() for d in rm])
pads = {}
for f in b.GetFootprints():
    if f.GetReference() in ('J6', 'J29', 'J1', 'J28'):
        pads[f.GetReference()] = sorted([(p.GetNumber(), pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for p in f.Pads()])
for d in rm: b.Remove(d)
def text(s, x, y, ang, h=1.0, th=0.15):
    t = pcbnew.PCB_TEXT(b); t.SetLayer(pcbnew.F_SilkS); t.SetText(s); t.SetPosition(VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(th)); t.SetTextAngleDegrees(ang); b.Add(t)
NAME = {'J6': 'SERVO 1', 'J29': 'SERVO 2', 'J1': 'BRINE TDS', 'J28': 'PRODUCT TDS'}
for r, ps in pads.items():
    yc = sum(p[2] for p in ps) / 3; x = ps[0][1]
    text(NAME[r], x - 6.0, yc, 90, 1.2, 0.18)
    for (num, px, py_), ch in zip(ps, ('S', '+', '-')):      # pad 1 = signal, 2 = +, 3 = -
        text(ch, x - 3.2, py_, 0, 1.0)
b.Save(sys.argv[2])
