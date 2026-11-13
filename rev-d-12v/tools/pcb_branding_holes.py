"""Rev D step 21: mounting holes to the four corners, dev-board type printed in the dev-board area, name / remix credits moved to
the top-left corner as horizontal text, large 12 V warning. No net change (the four standoffs stay on GND).
usage: pcb_branding_holes.py <step20.kicad_pcb> <out.kicad_pcb>      (KiCad 10 Python)"""
import sys
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
FPS = dict((f.GetReference(), f) for f in b.GetFootprints()); DRAW = list(b.GetDrawings()); TRACKS = list(b.GetTracks())
def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def text(s, x, y, h, w=None, th=None, ang=0, just="c", ko=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(P(x, y))
    t.SetTextSize(VECTOR2I(FromMM(w or h), FromMM(h))); t.SetTextThickness(FromMM(th or max(0.15, h * 0.15))); t.SetTextAngleDegrees(ang)
    t.SetHorizJustify({"l": pcbnew.GR_TEXT_H_ALIGN_LEFT, "r": pcbnew.GR_TEXT_H_ALIGN_RIGHT, "c": pcbnew.GR_TEXT_H_ALIGN_CENTER}[just])
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER); t.SetIsKnockout(ko); b.Add(t); return t
def track(net, pts, w=0.5):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FromMM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); b.Add(t)

# ---------------------------------------------------------------- 1. mounting holes: 4 mm in from each corner of the 160 x 90 outline (26.6..186.6 x 6.5..96.5)
HOLES = {"H1": (30.6, 10.5), "H2": (30.6, 92.5), "H3": (182.6, 10.5), "H4": (182.6, 92.5)}
old = {}
for ref, (x, y) in HOLES.items():
    fp = FPS[ref]; old[ref] = (round(ToMM(fp.GetPosition().x), 2), round(ToMM(fp.GetPosition().y), 2))
    fp.SetPosition(P(x, y))
gnd = b.FindNet("GND")
# three corners lie outside the ground pour (x from 42.8, y from 14.6): tie those standoffs to ground with a track
# (tracks start on the copper ring, 2.85 mm from the hole centre, not in the hole)
track(gnd, [(33.45, 10.5), (36.0, 10.5), (44.5, 19.0), (46.0, 19.0)], 0.6)
track(gnd, [(32.62, 94.52), (33.0, 94.9), (46.0, 94.9)], 0.6)
track(gnd, [(180.58, 12.52), (176.6, 16.5), (176.0, 17.5)], 0.6)          # to the GND pin of the SERVO 1 plug

# ---------------------------------------------------------------- 2. dev-board type, inside the socket outline (hidden once the dev board is fitted)
text("ESP32-S3-DevKitC-1-N16R8", 47.0, 60.4, 2.0, th=0.3, ang=90)
text("Espressif, board v1.1 (RGB LED on GPIO38)", 50.6, 60.4, 1.1, ang=90)
text("module ESP32-S3-WROOM-1-N16R8", 53.0, 60.4, 1.1, ang=90)
text("16 MB flash, 8 MB octal PSRAM", 55.4, 60.4, 1.1, ang=90)

# ---------------------------------------------------------------- 3. name and credits, top-left corner, horizontal
kill = [d for d in DRAW if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.F_SilkS and d.GetText() in ("BRINEOMATIC", "github.com/hoeken/brineomatic", "REV D 12V")]
assert len(kill) == 3, len(kill)
frame = []                                   # the thin silkscreen frame that surrounded the old vertical credits
for d in DRAW:
    if d.GetClass() == "PCB_SHAPE" and d.GetLayer() == pcbnew.F_SilkS:
        bb = d.GetBoundingBox()
        if 162 < ToMM(bb.GetLeft()) and ToMM(bb.GetRight()) < 169.5 and 58 < ToMM(bb.GetTop()) and ToMM(bb.GetBottom()) < 90: frame.append(d)
print("old credit frame items removed:", len(frame))
kill += frame
X = 36.2
text("BRINEOMATIC", X, 9.9, 2.6, th=0.35, just="l", ko=True)
text("REMIX REV D-12V", X, 13.6, 1.5, th=0.22, just="l", ko=True)
text("github.com/papparazzi/brineomatic", X, 16.3, 1.0, just="l")
text("based on Brineomatic Rev C1 by hoeken", X, 18.6, 1.0, just="l")
text("github.com/hoeken/brineomatic", X, 20.6, 1.0, just="l")

# ---------------------------------------------------------------- 4. supply warning: beside the fuse and above the power plug
text("12V ONLY - NO 24V", 165.6, 75.2, 2.0, th=0.32, ang=90, ko=True)
text("12V ONLY", 63.8, 90.3, 2.8, th=0.42, just="l", ko=True)                    # second, larger one in the free area left of the RS485 plug
text("9-15V DC   NO 24V", 63.8, 93.9, 1.3, th=0.2, just="l", ko=True)

for k in kill: b.Remove(k)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
print("holes moved:", dict((r, (old[r], HOLES[r])) for r in HOLES))
