"""Rev D step 27: the board side of sch_c57_revert.py. C57's footprint (CP_Elec_6.3x7.7, as in Rev-C1 and step 26) stays where
it is; only its Value text, on F.Fab, goes back to "100uF / 35v". Its LCSC field still reads C2836442: the board was never
changed when step 6 swapped the part. A text edit, so KiCad does not re-save the file and nothing else changes.
usage: pcb_c57_revert.py <in.kicad_pcb> <out.kicad_pcb>"""
import sys, re
t = open(sys.argv[1], 'rb').read().decode('utf-8')
i = t.index('(property "Reference" "C57"')
s = t.rindex('\t(footprint "', 0, i)
e = re.compile(r'\n\t\)\r?\n').search(t, i).end()       # the footprint's closing bracket (nested ones are indented deeper)
blk = t[s:e]
OLD, NEW = '(property "Value" "47uF / 50v"', '(property "Value" "100uF / 35v"'
assert blk.startswith('\t(footprint "Capacitor_SMD:CP_Elec_6.3x7.7"'), 'C57 footprint changed'
assert blk.count(OLD) == 1 and '(property "LCSC" "C2836442"' in blk, 'C57 is not in the step-26 state'
t = t[:s] + blk.replace(OLD, NEW) + t[e:]
open(sys.argv[2], 'wb').write(t.encode('utf-8'))
print('C57 value on the board: 47uF / 50v -> 100uF / 35v')
