"""Silkscreen text for Rev D 12 V.  usage: pcb_silk.py <pcb>"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
M = {'24V': '12V', 'POWER\n24V   GND': 'POWER\n12V   GND', 'REV C1': 'REV D 12V'}
n = 0
for d in b.GetDrawings():
    if d.GetClass() == 'PCB_TEXT' and d.GetText() in M:
        d.SetText(M[d.GetText()]); n += 1
b.Save(sys.argv[1]); print('texts changed', n)
