"""Silkscreen for J1/J28 after the ESD diodes moved beside them: shorter names, pin letters closer to the pads.  usage: in out"""
import sys, pcbnew
from pcbnew import VECTOR2I, FromMM as mm
b = pcbnew.LoadBoard(sys.argv[1])
rm = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT' and d.GetLayerName() == 'F.Silkscreen'
      and 166.5 < pcbnew.ToMM(d.GetPosition().x) < 174.0 and 43.5 < pcbnew.ToMM(d.GetPosition().y) < 70.5]
print('removed', sorted(d.GetText() for d in rm))
for d in rm: b.Remove(d)
def text(s, x, y, ang, h=1.0, th=0.15):
    t = pcbnew.PCB_TEXT(b); t.SetLayer(pcbnew.F_SilkS); t.SetText(s); t.SetPosition(VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(th)); t.SetTextAngleDegrees(ang); b.Add(t)
for name, yc in (('BRINE', 49.6), ('PROD', 63.9)):
    text(name, 168.6 if name == 'BRINE' else 169.5, yc, 90, 1.0, 0.15)
    for ch, dy in (('S', 3.5), ('+', 0.0), ('-', -3.5)):
        text(ch, 172.7, yc + dy, 0, 1.0)
for f in b.GetFootprints():          # references of the two terminals inside the body area (clear of the pin letters)
    if f.GetReference() in ('D8', 'D41'):
        r = f.Reference(); r.SetPosition(VECTOR2I(mm(170.4), mm(f.GetPosition().y / 1e6 - 1.5))); r.SetTextAngleDegrees(0)
    if f.GetReference() in ('J1', 'J28'):
        r = f.Reference(); r.SetPosition(VECTOR2I(mm(181.0), mm(49.6 if f.GetReference() == 'J1' else 63.9))); r.SetTextAngleDegrees(90)
b.Save(sys.argv[2])
