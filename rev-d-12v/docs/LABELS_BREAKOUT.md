# Rev D step 19: pin labels, breakout pads, plug labels

13 Nov 2026. Branch `rev-d-12v-labels`, on top of `rev-d-12v` step 17 (217fe22). The TMC2209 stays **soldered on the board as in Rev-C1**;
the socketed-module variant (step 18) lives on branch `rev-d-12v-stepper-socket` and is not part of this branch.

**No net was changed.** Schematic, BOM and CPL are those of step 17. Untested; no human has reviewed the layout.

## What changed (`tools/pcb_labels_breakout.py`)

| Item | Detail |
|---|---|
| Dev-board pin labels | All 44 header positions of the ESP32-S3-DevKitC-1 are named on the front silkscreen (1.0 mm text), outside the two socket rows so they stay readable with the dev board plugged in. Names follow Espressif's v1.1 header table (3V3, RST, GPIO numbers, 5V, GND, TX, RX). |
| Breakout pads | A plated hole (1.0 mm hole, 1.6 mm pad, takes a standard pin or a wire) beside every dev-board pin the board does not use: RST, 3, 46, TX, RX, 38, 37, 36, 35, 0, 45, 20, 19, plus one 3V3 and one GND pad. 15 pads. Each has its name on the front and on the back. They are extra pads of U5 with the same pad number as the socket pin they belong to, joined to it by a 0.25 mm top-layer track, so the netlist is unchanged. |
| Board outline | West edge moved 3 mm out (x 34 -> 31) for the west label column. Board is now **155.6 x 84.5 mm** (was 152.6 x 84.5). Mounting holes did not move. |
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

This board is **12 V only (9-15 V)**, as the rest of `rev-d-12v`: 16 V TVS diodes, 30 V MOSFETs, P-FET reverse-polarity stage instead of the eFuse. It must not be connected to 24 V. The 12-24 V design is upstream Rev-C1.

## Verification

- KiCad 10 DRC with schematic parity (`baseline/rev_d_step19_drc.json`): 0 unconnected, 0 clearance, 0 shorts; nothing new against step 17 except 2 more silk-over-copper warnings; the 2 dangling-track warnings are gone.
- `tools/trace_connectors.py`: an independent walk over the copper (track ends, vias, pads, filled pours) from every pin of every plug. **Every pin reaches every other pad of its net** (0 unreached), on step 17 and on step 19.
- Renders: `rev_d_pcb_step19_top.png`, `rev_d_pcb_step19_bottom.png`. Gerbers: `mfg/gerbers-rev_d_step19.zip` exists only on the author's PC (`*.zip` is git-ignored in this repository); regenerate with `kicad-cli pcb export gerbers` and `export drill` (not uploaded to JLCPCB, not quoted; the 3 mm wider board may change the bare-board price slightly).

### Why tracks seem to "stop in the middle of nowhere" in a 3D or JLCPCB view

Those views show only the top copper, and the vias are covered by solder mask. A track that ends at a via continues on another layer.
`routing_J4_J11_all_layers.png` shows the PROD FLOW and BRINE FLOW plugs on all four layers: the signal pin leaves on inner layer 1, comes up through a via at the test point and reaches its resistors on the top layer;
the 5 V pin sits in a 5 V copper area on inner layer 2; the GND pin connects through the ground pours.

## Reproduce

    git show 217fe22:brineomatic/brineomatic.kicad_pcb > step17.kicad_pcb
    python rev-d-12v/tools/pcb_labels_breakout.py step17.kicad_pcb brineomatic/brineomatic.kicad_pcb
