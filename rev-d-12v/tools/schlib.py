"""Helpers for scripted KiCad schematic edits (kiutils): pin positions and dangling-item pruning."""
import math

R2 = lambda v: round(v, 2)


def ref(sym):
    return [p.value for p in sym.properties if p.key == 'Reference'][0]


def lib_for(sch, sym):
    name = sym.libName or sym.libId
    for ls in sch.libSymbols:
        if ls.libId == sym.libId:
            return ls
    raise KeyError(sym.libId)


def pin_positions(sch, sym):
    """{pin_number: (x, y)} in schematic coordinates, for the unit/style the symbol uses."""
    ls = lib_for(sch, sym)
    out = []
    a = math.radians(sym.position.angle or 0)
    for u in ls.units:
        if u.unitId not in (0, sym.unit) or u.styleId not in (0, 1):
            continue
        for p in u.pins:
            x, y = p.position.X, p.position.Y
            if sym.mirror == 'x':
                y = -y
            elif sym.mirror == 'y':
                x = -x
            xr = x * math.cos(a) - y * math.sin(a)
            yr = x * math.sin(a) + y * math.cos(a)
            out.append((p.number, (R2(sym.position.X + xr), R2(sym.position.Y - yr))))
    return out


def prune(sch):
    """Iteratively delete dangling wires and orphan power symbols. Returns a log."""
    log = []
    def anchors(skip_wire=None, skip_sym=None):
        a = {}
        def add(pt, kind):
            a.setdefault(pt, []).append(kind)
        for s in sch.schematicSymbols:
            if s is skip_sym:
                continue
            for _, pt in pin_positions(sch, s):
                add(pt, 'pin')
        for l in sch.labels + sch.globalLabels + sch.hierarchicalLabels:
            add((R2(l.position.X), R2(l.position.Y)), 'label')
        for n in sch.noConnects:
            add((R2(n.position.X), R2(n.position.Y)), 'nc')
        for w in sch.graphicalItems:
            if w.type == 'wire' and w is not skip_wire:
                for p in w.points:
                    add((R2(p.X), R2(p.Y)), 'wire')
        return a
    def interior(pt, skip_wire):
        for w in sch.graphicalItems:
            if w.type != 'wire' or w is skip_wire:
                continue
            p, q = w.points
            if p.X == q.X == pt[0] and min(p.Y, q.Y) < pt[1] < max(p.Y, q.Y):
                return True
            if p.Y == q.Y == pt[1] and min(p.X, q.X) < pt[0] < max(p.X, q.X):
                return True
        return False
    while True:
        changed = False
        for w in [g for g in sch.graphicalItems if g.type == 'wire']:
            a = anchors(skip_wire=w)
            for p in w.points:
                pt = (R2(p.X), R2(p.Y))
                if pt not in a and not interior(pt, w):
                    sch.graphicalItems.remove(w)
                    log.append(('wire', [(R2(q.X), R2(q.Y)) for q in w.points]))
                    changed = True
                    break
        for s in list(sch.schematicSymbols):
            if not s.libId.startswith('power:'):
                continue
            a = anchors(skip_sym=s)
            ok = all((pt in a) or interior(pt, None) for _, pt in pin_positions(sch, s))
            if not ok:
                sch.schematicSymbols.remove(s)
                log.append(('power', ref(s)))
                changed = True
        if not changed:
            break
    def endcount(pt):
        return sum(1 for w in sch.graphicalItems if w.type == 'wire' for p in w.points if (R2(p.X), R2(p.Y)) == pt)
    for j in list(sch.junctions):
        pt = (R2(j.position.X), R2(j.position.Y))
        if endcount(pt) == 0 and not interior(pt, None):
            sch.junctions.remove(j)
    return log
