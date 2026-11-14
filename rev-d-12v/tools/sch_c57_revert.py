"""Rev D step 27: C57, the bulk capacitor of the TMC2209 supply (+12V), back to Rev-C1's part: 100 uF / 35 V, LCSC C2836442
(KNSCHA RVT100UF35V67RV0034, 6.3 x 7.7 mm, the same footprint as before). Step 6 had swapped it for 47 uF / 50 V C3349 to
save a line fee, but JLCPCB's line-by-line fee test of 1 Nov 2026 showed that C3349 is charged too, and no 100 uF SMD
electrolytic at JLCPCB is fee-free (14 Nov 2026: 1,146 found, all Extended, none preferred). The swap only halved the capacitance.
Edits only the Value and LCSC properties of C57 in tmc2209.kicad_sch; line endings and everything else stay as they are.
usage: sch_c57_revert.py <schematic folder>"""
import sys, os
p = os.path.join(sys.argv[1], 'tmc2209.kicad_sch')
t = open(p, 'rb').read().decode('utf-8')
i = t.index('(property "Reference" "C57"')
s = t.rindex('(symbol (lib_id', 0, i)                    # this sheet was re-saved by kiutils: one symbol header per line
e = t.find('(symbol (lib_id', i)
e = len(t) if e < 0 else e
blk = t[s:e]
OLD_V, NEW_V = '(property "Value" "47uF / 50v"', '(property "Value" "100uF / 35v"'
OLD_L, NEW_L = '(property "LCSC" "C3349"', '(property "LCSC" "C2836442"'
assert blk.count(OLD_V) == 1 and blk.count(OLD_L) == 1, 'C57 is not in the step-26 state'
assert '(property "Footprint" "Capacitor_SMD:CP_Elec_6.3x7.7"' in blk
t = t[:s] + blk.replace(OLD_V, NEW_V).replace(OLD_L, NEW_L) + t[e:]
open(p, 'wb').write(t.encode('utf-8'))
print('C57: 47uF / 50v, C3349 -> 100uF / 35v, C2836442')
