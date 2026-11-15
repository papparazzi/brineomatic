# Rev D steps 19 to 21: pin labels, breakout pads, plug labels, 160 x 90 mm board, corner holes, credits, 12 V warning

13 Nov 2026. Branch `rev-d-12v-labels`, on top of `rev-d-12v` step 17 (217fe22). The TMC2209 stays **soldered on the board as in Rev-C1**;
the socketed-module variant (step 18) lives on branch `rev-d-12v-stepper-socket` and is not part of this branch.

**No net was changed.** Schematic, BOM and CPL are those of step 17. Untested; no human has reviewed the layout.

## What changed (`tools/pcb_labels_breakout.py`)

| Item | Detail |
|---|---|
| Dev-board pin labels | All 44 header positions of the ESP32-S3-DevKitC-1 are named on the front silkscreen (1.0 mm text), outside the two socket rows so they stay readable with the dev board plugged in. Names follow Espressif's v1.1 header table (3V3, RST, GPIO numbers, 5V, GND, TX, RX). |
| Breakout pads | A plated hole (1.0 mm hole, 1.6 mm pad, takes a standard pin or a wire) beside every dev-board pin the board does not use: RST, 3, 46, TX, RX, 38, 37, 36, 35, 0, 45, 20, 19, plus one 3V3 and one GND pad. 15 pads. Each has its name on the front and on the back. They are extra pads of U5 with the same pad number as the socket pin they belong to, joined to it by a 0.25 mm top-layer track, so the netlist is unchanged. |
| Board outline (step 20, `tools/pcb_resize_160x90.py`) | **160.0 x 90.0 mm** (step 17: 152.6 x 84.5). +7.4 mm on the west (dev-board) side, +5.5 mm at the top. South and east edges did not move. The seven top-edge plugs (PROD FLOW ... STEPPER) moved up 5.5 mm with the edge so they stay at the board edge. At each old pin position a plated hole (1.2 mm pad, 0.6 mm hole) remains, so every existing track and plane connection ends where it did; a top-layer and a bottom-layer track (1.0 mm for supplies and motor phases, 0.5 mm for sensor signals) join it to the moved pin. CPL updated for the seven plugs (Mid Y -22.6 -> -17.1). |
| Plug labels | Sensor, servo, TDS and stepper plugs carry their name in the knockout style (white box, clear letters) directly at the plug, with a legend for every pin: PROD FLOW, BRINE FLOW (GND S 5V), HI PRES, LO PRES (S 12V), WATER TEMP, MOTOR TEMP (GND S 3V3), STEPPER (B2 B1 A1 A2), SERVO 1, SERVO 2, BRINE TDS, PROD TDS (GND 5V S). The old block labels 11 mm away from the plugs and the plain "- + S" marks were removed; the connector J-numbers are hidden on the silkscreen. |
| Already in that style, unchanged | POWER (12V GND), RS485 (A B GND), RELAY 1-5, I2C. |
| Dead copper removed | Two stubs that step 17's DRC reported as dangling (a 4 mm +12V stub on the back near C57, an 18 um sliver at U9). |

## Limits, stated plainly

- **Four breakout pads sit inside the socket rows, under the dev board: RX, 38, 35, 0.** Inner-layer tracks block the outside position there. They can be soldered from the back, or from the front with the dev board unplugged.
- **GPIO 35, 36, 37 are not usable on the specified N16R8 dev board** (Espressif: used by the octal memory). The pads are there for boards with other modules.
- **GPIO 0, 3, 45, 46 are strapping pins, 19/20 are the dev board's USB, TX/RX its UART port, RST its reset.** Usable for extensions only with that in mind.
- **RELAY 1-5 have no per-pin legend.** There is no free silkscreen between the label, the flyback diodes and the plug. Pin 1 (left, marked by the triangle) is +12V, pin 2 is the switched return.
- **I2C (JST-SH, 1 mm pitch)** has its name only.
- 1.0 mm text is JLCPCB's recommended minimum; the 0.9 mm legends are slightly below it and may print a little soft.

## Supply voltage

This board is **12 V only (9-15 V)**, as the rest of `rev-d-12v`: 16 V TVS diodes, 30 V MOSFETs, a P-FET reverse-polarity stage and, since step 25, a 12 V eFuse (TPS16630) after it instead of Rev-C1's TPS26630: current limit about 3.8 A, off above 16.9 V (`EFUSE.md`). It must not be connected to 24 V. The 12-24 V design is upstream Rev-C1.

## Verification

- KiCad 10 DRC with schematic parity (`baseline/rev_d_step27_drc.json`, all severities): 0 unconnected, 0 clearance, 0 shorts; against step 17 only silkscreen warnings changed (silk over copper 12 -> 13, silk overlap 23 -> 31: the plug names touch the pin-1 triangles of the plug footprints) and the 2 dangling-track warnings are gone.
- `tools/trace_connectors.py`: an independent walk over the copper (track ends, vias, pads, filled pours) from every pin of every plug. **Every pin reaches every other pad of its net** (0 unreached), on step 17, 19, 20 and 21 (the four standoffs included), and on steps 23 to 27.
- Renders: `rev_d_pcb_step26_top.png`, `rev_d_pcb_step26_bottom.png`. Gerbers and drill files: `mfg/gerbers-rev_d_step26.zip` (step 27 leaves the gerbers unchanged apart from dates), made with `tools/make_gerbers.py` (`.gitignore` now lets zip files in `rev-d-12v/mfg/` through). Not uploaded to JLCPCB, **not quoted**: the board area grew 11.7 % against step 17, so the bare-board price may rise slightly.

### Why tracks seem to "stop in the middle of nowhere" in a 3D or JLCPCB view

Those views show only the top copper, and the vias are covered by solder mask. A track that ends at a via continues on another layer.
`routing_J4_J11_all_layers.png` shows the PROD FLOW and BRINE FLOW plugs on all four layers: the signal pin leaves on inner layer 1, comes up through a via at the test point and reaches its resistors on the top layer;
the 5 V pin sits in a 5 V copper area on inner layer 2; the GND pin connects through the ground pours.

## Reproduce

    git show 217fe22:brineomatic/brineomatic.kicad_pcb > step17.kicad_pcb
    python rev-d-12v/tools/pcb_labels_breakout.py step17.kicad_pcb step19.kicad_pcb
    python rev-d-12v/tools/pcb_resize_160x90.py step19.kicad_pcb step20.kicad_pcb
    python rev-d-12v/tools/pcb_branding_holes.py step20.kicad_pcb step21.kicad_pcb
    python rev-d-12v/tools/pcb_antenna_keepout.py step21.kicad_pcb step22.kicad_pcb
    python rev-d-12v/tools/pcb_power_plug_align.py step22.kicad_pcb step23.kicad_pcb
    python rev-d-12v/tools/pcb_review_fix_power.py step23.kicad_pcb step24.kicad_pcb
    python rev-d-12v/tools/pcb_add_efuse.py step24.kicad_pcb rev_d.xml step25.kicad_pcb
    python rev-d-12v/tools/pcb_servo_power.py step25.kicad_pcb step26.kicad_pcb
    python rev-d-12v/tools/pcb_c57_revert.py step26.kicad_pcb brineomatic/brineomatic.kicad_pcb

Step 24 also edits the schematic and regenerates the CPL; those commands are in `REVIEW_FIXES.md`. Step 25 needs the step-25 schematic
and its netlist (`rev_d.xml`) first and regenerates the BOM, CPL and gerbers; those commands are in `EFUSE.md`. Step 26 changes copper
only (gerbers: `SERVO_POWER.md`). Step 27 changes C57's value text on the board and C57 in the schematic; its commands are in the step-27 section below. Checked on 14 Nov 2026: this chain gives the step-25 board and the step-26 board item for item, zone
fills included; only the random ids of added items differ (the step-24 board in between differs from the committed step-24 board only
in zone fill, at most 2.4 mm2 per layer).

## Known cosmetic points of the resize

- The new strips at the top and on the west side carry no ground pour (the pour outlines were not enlarged).
- The plug courtyards reach the top edge exactly as before (the plugs moved by the same 5.5 mm as the edge).

## Step 21 (`tools/pcb_branding_holes.py`): corner holes, dev-board type, credits, 12 V warning

| Item | Detail |
|---|---|
| Mounting holes | H1-H4 moved to the four corners, each 4.0 mm in from both edges: (30.6, 10.5), (30.6, 92.5), (182.6, 10.5), (182.6, 92.5) in KiCad coordinates. **Hole pattern is now 152.0 x 82.0 mm** (was 98.8 x 77.2 / 60.3, not rectangular). The standoff pads stay on GND; three of them lie outside the ground pour and are tied to ground with a 0.6 mm top-layer track. The alignment holes H5, H6 did not move. |
| Dev-board type | Printed inside the socket outline (covered once the dev board is fitted): "ESP32-S3-DevKitC-1-N16R8", "Espressif, board v1.1 (RGB LED on GPIO38)", "module ESP32-S3-WROOM-1-N16R8", "16 MB flash, 8 MB octal PSRAM". |
| Name and credits | Top-left corner, horizontal: BRINEOMATIC / REMIX REV D-12V / github.com/papparazzi/brineomatic / based on Brineomatic Rev C1 by hoeken / github.com/hoeken/brineomatic. The vertical name, link and "REV D 12V" beside the fuse were removed. |
| 12 V warning | "12V ONLY" (2.8 mm) with "9-15V DC   NO 24V" left of the RS485 plug, and "12V ONLY - NO 24V" (2.0 mm, vertical) beside the fuse next to the power plug. Both in the knockout style. |

No net change. DRC with parity: nothing new against step 20. Trace: 0 unreached.

## Step 22: antenna keep-out

No copper fill under the Wi-Fi antenna end of the dev board; see `DEVBOARD_PIN_AUDIT.md` section 3. No net change. The JLCPCB quote of 13 Nov 2026 (US$172.54) was made with the step-21 gerbers; the keep-out changes copper fill only.

## Step 23: power plug aligned with the other bottom plugs

Rev-C1 had a larger 5.08 mm terminal for the supply; its front was on the same line as the 3.5 mm plugs next to it (KiCad y 95.55).
The October change to a 3.5 mm terminal kept the old pin position, so the smaller body ended 2.0 mm further inside the board (front at y 93.55).
In a case that plug would have sat 2 mm deeper than its neighbours. `tools/pcb_power_plug_align.py` moves J10 2.0 mm towards the edge and
extends its 2.0 mm wide supply track by the same amount; the POWER label moves with it. No net change. DRC: nothing new. Trace: 0 unreached.
CPL: J10 Mid Y -85.5 -> -87.5.

Front of the plug bodies from the board edge after this step: bottom row 0.95 mm, top row 2.55 mm, right side 2.55 mm (the last two as designed in October).
The JLCPCB quote of 13 Nov 2026 predates steps 22 and 23.

## Step 24: the independent review's two blockers

The input power path from the fuse to the reverse-polarity MOSFETs and on to +12V is rebuilt with wide copper (B1), and the CPL now carries
JLCPCB's rotation corrections, as Rev-C1's did (B2). No net change, no part change, BOM unchanged; the CPL and ten stale schematic
`Rotation Offset` fields change. Detail, numbers and the remaining open findings: `REVIEW_FIXES.md`.

## Step 25: eFuse back (review finding M2)

A 12 V eFuse (TI TPS16630, U3) goes back between the reverse-polarity MOSFETs and the +12V rail, where Rev-C1 had its TPS26630:
current limit, overvoltage cut-off, soft start. Nine parts added; the MOSFET-source copper becomes the new net PFET_OUT; D49, C22, R22,
TP41 and the "FUSE 5x20" label move; ten references are hidden. DRC: nothing new (252 against 253). Trace: 0 unreached.
Detail and numbers: `EFUSE.md`.

## Step 26: servo supply on wide top-layer copper (review finding M1)

The servo 5 V supply (5V_HIGH_POWER) from D10 to J6 pin 2 and J29 pin 2 now runs on the top layer, 1.8-4.0 mm wide, instead of
0.25 mm track mostly on inner layer In1: 13 mOhm from F2 to each servo terminal instead of 161-230 mOhm. The 4.0 mm run uses the empty
band below the top plug row. No net or part change; the TP42 via and one ground via moved slightly. DRC: identical to step 25.
Trace: 0 unreached. Detail and numbers: `SERVO_POWER.md`.

## Step 27: C57 back to Rev-C1's 100 uF (review finding m6)

C57, the bulk capacitor of the TMC2209 supply on +12V, goes back from 47 uF/50 V (C3349) to Rev-C1's 100 uF/35 V (C2836442). The
October swap was meant to save a line fee, but JLCPCB charges the C3349 line too, and no 100 uF SMD electrolytic at JLCPCB is
fee-free; the swap only halved the capacitance. Same footprint and place: copper and silkscreen do not change (gerbers identical to
step 26 apart from dates). The BOM changes in one line; the CPL does not change. DRC: same counts as step 26. Trace: 0 unreached.
Detail and numbers: `CHANGE_REGISTER.md` section M.

    python rev-d-12v/tools/sch_c57_revert.py brineomatic
    python rev-d-12v/tools/pcb_c57_revert.py step26.kicad_pcb brineomatic/brineomatic.kicad_pcb
    kicad-cli sch export netlist --format kicadxml -o rev_d.xml brineomatic/brineomatic.kicad_sch
    KICAD_CLI=<kicad-cli> python rev-d-12v/tools/make_jlc.py rev_d.xml brineomatic/brineomatic.kicad_pcb rev-d-12v/mfg
    python rev-d-12v/tools/audit_changes.py rev_c1.xml rev_d.xml rev-d-12v/docs/CHANGE_AUDIT.md

`rev_c1.xml` is the netlist of the Rev-C1 tag's schematic (`kicad-cli sch export netlist` on a `git archive Rev-C1` copy).
