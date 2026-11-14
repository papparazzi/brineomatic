"""Rev D step 25 (independent review, major M2): a 12 V eFuse, TI TPS16630PWPR (LCSC C1849461), goes back between the reverse-polarity
P-FETs and the +12V rail, where Rev-C1 had its TPS26630. It caps any fault at about 3.8 A within about 1 us, so a short or an overload
no longer has to be stopped by the 3.15 A time-lag fuse while the SOT-23 MOSFETs carry it.
  - the MOSFET sources and D56 (gate clamp) move from +12V to a new net PFET_OUT: the bus segment between D56 and TP15 is deleted and
    PFET_OUT is labelled at the end of the remaining segment; PWR_FLAG #FLG04 stays on PFET_OUT and U3's OUT pins drive +12V;
  - U3 TPS16630 with Rev-C1's reference designators where Rev-C1 had the same function:
      R76 4.7k  ILIM -> current limit 18 kOhm.A / 4.7 kOhm = 3.83 A (+-10 %: 3.45-4.21 A; Rev-C1: 4.53k, 3.97 A)
      C15 100n  dVdT -> 25 ms soft start at 12 V
      R72 24k / R73 4.7k / R74 2.2k  UVLO/OVP divider -> on above 5.4 V (no practical UVLO, owner's M3 decision), off above 16.9 V
                (16.2-17.5 V worst case: above a 15.5-16 V equalisation charge, below the SMBJ16CA's 17.8 V breakdown)
      R75 0R    MODE to GND -> auto-retry after a fault, as Rev-C1; leave R75 off for latch-off
      R77 20k   IMON -> 0.56 V per A across R77 (measure at R77; the firmware does not read it)
      SHDN, FLT not connected: SHDN has an internal pull-up (device on), FLT is an open-drain output. A fault LED and test points
                were left out because the board has no room for them next to U3.
      C63 1u    input capacitor at IN
      PGOOD     to the existing global PGOOD net (buck U2 EN, R22 24k pull-up), as Rev-C1
  - the block sits in the free space at the bottom of the Power Supply sheet and connects by labels.
All values except U3 and the 0R are lines the BOM already has. No other part changes.
usage: sch_add_efuse.py <schematic folder>"""
import sys, os, re, uuid
F = os.path.join(sys.argv[1], 'power_supply.kicad_sch')
t = open(F, encoding='utf-8', newline='').read()
NL = '\r\n' if '\r\n' in t else '\n'
PATH = '/96477ae2-ef08-48f3-8dd4-fe4478541f68/7cbb3b3c-cf93-4880-b816-c6df902b993c'   # Power Supply sheet instance
_n = [0]
def U():                                       # deterministic UUIDs: a re-run gives the same file, and the board script links to them
    _n[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'github.com/papparazzi/brineomatic/rev-d-12v/step25/efuse/%d' % _n[0]))

# starting state (step 24)
assert '(reference "U3")' not in t and '(reference "R76")' not in t and '"PFET_OUT"' not in t
assert re.search(r'\(symbol \(lib_id "Transistor_FET:AO3401A"\) \(at 144\.78 43\.18 0\)', t)
wb = re.search(r'\r?\n  \(wire \(pts \(xy 176\.53 38\.1\) \(xy 195\.58 38\.1\)\)\r?\n    \(stroke \(width 0\) \(type default\)\)\r?\n    \(uuid [0-9a-f-]+\)\r?\n  \)', t)
wa = re.search(r'\(wire \(pts \(xy 147\.32 38\.1\) \(xy 176\.53 38\.1\)\)', t)
assert wb and wa
t = t[:wb.start()] + t[wb.end():]              # the bus no longer joins the MOSFET sources to +12V

# ---- library symbol for the TPS16630 in the PWP (HTSSOP-20) package
PINS = [('1', 'IN', 'power_in', 'L', 7.62), ('2', 'IN', 'power_in', 'L', 5.08), ('3', 'IN', 'power_in', 'L', 2.54),
        ('6', 'P_IN', 'power_in', 'L', 0), ('7', 'UVLO', 'input', 'L', -2.54), ('8', 'OVP', 'input', 'L', -5.08),
        ('13', '~{SHDN}', 'input', 'L', -7.62), ('12', 'MODE', 'input', 'L', -10.16),
        ('20', 'OUT', 'power_out', 'R', 7.62), ('19', 'OUT', 'passive', 'R', 5.08), ('18', 'OUT', 'passive', 'R', 2.54),   # one driver per net
        ('16', 'PGOOD', 'open_collector', 'R', 0), ('15', '~{FLT}', 'open_collector', 'R', -2.54), ('14', 'IMON', 'output', 'R', -5.08),
        ('10', 'dVdT', 'passive', 'R', -7.62), ('11', 'ILIM', 'passive', 'R', -10.16),
        ('9', '~', 'power_in', 'B', -2.54), ('21', '~', 'passive', 'B', 0),      # GND and exposed pad; names hidden (they would hit MODE/ILIM)
        ('4', 'NC', 'no_connect', 'T', -2.54), ('5', 'NC', 'no_connect', 'T', 0), ('17', 'NC', 'no_connect', 'T', 2.54)]
GEO = {'L': lambda v: (-10.16, v, 0), 'R': lambda v: (10.16, v, 180), 'B': lambda v: (v, -15.24, 90), 'T': lambda v: (v, 12.7, 270)}
E = '(effects (font (size 1.27 1.27)))'
EH = '(effects (font (size 1.27 1.27)) hide)'
lib = ['    (symbol "brineomatic_local:TPS16630PWP" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
       '      (property "Reference" "U" (at -7.62 11.43 0)', '        (effects (font (size 1.27 1.27)) (justify left))', '      )',
       '      (property "Value" "TPS16630PWP" (at 0 11.43 0)', '        (effects (font (size 1.27 1.27)) (justify left))', '      )',
       '      (property "Footprint" "Package_SO:HTSSOP-20-1EP_4.4x6.5mm_P0.65mm_EP3.4x6.5mm_Mask2.96x2.96mm" (at 0 -19.05 0)', '        ' + EH, '      )',
       '      (property "Datasheet" "https://www.ti.com/lit/ds/symlink/tps1663.pdf" (at 0 -21.59 0)', '        ' + EH, '      )',
       '      (property "Description" "60 V 6 A eFuse, adjustable current limit, adjustable overvoltage cut-off, HTSSOP-20" (at 0 0 0)', '        ' + EH, '      )',
       '      (symbol "TPS16630PWP_0_1"',
       '        (rectangle (start -7.62 10.16) (end 7.62 -12.7)', '          (stroke (width 0.254) (type default))', '          (fill (type background))', '        )',
       '      )', '      (symbol "TPS16630PWP_1_1"']
for num, name, kind, side, v in PINS:
    x, y, a = GEO[side](v)
    lib += ['        (pin %s line (at %g %g %d) (length 2.54)' % (kind, x, y, a),
            '          (name "%s" %s)' % (name, E), '          (number "%s" %s)' % (num, E), '        )']
lib += ['      )', '    )']
ls = t.index('\n  (lib_symbols')
d, i = 0, ls + 1
while True:                                    # end of the lib_symbols block
    c = t[i]
    if c == '"':
        i += 1
        while t[i] != '"': i += 2 if t[i] == chr(92) else 1
    elif c == '(': d += 1
    elif c == ')':
        d -= 1
        if d == 0: break
    i += 1
t = t[:i].rstrip(' ') + NL.join(lib) + NL + '  ' + t[i:]

# ---- placed items
items = []
def prop(name, val, x, y, hide=False, ang=0):
    return ['    (property "%s" "%s" (at %g %g %d)' % (name, val, x, y, ang), '      ' + (EH if hide else E), '    )']
def sym(lib_id, ref, val, x, y, ang, fields, pins, in_bom='yes', refat=None, valat=None, valhide=False):
    s = ['  (symbol (lib_id "%s") (at %g %g %d) (unit 1)' % (lib_id, x, y, ang),
         '    (in_bom %s) (on_board yes) (dnp no)' % in_bom, '    (uuid %s)' % U()]
    s += prop('Reference', ref, *(refat or (x + 2.54, y - 1.27)), ref.startswith('#')) + prop('Value', val, *(valat or (x + 2.54, y + 1.27)), valhide)
    for k, v in fields: s += prop(k, v, x, y, True)
    s += ['    (pin "%s" (uuid %s))' % (p, U()) for p in pins]
    s += ['    (instances', '      (project "brineomatic"', '        (path "%s"' % PATH, '          (reference "%s") (unit 1)' % ref,
          '        )', '      )', '    )', '  )']
    items.append(NL.join(s))
def wire(x1, y1, x2, y2):
    items.append(NL.join(['  (wire (pts (xy %g %g) (xy %g %g))' % (x1, y1, x2, y2), '    (stroke (width 0) (type default))', '    (uuid %s)' % U(), '  )']))
def junction(x, y):
    items.append(NL.join(['  (junction (at %g %g) (diameter 0) (color 0 0 0 0)' % (x, y), '    (uuid %s)' % U(), '  )']))
def label(text, x, y, ang):
    items.append(NL.join(['  (label "%s" (at %g %g %d)' % (text, x, y, ang), '    (effects (font (size 1 1)))', '    (uuid %s)' % U(), '  )']))
pwr = [200]
def gnd(x, y):
    pwr[0] += 1
    sym('power:GND', '#PWR0%d' % pwr[0], 'GND', x, y, 0, [('Footprint', ''), ('Datasheet', ''), ('Description', 'Power symbol creates a global label with name "GND" , ground'.replace('"', chr(92) + '"'))], ['1'])
R = 'Resistor_SMD:R_0603_1608Metric'; C = 'Capacitor_SMD:C_0603_1608Metric'
def res(ref, val, lcsc, x, y, ang=0, **kw): sym('Device:R_Small_US', ref, val, x, y, ang, [('Footprint', R), ('Datasheet', '~'), ('Description', 'Resistor, small US symbol'), ('LCSC', lcsc)], ['1', '2'], **kw)
def cap(ref, val, lcsc, x, y): sym('Device:C_Small', ref, val, x, y, 0, [('Footprint', C), ('Datasheet', '~'), ('Description', 'Unpolarized capacitor, small symbol'), ('LCSC', lcsc)], ['1', '2'])

label('PFET_OUT', 176.53, 38.1, 0)              # the MOSFET-source bus keeps D56, both sources and PWR_FLAG #FLG04
UX, UY = 100.33, 180.34                         # U3; left pins at x 90.17, right pins at x 110.49
sym('brineomatic_local:TPS16630PWP', 'U3', 'TPS16630PWPR', UX, UY, 0,
    [('Footprint', 'Package_SO:HTSSOP-20-1EP_4.4x6.5mm_P0.65mm_EP3.4x6.5mm_Mask2.96x2.96mm'), ('Datasheet', 'https://www.ti.com/lit/ds/symlink/tps1663.pdf'),
     ('Description', '60 V 6 A eFuse, adjustable current limit, adjustable overvoltage cut-off'), ('LCSC', 'C1849461')], [p[0] for p in PINS],
    refat=(92.71, 166.37), valat=(106.68, 166.37))
for x in (97.79, 100.33, 102.87):               # NC pins 4, 5, 17
    items.append(NL.join(['  (no_connect (at %g 167.64) (uuid %s))' % (x, U())]))
# input side: IN 1-3 and P_IN joined, C63 and the PFET_OUT label
for y1, y2 in ((172.72, 175.26), (175.26, 177.8), (177.8, 180.34)): wire(90.17, y1, 90.17, y2)
wire(85.09, 172.72, 90.17, 172.72); wire(82.55, 172.72, 85.09, 172.72); label('PFET_OUT', 82.55, 172.72, 90)
for x, y in ((90.17, 172.72), (90.17, 175.26), (90.17, 177.8), (85.09, 172.72)): junction(x, y)
cap('C63', '1uF', 'C15849', 85.09, 175.26); gnd(85.09, 177.8)
# UVLO / OVP divider
res('R72', '24k', 'C23352', 72.39, 175.26, refat=(76.2, 173.99), valat=(76.2, 176.53))
res('R73', '4.7K', 'C23162', 72.39, 180.34, refat=(76.2, 179.07), valat=(76.2, 181.61))
res('R74', '2.2k', 'C4190', 72.39, 185.42, refat=(76.2, 184.15), valat=(76.2, 186.69))
label('PFET_OUT', 72.39, 172.72, 90); gnd(72.39, 187.96)
wire(67.31, 177.8, 72.39, 177.8); label('EF_UVLO', 67.31, 177.8, 180); junction(72.39, 177.8)
wire(67.31, 182.88, 72.39, 182.88); label('EF_OVP', 67.31, 182.88, 180); junction(72.39, 182.88)
label('EF_UVLO', 90.17, 182.88, 180); label('EF_OVP', 90.17, 185.42, 180)
# SHDN not connected (internal pull-up), MODE link
items.append(NL.join(['  (no_connect (at 90.17 187.96) (uuid %s))' % U()]))
wire(87.63, 190.5, 90.17, 190.5); res('R75', '0R', 'C21189', 87.63, 193.04, refat=(83.82, 192.41), valat=(83.82, 194.95)); gnd(87.63, 195.58)
# ground pins
wire(97.79, 195.58, 100.33, 195.58); gnd(97.79, 195.58)
# output side: OUT 18-20 to +12V
wire(110.49, 172.72, 110.49, 175.26); wire(110.49, 175.26, 110.49, 177.8); wire(110.49, 172.72, 115.57, 172.72)
junction(110.49, 172.72); junction(110.49, 175.26)
pwr[0] += 1
sym('power:+12V', '#PWR0%d' % pwr[0], '+12V', 115.57, 172.72, 0, [('Footprint', ''), ('Datasheet', ''), ('Description', 'Power symbol creates a global label with name "+12V"'.replace('"', chr(92) + '"'))], ['1'])
# PGOOD to the buck enable (global label, as at R22)
items.append(NL.join(['  (global_label "PGOOD" (shape output) (at 110.49 180.34 0) (fields_autoplaced)', '    (effects (font (size 1.27 1.27)) (justify left))',
                      '    (uuid %s)' % U(), '    (property "Intersheetrefs" "${INTERSHEET_REFS}" (at 119.9462 180.34 0)',
                      '      (effects (font (size 1.27 1.27)) (justify left) hide)', '    )', '  )']))
# FLT not connected (open-drain fault output)
items.append(NL.join(['  (no_connect (at 110.49 182.88) (uuid %s))' % U()]))
# IMON, dVdT, ILIM
wire(110.49, 185.42, 125.73, 185.42); res('R77', '20k', 'C4184', 125.73, 187.96, refat=(129.54, 186.69), valat=(129.54, 189.23))
gnd(125.73, 190.5)
wire(110.49, 187.96, 118.11, 187.96); cap('C15', '100nF', 'C14663', 118.11, 190.5); gnd(118.11, 193.04)
wire(110.49, 190.5, 113.03, 190.5); res('R76', '4.7K', 'C23162', 113.03, 193.04, refat=(109.22, 193.67), valat=(109.22, 196.21)); gnd(113.03, 195.58)
items.append(NL.join(['  (text "12 V eFuse U3 TPS16630 (Rev D step 25, independent review M2): current limit 18/R76 = 3.8 A, off above 16.9 V (R72-R74),\\nsoft start C15 (25 ms), auto-retry with R75 fitted (leave R75 off for latch-off). IMON across R77: 0.56 V/A."'
                      ' (at 55.88 165.1 0)', '    (effects (font (size 1.27 1.27)) (justify left bottom))', '    (uuid %s)' % U(), '  )']))

end = t.rstrip().rfind(')')
t = t[:end].rstrip() + NL + NL + (NL + NL).join(items) + NL + ')' + NL
open(F, 'w', encoding='utf-8', newline='').write(t)
print('added U3 and %d other items; removed the bus segment (176.53, 38.1)-(195.58, 38.1)' % (len(items) - 1))
