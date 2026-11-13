# Parts check and consolidation options, 13 Nov 2026

Branch `rev-d-12v-labels`, step 21 (TMC2209 soldered, 160 x 90 mm). BOM `mfg/BOM-rev_d.csv`: 57 lines, 199 assembled parts + 2 dev-board sockets.

## 1. What has been checked

| Check | Result | How |
|---|---|---|
| Every BOM line exists at JLCPCB and is in stock | 57 of 57 found. Lowest stock: PSD12C 1,175, fuse holder C206887 1,577, 0.11R C327071 3,796 (need 5 to 10 each). | JLCPCB parts API, 13 Nov 2026 |
| Library type | 31 Basic, 26 Extended (6 of them flagged "preferred"). The October quote charged 14 Extended lines. | same |
| Board = schematic | Every pad net equals the schematic netlist; ERC 0 errors (step 17), DRC 0 unconnected. | KiCad 10 DRC with parity |
| Copper really connects | Every plug pin and standoff reaches every pad of its net. | `tools/trace_connectors.py` |
| BOM and CPL = schematic | 199 parts in each, none missing or extra (step 17 files; CPL updated for the 7 moved plugs). | script cross-check on step 18, same files here apart from U9 |
| Datasheet figures for the changed parts | Read from manufacturer PDFs on 31 Oct 2026 for AO3401A, AO3400A, RT7272B, TMC2209, 1N4148W and the Espressif guide (see `CHANGE_REGISTER.md`, evidence class DS). | earlier work |
| Through-hole part placement | Checked in JLCPCB's viewer on 31 Oct 2026 for the buzzer, electrolytics, inductor, fuse holder, terminals. | earlier work |

## 2. What has NOT been checked

- **No board has been built or powered.** Nothing here is a working-hardware result. `BRINGUP_TEST_PLAN.md` lists the 14 bench steps.
- Against Rev-C1 (433 running hours reported by its author) this board changes the supply stage, 26 part choices and the controller mounting. None of those changes has been tested.
- Datasheet gaps still open from October: SMBJ16CA manufacturer PDF, buzzer PDF (coil resistance), 3.3 V current budget of the dev board's regulator.
- Footprint against the physical part was not re-verified line by line in this round; JLCPCB's own DFM check runs only after an order is placed.
- No human has reviewed the layout.

## 3. Options to reduce the number of different parts

All Basic parts are free of line fees on Economic assembly, so merging two Basic values saves a BOM line but no money.
Money is only saved by removing a charged Extended line (US$3.09 each plus the part).

### 3a. Value merges, no layout change, no function change

| Change | Lines | Effect | Risk |
|---|---|---|---|
| R51 5.1k -> 4.7k (same line as R7, R8, R31, R61) | -1 | 3.3 V indicator LED 8 % brighter | none |
| R27 47k -> 20k (same line as R55, R58, R66, R68) | -1 | 12 V indicator LED about 0.5 mA instead of 0.2 mA | none |
| C33 22 uF 0603 -> 10 uF 0603 (same line as C9, C59) | -1 | less bulk on the 3.3 V rail next to the dev board, which has its own capacitors | low, untested |
| R5, R29 1.2k -> 1k (same line as R13 ...) | -1 | flow-meter pull-up to 5 V: 5.0 mA instead of 4.2 mA | check the flow sensor's output rating first |

Result: 57 -> 53 lines, cost unchanged.

### 3b. Features that could be left unpopulated if they are not used

| Feature | Parts | Charged Extended lines saved |
|---|---|---|
| I2C / Qwiic plug | J2 | 1 |
| RS-485 port | U10, D44, D45, R66-R69, C59, C60, J23 | 1 (PSD12C) |
| Buzzer | BZ1, D18, Q2, its resistors | 1 |
| Servo outputs | F2, J6, J29, D10-D12, R11, R12, C21 | 1 (polyfuse) |

Each is a decision about what the watermaker needs, not a parts optimisation. The footprints stay on the board.

### 3c. Looked at and not recommended

- One electrolytic type instead of two: C57 sits on the 12 V rail (up to 15 V); the 16 V part used on the 5 V rails has no margin there.
- One TVS family: SMBJ16CA, SMAJ5.0A, SMF30CA, PESD3V3L1BA, PSM712 and PSD12C protect different voltages and have different footprints.
- BAT54S -> BAV99 on the flow-meter inputs: the Schottky clamps the 5 V pulse to 3.3 V + 0.3 V; a silicon diode would let the pin reach about 4.0 V.
- 4-pin stepper plug as two 2-pin plugs: saves a line but needs a layout change and the closed-end bodies do not sit at one pitch.
- TMC2209 support parts (22 nF, 4.7 uF, 0.11R): values are set by the driver's datasheet.

## 4. JLCPCB Economic quote, 13 Nov 2026 (5 boards, top side, quote page only: nothing saved to cart, nothing ordered)

Files: `mfg/gerbers-rev_d_step21.zip`, `mfg/BOM-rev_d.csv`, `mfg/CPL-rev_d.csv`. JLCPCB detected a 4-layer board of 90 x 160 mm.
All 57 BOM lines matched and selected (the dev-board socket line U5A,U5B comes up unselected and was ticked by hand).
The seven moved top plugs sit on their outlines in JLCPCB's 2D placement viewer. Page defaults for everything else (green, 1.6 mm).

| Item | USD |
|---|---|
| PCB (engineering 25.00 + board 8.90) | 33.90 |
| Setup fee | 8.24 |
| Stencil | 1.55 |
| Components (57 lines) | 69.89 |
| Extended components fee (14 lines x 3.09) | 43.26 |
| SMT assembly | 4.12 |
| Hand-soldering labour | 3.61 |
| Manual assembly | 7.97 |
| **Total** | **172.54** |

US$34.51 per board, without shipping and without the five dev boards. The October quote for the 152.6 x 84.5 mm board was US$178.51.

