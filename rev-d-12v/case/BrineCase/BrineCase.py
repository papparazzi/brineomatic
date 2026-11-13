# Brineomatic Rev D-12V (step 23, 160 x 90 mm) - 3D-printable case, built in Autodesk Fusion with the Python API.
# Run from Fusion (Shift+S > Scripts) or through the ClaudeBridge add-in.
#
# Coordinates are board coordinates in mm: origin = board bottom-left corner seen from the component side,
# +x right, +y up the board. KiCad:  x = kicad_x - 26.6,  y = 96.5 - kicad_y.  z up from the case floor.
# Relays / RS485 / POWER plugs are on the y = 0 edge, the sensor plugs on y = 90, servo / TDS plugs on x = 160,
# the ESP32 dev board on the left with its USB end towards y = 0.
# Fusion's API works in cm, so every length goes through CM.
#
# Three printed parts, all support-free on a 0.4 mm nozzle:
#   base          floor down
#   cover         top face down (plug notches and the USB notch are open slots towards the parting line)
#   display clamp flat
import adsk.core, adsk.fusion, traceback, os

CM = 0.1
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() and 'ClaudeBridge' not in __file__ \
    else r'C:\Users\sascha\Documents\Claude CODE\lada-panas\brineomatic\repo\rev-d-12v\case\BrineCase'
OUT = os.path.join(HERE, '..', 'print')
F3D = os.path.join(HERE, '..', 'fusion', 'brineomatic_case_revD12V.f3d')
REF_STEP = os.path.join(HERE, '..', 'ref', 'brineomatic_step23_board.step')
SHOTS = os.path.join(HERE, '..', 'renders')
WITH_REF = False     # True: also import the KiCad board model and run an interference check (slow; run as a second job)

# ---------------------------------------------------------------- board facts (from the KiCad file, step 23)
BX, BY, PCB_T = 160.0, 90.0, 1.6
HOLES = ((4.0, 4.0), (4.0, 86.0), (156.0, 4.0), (156.0, 86.0))      # 4.22 mm plain holes, 152 x 82 pattern
HDR_H = 7.55            # terminal header height above the board (KiCad model)
FUSE_H = 11.5           # fuse holder, tallest soldered part (KiCad model)
PINS_BELOW = 4.0        # longest through-hole pin under the board (fuse holder, KiCad model)
# plug headers: (name, lo, hi) = extent of the header body along the edge (KiCad fab outline)
BOTTOM = (('RS485', 59.85, 71.85), ('RELAY 1', 72.90, 81.40), ('RELAY 2', 82.40, 90.90), ('RELAY 3', 91.96, 100.46),
          ('RELAY 4', 101.50, 110.00), ('RELAY 5', 111.06, 119.56), ('POWER', 121.56, 130.06))
TOP_ROW = (('PROD FLOW', 45.40, 57.40), ('BRINE FLOW', 59.80, 71.80), ('HI PRES', 74.20, 82.70), ('LO PRES', 85.10, 93.60),
           ('WATER TEMP', 96.00, 108.00), ('MOTOR TEMP', 110.40, 122.40), ('STEPPER', 124.80, 140.30))
EAST = (('PROD TDS', 26.61, 38.60), ('BRINE TDS', 40.91, 52.91), ('SERVO 2', 55.20, 67.20), ('SERVO 1', 69.50, 81.51))
# dev board (ESP32-S3-DevKitC-1): socket rows at x 11.40 and 34.26, outline x 10.06..35.60, y 4.61..67.66, USB end at y 4.61
DEV_X0, DEV_X1, DEV_Y0 = 10.06, 35.60, 4.61
DEV_SPACER = 2.5        # header plastic of the dev board resting on the 8.5 mm sockets (assumed as on the bilge alarm; not measured)

# ---------------------------------------------------------------- display facts (seller drawing, see ../DISPLAY_2.42_OLED.md; NOT measured)
D_PCB_W, D_PCB_H = 70.08, 48.04
D_GLASS_W, D_GLASS_H = 62.64, 39.18
D_VIS_W, D_VIS_H = 57.80, 29.76
D_GLASS_ABOVE_PCB = 4.29        # 5.29 total - 1.00 board
D_ACTIVE_UP = 3.1               # active area centre above the glass centre (scaled from the drawing, +-0.4)
D_CX, D_CY = 84.0, 45.0         # display centre on the cover: right of the dev board (x < 35.6), clamp screws left of the fuse holder (x > 126.5)

# ---------------------------------------------------------------- print parameters (0.4 mm nozzle)
WALL = 2.0              # walls, floor, ceiling: 5 perimeters / 10 layers at 0.2
CLR = 0.6               # gap between board edge and inner wall
STANDOFF_TOP = WALL + PINS_BELOW + 2.0      # board underside 6.0 above the floor's top face -> z 8.0
PCB_TOP = STANDOFF_TOP + PCB_T              # 9.6
SPLIT = PCB_TOP                             # base wall ends level with the board top; plugs and cables leave above it
DEV_TOP = PCB_TOP + 8.5 + DEV_SPACER + 1.6 + 3.3      # tallest dev-board part (USB shell)
CEIL_IN = DEV_TOP + 3.0                     # 3 mm of air above the dev board
TOP = CEIL_IN + WALL
NOTCH_H = 12.0          # plug notch height above the board: header 7.55 + 4.45 for the plug's screw heads (plug not measured)
NOTCH_SIDE = 0.4        # each side of a header body
FIN_MIN = 1.2           # thinnest wall left between two notches (3 perimeters); closer plugs share one notch
USB_W, USB_H = 24.0, 7.2                    # one notch for both USB plugs; top 7.2 above the dev board's underside (connector centre +3.5 for the plug's grip)
R_I, R_O = 1.2, 3.2
IX0, IX1, IY0, IY1 = -CLR, BX + CLR, -CLR, BY + CLR
OX0, OX1, OY0, OY1 = IX0 - WALL, IX1 + WALL, IY0 - WALL, IY1 + WALL

# M3 heat-set insert (Ruthex / Voron M3 x 5 x 4): pilot 4.4, depth 4.8
INS_D, INS_DEPTH, BOSS_D = 4.4, 4.8, 7.6
SCREW_CLR_D, CBORE_D, TUBE_D = 3.4, 6.0, 8.0
SCREW_L, SCREW_ENGAGE = 20.0, 3.5             # M3 x 20 closing screws, 3.5 mm into the 4 mm insert
CBORE_H = TOP - (STANDOFF_TOP + SCREW_L - SCREW_ENGAGE)      # counterbore depth that makes that screw length fit (6.0)
LUG_W, LUG_L, LUG_T, LUG_HOLE = 14.0, 12.0, 4.0, 4.5      # four screw-down lugs on the base
# display mount
POCKET_D = 1.2                              # glass sinks this far into the ceiling; 0.8 mm lip frames the window
D_BOSS_X, D_BOSS_Y = D_PCB_W / 2 + 0.4 + 3.4, 15.0          # clamp bosses left and right of the display board
D_PCB_BACK = CEIL_IN - (D_GLASS_ABOVE_PCB - POCKET_D) - 1.0  # z of the display board's back face (cover upright)
CLAMP_T, CLAMP_LAP = 2.4, 1.8

app = adsk.core.Application.get()
tbm = adsk.fusion.TemporaryBRepManager.get()


def P(x, y, z): return adsk.core.Point3D.create(x * CM, y * CM, z * CM)
def V(x, y, z): return adsk.core.Vector3D.create(x, y, z)


def box(x0, x1, y0, y1, z0, z1):
    obb = adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), V(1, 0, 0), V(0, 1, 0),
                                                 (x1 - x0) * CM, (y1 - y0) * CM, (z1 - z0) * CM)
    return tbm.createBox(obb)


def cyl(x, y, z0, z1, d): return tbm.createCylinderOrCone(P(x, y, z0), d / 2 * CM, P(x, y, z1), d / 2 * CM)
def add(a, b): tbm.booleanOperation(a, b, adsk.fusion.BooleanTypes.UnionBooleanType)
def sub(a, b): tbm.booleanOperation(a, b, adsk.fusion.BooleanTypes.DifferenceBooleanType)


def rr(x0, x1, y0, y1, z0, z1, r):
    b = box(x0 + r, x1 - r, y0, y1, z0, z1)
    add(b, box(x0, x1, y0 + r, y1 - r, z0, z1))
    for cx in (x0 + r, x1 - r):
        for cy in (y0 + r, y1 - r):
            add(b, cyl(cx, cy, z0, z1, 2 * r))
    return b


def build_base():
    b = rr(OX0, OX1, OY0, OY1, 0, SPLIT, R_O)
    sub(b, rr(IX0, IX1, IY0, IY1, WALL, SPLIT + 1, R_I))
    for x, y in HOLES:                               # board posts with heat-set inserts; the closing screws end here
        add(b, cyl(x, y, WALL - 0.1, STANDOFF_TOP, BOSS_D))
        sub(b, cyl(x, y, STANDOFF_TOP - INS_DEPTH, STANDOFF_TOP + 1, INS_D))
    for sx, x, ys in ((-1, OX0, (20.0, 70.0)), (1, OX1, (12.0, 85.5))):     # screw-down lugs, flush with the floor; east ones beside the plug row
        for y in ys:
            x0, x1 = (x - LUG_L, x + 1.0) if sx < 0 else (x - 1.0, x + LUG_L)
            add(b, rr(x0, x1, y - LUG_W / 2, y + LUG_W / 2, 0, LUG_T, 2.0))
            sub(b, cyl(x + sx * LUG_L * 0.55, y, -1, LUG_T + 1, LUG_HOLE))
    sub(b, rr(IX0, IX1, IY0, IY1, WALL, SPLIT + 1, R_I))   # lugs must not reach into the cavity
    for x, y in HOLES:
        add(b, cyl(x, y, WALL - 0.1, STANDOFF_TOP, BOSS_D))
        sub(b, cyl(x, y, STANDOFF_TOP - INS_DEPTH, STANDOFF_TOP + 1, INS_D))
    return b


def cbore(c, x, y):
    """M3 head counterbore with a 45 degree cone seat (prints top side down without a flat overhang)"""
    seat = TOP - CBORE_H
    r_in, r_head, r_out = SCREW_CLR_D / 2, 2.75, CBORE_D / 2
    z0 = seat - (r_head - r_in)
    z1 = z0 + (r_out - r_in)
    sub(c, tbm.createCylinderOrCone(P(x, y, z0), r_in * CM, P(x, y, z1), r_out * CM))
    sub(c, cyl(x, y, z1, TOP + 1, CBORE_D))


def notches(row):
    """notch extents for a row of plugs; neighbours that would leave a wall thinner than FIN_MIN share one notch"""
    out = []
    for name, lo, hi in sorted(row, key=lambda r: r[1]):
        lo, hi = lo - NOTCH_SIDE, hi + NOTCH_SIDE
        if out and lo - out[-1][1] < FIN_MIN:
            out[-1][1] = hi
        else:
            out.append([lo, hi])
    return out


def build_cover():
    c = rr(OX0, OX1, OY0, OY1, SPLIT, TOP, R_O)
    sub(c, rr(IX0, IX1, IY0, IY1, SPLIT - 1, CEIL_IN, R_I))
    # plug notches: open slots from the parting line upwards
    for lo, hi in notches(BOTTOM):
        sub(c, box(lo, hi, OY0 - 1, IY0 + 0.5, SPLIT - 1, PCB_TOP + NOTCH_H))
    for lo, hi in notches(TOP_ROW):
        sub(c, box(lo, hi, IY1 - 0.5, OY1 + 1, SPLIT - 1, PCB_TOP + NOTCH_H))
    for lo, hi in notches(EAST):
        sub(c, box(IX1 - 0.5, OX1 + 1, lo, hi, SPLIT - 1, PCB_TOP + NOTCH_H))
    # USB notch below the dev board's USB end (both ports)
    ucx = (DEV_X0 + DEV_X1) / 2
    usb_top = PCB_TOP + 8.5 + DEV_SPACER + USB_H
    sub(c, box(ucx - USB_W / 2, ucx + USB_W / 2, OY0 - 1, IY0 + 0.5, SPLIT - 1, usb_top))
    # closing-screw tubes through the board's corner holes
    for x, y in HOLES:
        add(c, cyl(x, y, PCB_TOP + 0.1, CEIL_IN + 0.1, TUBE_D))
        sub(c, cyl(x, y, PCB_TOP - 1, TOP + 1, SCREW_CLR_D))
        cbore(c, x, y)
    # display: window, glass pocket, clamp bosses
    wy = D_CY + D_ACTIVE_UP
    sub(c, rr(D_CX - D_VIS_W / 2 - 0.3, D_CX + D_VIS_W / 2 + 0.3, wy - D_VIS_H / 2 - 0.3, wy + D_VIS_H / 2 + 0.3, CEIL_IN - 1, TOP + 1, 1.0))
    sub(c, box(D_CX - D_GLASS_W / 2 - 0.3, D_CX + D_GLASS_W / 2 + 0.3, D_CY - D_GLASS_H / 2 - 0.3, D_CY + D_GLASS_H / 2 + 0.3, CEIL_IN - 1, CEIL_IN + POCKET_D))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = D_CX + sx * D_BOSS_X, D_CY + sy * D_BOSS_Y
            add(c, cyl(x, y, D_PCB_BACK, CEIL_IN + 0.1, BOSS_D))
            sub(c, cyl(x, y, D_PCB_BACK - 1, D_PCB_BACK + INS_DEPTH, INS_D))
    return c


def build_clamp():
    """Frame that presses on the edge of the display board from behind. Modelled in place (cover upright)."""
    z1, z0 = D_PCB_BACK, D_PCB_BACK - CLAMP_T
    # one piece, U-shaped: the top bar runs outside the display board (the pin header is inside it), the bottom stays open for the flex cable fold
    k = box(D_CX - D_BOSS_X - BOSS_D / 2, D_CX + D_BOSS_X + BOSS_D / 2, D_CY - D_PCB_H / 2 - 0.4, D_CY + D_PCB_H / 2 + 4.4, z0, z1)
    sub(k, box(D_CX - D_PCB_W / 2 + CLAMP_LAP, D_CX + D_PCB_W / 2 - CLAMP_LAP, D_CY - D_PCB_H / 2 + CLAMP_LAP, D_CY + D_PCB_H / 2 - CLAMP_LAP, z0 - 1, z1 + 1))
    sub(k, box(D_CX - 8.0, D_CX + 8.0, D_CY + D_PCB_H / 2 - CLAMP_LAP - 0.5, D_CY + D_PCB_H / 2 + 0.4, z0 - 1, z1 + 1))   # header pins and wires, top centre
    sub(k, box(D_CX - 9.0, D_CX + 9.0, D_CY - D_PCB_H / 2 - 1, D_CY - D_PCB_H / 2 + CLAMP_LAP + 0.5, z0 - 1, z1 + 1))     # flex cable fold, bottom centre
    for sx in (-1, 1):
        for sy in (-1, 1):
            sub(k, cyl(D_CX + sx * D_BOSS_X, D_CY + sy * D_BOSS_Y, z0 - 1, z1 + 1, SCREW_CLR_D))
    return k


def paint(design, body, name):
    try:
        lib = app.materialLibraries.itemByName('Fusion Appearance Library')
        ap = design.appearances.itemByName(name) or design.appearances.addByCopy(lib.appearances.itemByName(name), name)
        body.appearance = ap
    except Exception as e:
        print('paint failed', name, e)


def run():
    for i in range(app.documents.count - 1, -1, -1):          # close unsaved documents from earlier runs of this script
        try:
            d = app.documents.item(i)
            dz = adsk.fusion.Design.cast(d.products.itemByProductType('DesignProductType'))
            if dz and not d.isSaved and any(o.component.name == 'Case base' for o in dz.rootComponent.occurrences):
                d.close(False)
        except Exception:
            pass
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    root = design.rootComponent
    parts = (('Case base', build_base, 'Plastic - Matte (Black)'), ('Case cover', build_cover, 'Plastic - Matte (Gray)'),
             ('Display clamp', build_clamp, 'Plastic - Matte (Red)'))
    comps = {}
    for name, fn, look in parts:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = name
        body = occ.component.bRepBodies.add(fn())
        body.name = name
        comps[name] = occ.component
        paint(design, body, look)
        bb = body.boundingBox
        print('%-14s %.1f x %.1f x %.1f mm, %.1f cm3, %d faces' % (name, (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
                                                                   (bb.maxPoint.z - bb.minPoint.z) * 10, body.volume, body.faces.count))
    print('heights: board top z %.1f, dev board top z %.1f, ceiling inside z %.1f, case top z %.1f' % (PCB_TOP, DEV_TOP, CEIL_IN, TOP))
    print('closing screws: M3 x %d, head seat %.1f mm below the top face, %.1f mm of thread in the insert' % (SCREW_L, CBORE_H, SCREW_ENGAGE))
    print('display: board back at z %.1f, %.1f mm above the main board; fuse holder top is %.1f mm above the main board' % (
        D_PCB_BACK, D_PCB_BACK - CLAMP_T - PCB_TOP, FUSE_H))

    ents = adsk.core.ObjectCollection.create()
    for name in comps:
        ents.add(comps[name].bRepBodies.itemByName(name))
    if WITH_REF and os.path.exists(REF_STEP):
        im = app.importManager
        before = root.occurrences.count
        im.importToTarget(im.createSTEPImportOptions(os.path.normpath(REF_STEP)), root)       # into the ROOT component only
        ref = root.occurrences.item(root.occurrences.count - 1) if root.occurrences.count > before else None
        if ref:
            bb = ref.boundingBox
            zshift = PCB_TOP - (bb.minPoint.z * 10 + PINS_BELOW)          # lowest point of the model is the fuse holder pin, 4.0 below the board top
            m = adsk.core.Matrix3D.create()
            m.translation = V(0, 0, zshift * CM)
            ref.transform = m
            print('board model imported: bbox x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f, lifted by %.2f mm' % (
                bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10, zshift))
            ents.add(ref)
    res = design.analyzeInterference(design.createInterferenceInput(ents))
    print('interferences:', res.count)
    for i in range(min(res.count, 40)):
        it = res.item(i)
        b = it.interferenceBody.boundingBox
        print('  %s <-> %s  %.2f mm3  x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (
            it.entityOne.name, it.entityTwo.name, it.interferenceBody.volume * 1000,
            b.minPoint.x * 10, b.maxPoint.x * 10, b.minPoint.y * 10, b.maxPoint.y * 10, b.minPoint.z * 10, b.maxPoint.z * 10))

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(F3D), exist_ok=True)
    em = design.exportManager
    for name in comps:
        fn = name.lower().replace(' ', '_')
        o = em.createSTLExportOptions(comps[name].bRepBodies.itemByName(name), os.path.join(OUT, fn + '.stl'))
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(o)
        em.execute(em.createSTEPExportOptions(os.path.join(OUT, fn + '.step'), comps[name]))
    em.execute(em.createFusionArchiveExportOptions(os.path.normpath(F3D)))
    # screenshots: closed case, cover removed, cover from the inside
    try:
        os.makedirs(SHOTS, exist_ok=True)
        vp = app.activeViewport
        occs = dict((o.component.name, o) for o in root.occurrences)
        def shot(fn, eye, up=(0, 0, 1), hide=()):
            for n, o in occs.items():
                o.isLightBulbOn = n not in hide
            cam = vp.camera
            cam.target = P(80, 45, 15); cam.eye = P(*eye); cam.upVector = V(*up); cam.isFitView = True
            vp.camera = cam
            vp.refresh(); adsk.doEvents()
            vp.saveAsImageFile(os.path.join(SHOTS, fn), 1800, 1200)
        shot('case_closed_iso.png', (260, -140, 190))
        shot('case_closed_back_iso.png', (-100, 230, 190))
        shot('case_open_iso.png', (260, -140, 190), hide=('Case cover', 'Display clamp'))
        shot('case_open_top.png', (80, 45, 400), up=(0, 1, 0), hide=('Case cover', 'Display clamp'))
        shot('cover_inside.png', (200, -110, -170), hide=('Case base',) + tuple(n for n in occs if n not in ('Case base', 'Case cover', 'Display clamp')))
        for o in occs.values():
            o.isLightBulbOn = True
        print('screenshots written to', os.path.normpath(SHOTS))
    except Exception:
        print('screenshots failed: ' + traceback.format_exc())
    print('exported STL + STEP to', os.path.normpath(OUT), 'and', os.path.normpath(F3D))


try:
    run()
except Exception:
    print('FAILED\n' + traceback.format_exc())
    raise
