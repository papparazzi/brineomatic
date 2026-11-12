"""Rev D step 18, schematic side: TMC2209-LA chip symbol U9 -> BIGTREETECH TMC2209 V1.3 module symbol (same pin positions, so the
wiring stays), remove R57 R60 C48 C45 C47 R58 R59, then prune the wires, junctions, labels and power symbols left dangling.
usage: sch_stepper_socket.py <tmc2209.kicad_sch> <out.kicad_sch> [<root.kicad_sch> <root_out.kicad_sch>]   (plain Python 3, text-level edit)"""
import sys, re, math, uuid

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

def span(text, i):
    """end index (exclusive) of the s-expression starting at text[i] == '('"""
    d = 0; q = False; k = i
    while True:
        c = text[k]
        if q:
            if c == "\\": k += 1
            elif c == '"': q = False
        elif c == '"': q = True
        elif c == "(": d += 1
        elif c == ")":
            d -= 1
            if d == 0: return k + 1
        k += 1

def children(text, i):
    """spans of the direct children of the list starting at text[i]"""
    out = []; e = span(text, i); k = i + 1; q = False
    while k < e - 1:
        c = text[k]
        if c == '"':
            k += 1
            while text[k] != '"': k += 2 if text[k] == "\\" else 1
        elif c == "(":
            j = span(text, k); out.append((k, j)); k = j; continue
        k += 1
    return out

OLD_LIB, NEW_LIB = "Driver_Motor:TMC2209-LA", "brineomatic_local:BTT_TMC2209_V1.3"
# chip pin -> (module pad, name, type); chip pins not listed are dropped
PINMAP = {"2": ("1", "EN", "input"), "9": ("2", "MS1", "input"), "10": ("3", "MS2", "input"), "14": ("4", "RX/PDN_UART", "bidirectional"),
          "13": ("6", "CLK", "input"), "16": ("7", "STEP", "input"), "19": ("8", "DIR", "input"), "18": ("9", "GND", "power_in"),
          "15": ("10", "VIO", "power_in"), "1": ("11", "B2", "output"), "26": ("12", "B1", "output"), "24": ("13", "A1", "output"),
          "21": ("14", "A2", "output"), "29": ("15", "GND", "passive"), "22": ("16", "VM", "power_in"), "12": ("17", "INDEX", "output"),
          "11": ("18", "DIAG", "output")}
REMOVE = {"R57", "R60", "C48", "C45", "C47", "R58", "R59"}

# ------------------------------------------------------------ 1. library symbol
i = s.index('(symbol "%s"' % OLD_LIB); j = span(s, i); lib = s[i:j]
PIN = re.compile(r'\(pin (\w+) line \(at ([-\d.]+) ([-\d.]+) (\d+)\) \(length ([\d.]+)\)(?: hide)?\s*\(name "([^"]*)"[^\n]*\n\s*\(number "(\d+)"[^\n]*\n\s*\)')
pins = []
def repl(m):
    num = m.group(7)
    if num not in PINMAP: return ""
    pad, name, typ = PINMAP[num]; pins.append(pad)
    return ('(pin %s line (at %s %s %s) (length %s)\n          (name "%s" (effects (font (size 1.27 1.27))))\n          (number "%s" (effects (font (size 1.27 1.27))))\n        )'
            % (typ, m.group(2), m.group(3), m.group(4), m.group(5), name, pad))
u1 = lib.index('(symbol "TMC2209-LA_1_1"'); u1e = span(lib, u1)
unit = PIN.sub(repl, lib[u1:u1e])
assert sorted(pins, key=int) == sorted((v[0] for v in PINMAP.values()), key=int), pins
tx = ('(pin no_connect line (at -15.24 10.16 0) (length 2.54)\n          (name "TX" (effects (font (size 1.27 1.27))))\n          (number "5" (effects (font (size 1.27 1.27))))\n        )\n      ')
unit = unit[:-1].rstrip() + "\n        " + tx + ")"
lib = lib[:u1] + unit + lib[u1e:]
lib = lib.replace('"%s"' % OLD_LIB, '"%s"' % NEW_LIB).replace('"TMC2209-LA_', '"BTT_TMC2209_V1.3_')
lib = lib.replace('(property "Value" "TMC2209-LA"', '(property "Value" "BTT TMC2209 V1.3 module"')
s = s[:i] + lib + s[j:]

# ------------------------------------------------------------ 2. placed symbols
root = s.index("(kicad_sch")
def top():
    return [(a, b) for a, b in children(s, root)]
def ref_of(blk):
    m = re.search(r'\(property "Reference" "([^"]+)"', blk); return m.group(1) if m else None
cut = []
for a, b in top():
    blk = s[a:b]
    if not blk.startswith("(symbol (lib_id"): continue
    r = ref_of(blk)
    if r in REMOVE: cut.append((a, b, ""))
    elif r == "U9":
        assert OLD_LIB in blk
        n = blk.replace(OLD_LIB, NEW_LIB)
        n = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "BTT TMC2209 V1.3 module"', n)
        n = re.sub(r'\(property "Footprint" "[^"]*"', '(property "Footprint" "brineomatic_local:BTT_TMC2209_V1.3_Socket"', n)
        n = re.sub(r'\(property "Datasheet" "[^"]*"', '(property "Datasheet" "https://github.com/bigtreetech/BIGTREETECH-Stepper-Motor-Driver/tree/master/TMC2209/V1.3"', n)
        n = re.sub(r'\(property "Description" "[^"]*"', '(property "Description" "Plug-in stepper driver module (TMC2209), two 1x8 sockets + DIAG/INDEX, hand-fitted; not a JLCPCB assembly part"', n)
        for key in ("LCSC", "Rotation Offset"):
            k = n.index('(property "%s"' % key); n = n[:k] + n[span(n, k):].lstrip()
        k0 = n.index('(pin "'); k1 = n.index("(instances")
        n = n[:k0] + "".join('(pin "%d" (uuid %s))\n    ' % (p, uuid.uuid4()) for p in range(1, 19)) + n[k1:]
        cut.append((a, b, n))
assert len(cut) == len(REMOVE) + 1, len(cut)
for a, b, n in sorted(cut, reverse=True):
    s = s[:a] + n + (s[b:].lstrip("\n") if not n else s[b:])

# ------------------------------------------------------------ 3. prune what the removed parts left dangling
R = lambda v: round(float(v), 2)
def lib_pins():
    lp = {}
    ls = s.index("(lib_symbols")
    for a, b in children(s, ls):
        blk = s[a:b]; name = re.match(r'\(symbol "([^"]+)"', blk).group(1); pts = []
        for ua, ub in children(blk, 0):
            sub = blk[ua:ub]; m = re.match(r'\(symbol "[^"]*_(\d+)_(\d+)"', sub)
            if not m or m.group(2) not in ("0", "1"): continue
            pts += [(R(x), R(y)) for x, y in re.findall(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+)', sub)]
        lp[name] = pts
    return lp
def scan():
    lp = lib_pins(); items = {"wire": [], "junction": [], "label": [], "power": [], "pins": []}
    for a, b in top():
        blk = s[a:b]
        if blk.startswith("(wire"):
            p = re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', blk); items["wire"].append(((R(p[0][0]), R(p[0][1])), (R(p[1][0]), R(p[1][1])), a, b))
        elif blk.startswith("(junction"):
            m = re.search(r'\(at ([-\d.]+) ([-\d.]+)', blk); items["junction"].append(((R(m.group(1)), R(m.group(2))), a, b))
        elif blk.startswith(("(label", "(global_label", "(hierarchical_label")):
            m = re.search(r'\(at ([-\d.]+) ([-\d.]+)', blk); items["label"].append(((R(m.group(1)), R(m.group(2))), a, b, re.match(r'\(\w+ "([^"]*)"', blk).group(1)))
        elif blk.startswith("(symbol (lib_id"):
            m = re.match(r'\(symbol \(lib_id "([^"]+)"\) \(at ([-\d.]+) ([-\d.]+) (\d+)\)( \(mirror (\w)\))?', blk)
            X, Y, ang, mir = float(m.group(2)), float(m.group(3)), math.radians(float(m.group(4))), m.group(6)
            pts = []
            for x, y in lp[m.group(1)]:
                if mir == "x": y = -y
                elif mir == "y": x = -x
                pts.append((R(X + x * math.cos(ang) - y * math.sin(ang)), R(Y - (x * math.sin(ang) + y * math.cos(ang)))))
            r = ref_of(blk)
            if r.startswith("#"): items["power"].append((pts, a, b, r))
            items["pins"] += pts
    return items
def on(p, w):
    (x1, y1), (x2, y2) = w[0], w[1]
    if p in (w[0], w[1]): return False
    if abs((x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1)) > 1e-6: return False
    return min(x1, x2) - 1e-6 <= p[0] <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= p[1] <= max(y1, y2) + 1e-6
log = []
while True:
    it = scan(); kill = []
    junc = set(j[0] for j in it["junction"]); lab = set(l[0] for l in it["label"]); pinset = set(it["pins"])
    ends = {}
    for w in it["wire"]:
        for p in w[:2]: ends[p] = ends.get(p, 0) + 1
    for w in it["wire"]:
        for p in w[:2]:
            if p in pinset or p in lab or ends[p] > 1: continue
            if p in junc and any(on(p, o) for o in it["wire"]): continue
            kill.append((w[2], w[3], "wire %s-%s" % (w[0], w[1]))); break
    if not kill:
        for pts, a, b, r in it["power"]:
            if not any(p in ends or sum(1 for q in it["pins"] if q == p) > 1 for p in pts): kill.append((a, b, "power symbol " + r))
        for p, a, b in it["junction"]:
            if ends.get(p, 0) + sum(1 for o in it["wire"] if on(p, o)) * 2 + (p in pinset) < 3: kill.append((a, b, "junction %s" % (p,)))
        for p, a, b, name in it["label"]:
            if p not in ends and p not in pinset and not any(on(p, o) for o in it["wire"]): kill.append((a, b, "label %s %s" % (name, p)))
    if not kill: break
    for a, b, what in sorted(set(kill), reverse=True):
        s = s[:a] + s[b:].lstrip("\n"); log.append(what)
# sheet note: SPREAD is not on the module header; say what the module replaces
k = s.index('(text "SPREAD (with pull-down)'); ke = span(s, k); old = s[k:ke]
s = (s[:k] + '(text "U9 = BIGTREETECH TMC2209 V1.3 plug-in module\\nOn the module: 0.11R sense resistors, charge pump,\\n5VOUT capacitor, VREF trimmer.\\n'
     'Set the trimmer to 1.67 V (was R58/R59).\\nSPREAD is not brought out."' + old[old.index("\n    (at"):].replace("(at 196.85 123.19 0)", "(at 196.85 149.5 0)") + s[ke:])
open(dst, "w", encoding="utf-8", newline="\n").write(s)
if len(sys.argv) > 4:      # root sheet: drop the unused SPREAD sheet pin and its no-connect flag
    r = open(sys.argv[3], encoding="utf-8").read()
    for key in ('(pin "SPREAD" input (at 59.69 49.53 180)', '(no_connect (at 59.69 49.53)'):
        k = r.index(key); r = r[:k].rstrip() + r[span(r, k):]
    open(sys.argv[4], "w", encoding="utf-8", newline="\n").write(r)
print("removed symbols", sorted(REMOVE), "| pruned %d items:" % len(log))
for l in log: print("   ", l)
