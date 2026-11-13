"""Rev D step 24 (independent review of 13 Nov 2026, blocker B2 / note N2): delete the 'Rotation Offset' fields that the remix
inherited from Rev-C1 parts it has since replaced. The field is a JLCPCB placement correction that the Fabrication-Toolkit (Rev-C1's
production tool) and now make_jlc.py add to the KiCad rotation, so a stale value turns the new part on the assembly line.
  D18      180   Rev-C1: B5819W. Now 1N4148W C81598, the same part as D20, which Rev-C1 placed with no offset.
  J4/J11   180   Rev-C1: JST PH 3-pin. Now 3.5 mm pluggable terminals, placement checked in JLCPCB's viewer with no offset.
  J5/J22   180   Rev-C1: JST PH 3-pin. Now 3.5 mm pluggable terminals (as above).
  J21      180   Rev-C1: JST PH 4-pin. Now a 3.5 mm pluggable terminal (as above).
  J1/J28   270   Rev-C1: 2x3 pin headers (J28 is a copy of J1). Now 3.5 mm pluggable terminals (as above).
  J6/J29   270   Rev-C1: 2x3 pin headers (J29 is a copy of J6). Now 3.5 mm pluggable terminals (as above).
The fields that are still right stay: C21/C23/C57 180, U2 90, U4 90, U9 270 (same corrections as in Rev-C1's production file).
Only the property blocks are cut out of the files; nothing else changes. Instances are found by the root sheet's UUID (some carry an
empty project name, sheets used twice list two paths); stale instance entries of other projects ("sendit") are ignored.
usage: sch_clear_rotation_offsets.py <schematic folder>"""
import sys, os, re
STALE = {'D18': '180', 'J4': '180', 'J11': '180', 'J5': '180', 'J22': '180', 'J21': '180', 'J1': '270', 'J28': '270', 'J6': '270', 'J29': '270'}
ROOT = re.search(r'\(uuid ([0-9a-f-]+)\)', open(os.path.join(sys.argv[1], 'brineomatic.kicad_sch'), encoding='utf-8').read()).group(1)


def close(t, i):
    """index of the ')' that closes the '(' at t[i]"""
    d = 0
    while True:
        c = t[i]
        if c == '"':
            i += 1
            while t[i] != '"': i += 2 if t[i] == chr(92) else 1
        elif c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return i
        i += 1


seen = {}
for fn in sorted(os.listdir(sys.argv[1])):
    if not fn.endswith('.kicad_sch'): continue
    path = os.path.join(sys.argv[1], fn)
    t = open(path, encoding='utf-8', newline='').read()
    cuts, i = [], 0
    while True:
        i = t.find('\n  (symbol (lib_id', i)
        if i < 0: break
        j = close(t, i + 3)
        blk = t[i:j + 1]
        refs = re.findall(r'\(path "/' + ROOT + r'[^"]*"\s+\(reference "([^"]+)"\)', blk)
        hit = [r for r in refs if r in STALE]
        if hit:
            assert sorted(hit) == sorted(refs), (fn, refs)
            k = blk.find('(property "Rotation Offset" ')
            assert k > 0 and blk.count('(property "Rotation Offset" ') == 1, (fn, refs)
            val = re.match(r'\(property "Rotation Offset" "([^"]*)"', blk[k:]).group(1)
            assert all(STALE[r] == val for r in refs), (fn, refs, val)
            a = i + blk.rfind('\n', 0, k)          # from the line break before the property ...
            if t[a - 1] == '\r': a -= 1
            b = i + close(blk, k) + 1               # ... to its closing parenthesis
            cuts.append((a, b))
            for r in refs: seen[r] = (fn, val)
        i = j
    if cuts:
        for a, b in reversed(cuts): t = t[:a] + t[b:]
        open(path, 'w', encoding='utf-8', newline='').write(t)
        print('%-24s %d field(s) removed' % (fn, len(cuts)))
assert set(seen) == set(STALE), sorted(set(STALE) - set(seen))
for r in sorted(seen): print('   %-4s %s  Rotation Offset %s removed' % (r, seen[r][0], seen[r][1]))
