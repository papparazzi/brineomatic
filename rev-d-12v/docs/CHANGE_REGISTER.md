# Rev D (12 V) change register vs Rev-C1

Baseline: github.com/hoeken/brineomatic tag **Rev-C1**. Envelope: ~3 A board (3.15 A time-lag fuse, 3 A per output), 12 V house bus (9-15 V; 14.8 V max charge voltage).
Goals: see `GOALS.md`. Complete machine-generated diff: `CHANGE_AUDIT.md` (180 parts identical, 127 changed/added/removed, **0 unexplained**; 0 net differences involving a part that is not listed below).

**Evidence classes** used in the "Due diligence" column
- **LIVE** - checked on jlcpcb.com / lcsc.com in this project (stock, Basic/fee-free status, price).
- **CALC** - my own arithmetic, shown in `VETTING.md` or here.
- **DS** - number taken from a manufacturer datasheet from memory of the part family; **must be re-confirmed against the PDF before an order** (listed under "Open items").
- **SIM/BENCH** - none yet. **No bench test has been done (V6 open).**

Risk class: R0 none, R1 re-rating/value change, R2 different part same function, R3 function/architecture change.

## A. Architecture and mechanical changes (R3)

| ID | Change | Lost / gained | Due diligence | Open |
|---|---|---|---|---|
| A1 | TPS26630 eFuse U3 + Q3 (CSD19537) + Q8 + R21, R72-R77, C15, TP50-52 removed. Added 2x AO3401A P-FET (Q9,Q10; **drain on the battery side PRE_24, source on the +12V rail**), R78 10k gate-to-GND, D56 BZT52C10 gate clamp (source-gate, cathode on the rail). | Lost: UVLO/OVP, active 4 A limit, soft-start, reverse-current block. Kept: reverse-polarity block, F1 3.15 A, TVS. The firmware never read IMON/FLT/PGOOD (test points only). | CALC: two FETs in parallel ~24 mOhm -> 74 mV / 0.23 W at 3.15 A (Rds 47 mOhm @ Vgs -10 V, DS). One FET (4 A) would be over-rated because the fuse carries 4.25 A for up to an hour -> two. Zener holds |Vgs| to 10 V (AO3401A abs max 12 V, DS). Reverse 14.8 V: drain -14.8 V, source ~0 V, gate 0 V -> Vgs ~0, body diode blocks. **A first version had the FET backwards (source on battery side: body diode would conduct on reverse and blow F1); found on review, fixed.** | Confirm AO3401A Vgs/Id/Rds on the Alpha&Omega PDF; bench: reverse -12 V and -15 V on a current-limited supply, FET temperature at 3 A / 30 min. RT7272 EN now has no supervisor (buck starts as soon as VIN rises; relies on the RT7272 internal UVLO). |
| A2 | ESP32-S3-WROOM module U5 + USB-C J19, boot/reset SW1/SW2, USBLC6 U6, WS2812 D40, level shifter U8, 3V3 LDO U7, USB/EN/boot support parts (C37-C43, R43-R53, D36-D38, FB1, J20, J24, TP27-29) removed. Added 2x 1x22 sockets (U5) for an **ESP32-S3-DevKitC-1 v1.1**, D57 SS34 in series with the dev-board 5V pin. | Lost: on-board USB-C and own 3V3 regulator. Gained: replaceable controller, Economic-eligible, 8 fewer paid lines. | Every GPIO mapped against the Espressif v1.1 pin table (script check; same pin numbers keep all 24 net labels). **+3.3V for all loads now comes from the dev-board LDO** (CALC load not yet summed). D57: Espressif says USB and the 5V pin must not be used together; the diode gives ~0.4 V drop (dev board sees ~4.6 V). v1.0 boards have the RGB LED on GPIO48 = RS485_DI conflict, so **only v1.1 is supported**. | Sum the 3V3 load vs the dev-board LDO rating; check 5 V pin at 4.6 V; test USB + 12 V simultaneously (no back-feed). |
| A3 | Board outline: 106 x 63.5 mm -> **135 x 84.5 mm** (x 34-169, y 12-96.5). +29 mm west for the dev-board strip, +17 mm along the top for the screw-terminal strip, +4 mm at the bottom edge for J23. Mounting holes H1, H2, H4 moved (66.6,32.6 -> 66.6,15.7; 66.6,88.9 -> 66.6,92.9; 165.4,88.9 -> 165.4,92.9); H3, H5, H6 unchanged. | Bare board price: $5.30 per 5 at 135 x 63.5 mm, $7.10 at 135 x 84.5 mm (quotes); Rev-C1's own size was not quoted. | LIVE: JLCPCB quote. | **The Rev C case (`models/Brineomatic Rev C Case.step`) does not fit**; a new case/panel cut-out is needed. |
| A4 | Rail renamed +24V -> +12V; silkscreen "12V", "REV D 12V". | Input must be 9-15 V. | Net-identical (audit confirms the rename is the only difference on that net apart from A1). | **Print a "12 V ONLY" warning on the silkscreen (not done).** 4-20 mA sensors see Vbus - 2 V at 20 mA: confirm the sensor datasheet minimum supply. |

## B. Protection, power-stage and semiconductor swaps

| ID | Refs | Rev-C1 -> Rev D | Why | Due diligence | Open |
|---|---|---|---|---|---|
| B1 | D19, D15, D27, D30, D33, D48 | SMBJ30CA C83847 -> **SMBJ16CA C19077572** (bidirectional) | 12 V design: standoff 16 V > 14.8 V charge voltage; clamp ~26 V instead of ~48 V so downstream parts (TMC2209, RT7272, MOSFETs) see lower surge. **Bidirectional on purpose** at the input so a reversed battery does not conduct through the TVS and sacrifice F1. | LIVE fee-free, 140k stock. CALC: 26 V clamp < AO3400A 30 V (B4), < TMC2209 VS absolute max (DS, 29 V class). | Confirm TMC2209/RT7272 absolute-max vs 26 V clamp on the PDFs. |
| B2 | D50-D55, D1, D2, D10, D44, D6, D24, D4, D9, D35, D42 | Same function, different LCSC source (SMF30CA C19077519 -> C2990493; SMAJ5.0A C87074 -> C2925443; PSM712 -> C32677; BAT54S -> C7420333) and BAV199 C40919 -> **BAV99 C2500** | Fee-free sources of the same part. BAV99 instead of BAV199: BAV199 is the low-leakage dual; BAV99 leaks more. | CALC: on the ADC sense nodes (behind 10k) leakage <= ~0.3 mV at 25 C (<1 LSB of the ADS1115 at the used gain). Motor-output clamps D50-55 left at the 30 V class on purpose (inductive kick). | Leakage grows with temperature (BAV99 at 60-70 C inside an enclosure): bench check ADC offset warm. |
| B3 | D14, D26, D29, D32, D47, D49 | SS54 C22452 (5 A) -> **SS34 C8678** (3 A, 40 V) | Flyback/rail clamp: load limit is 3 A, so a 3 A Schottky is enough; same SMA footprint; Basic. | CALC: flyback current <= output current <= 3 A. | Repeat-peak/surge rating vs actual solenoid inrush if loads exceed 3 A. |
| B4 | Q1, Q2, Q4, Q5, Q6, Q7 | Si2318 C14498 (40 V) -> **AO3400A C20917** (30 V) | Basic, fee-free; better turn-on at 3.3 V gate drive; 30 V is enough once the rail is 12 V and drains are clamped to ~26 V (B1). | LIVE Basic. DS: Vds 30 V, Id 5.7 A, Vgs(th) ~0.65-1.45 V, Rds(on) ~33 mOhm @ 4.5 V / ~52 mOhm @ 2.5 V. CALC: 3 A * 3 A * 0.05 Ohm = 0.45 W per FET in SOT-23 (rated ~1.4 W at 25 C): acceptable but warm. | **Bench: FET temperature at 3 A continuous, switching waveform with a real solenoid.** Confirm figures on the PDF. |
| B5 | D13, D21, D22, D25, D28, D31, D39, D46 | LED GREEN C12624 -> **RED C2286** (0603) | Red 0603 is Basic (fee-free); green is not. | CALC: red Vf is lower, so LED current rises slightly for the same series resistor (not quantified; resistor values were not changed). Cosmetic: colours of status LEDs change (silkscreen text may refer to colours: not reviewed). | Check silkscreen/manual text that names LED colours. |
| B6 | D18 | Buzzer flyback B5819W C7420330 -> **1N4148W C81598** | An SMA SS34 would collide with the buzzer courtyard; 1N4148W is Basic. | CALC: magnetic buzzer coil current is tens of mA, within the 1N4148W 150-300 mA rating; clamp is 0.7 V instead of ~0.3 V (Schottky), harmless. | Confirm the buzzer (QMB-09B-03) rated current on its datasheet. |

## C. Passive and IC value changes

| ID | Refs | Rev-C1 -> Rev D | Due diligence | Open |
|---|---|---|---|---|
| C1 | C3, C24 | 2.7 nF -> 2.2 nF C1604 | Flow-meter RC corner +20 %. CALC. | Test with a pulse generator at the maximum flow frequency. |
| C1 | C18 | 2.7 nF -> 2.2 nF | RT7272 compensation zero 2.46 -> 3.0 kHz (+20 %); expected benign. CALC. | Buck load step 0 -> 1 A on the bench. |
| C1 | C52, C53, C55, C56 | "470 pF/100 V" (LCSC part actually 47 pF: Rev-C1 BOM bug, upstream issue #4) -> 470 pF/50 V X7R C1620 | Motor outputs sit behind ferrites and the TVS clamps at ~48 V < 50 V. | - |
| C2 | C11-C14, C22, C46, C49 | 10 uF **1210** C138687 -> 10 uF/50 V X5R **1206** C13585 (footprint changed in place) | Bulk decoupling; DC-bias derating at 12-15 V is mild at 50 V rating. Basic. | Ripple on the 12 V rail during stepper operation. |
| C3 | C21, C23 | 220 uF/16 V C2977551 (6.3x5.4) -> **C3342** (105 C, 2000 h, 6.3x7.7) | Same value/voltage, 5 V rail, ample margin. | **Body is 2.3 mm taller**: check enclosure height. |
| C3 | C57 | 100 uF/35 V C2836442 -> **47 uF/50 V C3349** | Value halved (real change): bulk capacitance on the 12 V rail, ripple and load-dump hold-up reduced. The 10 uF ceramics (C2) and the buck's own caps carry the rest. | **Bench: input ripple at 3 A, stepper start-up; revert to 100 uF if poor.** |
| C4 | R23 | 82 k 1 % -> C23254 (same value) | Source swap. | - |
| C4 | R25 | 62 k 1 % -> C23221 (same value) | Source swap. | - |
| C4 | R26 | 11.8 k -> **12 k** C22790 | RT7272 FB divider 62 k/11.8 k = 5.00 V -> 62 k/12 k = 4.93 V (-1.4 %). | Measure +5V (expect 4.93 V +/- 3 %). |
| C4 | R27 | 100 k -> **47 k** C25819 | Power LED current (12 V - 2 V)/47 k = 0.21 mA = same as 24 V with 100 k. | - |
| C4 | U10 | MAX3485 C668204 -> **SP3485EN C8963** | Pin-compatible 3.3 V RS-485 transceiver, 10 Mbps, Basic. | Bench RS-485 test. |

## D. Connectors (all 3.5 mm pluggable screw terminals, one family)

| ID | Refs | Rev-C1 -> Rev D | Due diligence | Open |
|---|---|---|---|---|
| D1 | J10, J9 | 5.08 mm power-in terminal (+ loose plug) -> 3.5 mm 2-pin C5188295 (plug C5188249) | 3.5 mm family rated 8 A / 300 V (plug, DS) for a 3.15 A board; wire 16-28 AWG. | Confirm wire gauge for the 3 A feed (16 AWG fits). |
| D1 | J3, J18 (2-pin), J4, J5, J11, J22 (3-pin), J21 (4-pin) | JST-PH S2B/S3B/S4B-PH-K horizontal (C173752, C157929, C157926) -> 3.5 mm screw terminals C5188295 / C5188296 / C5188297 | One connector family, no crimping, 8 A vs JST-PH 2 A per pin. LIVE: parts fee-free; screw terminal board-side $0.04-0.06 each. Pin numbering is unchanged (net-identical per audit). | **Physical pin order**: pin 1 is now at the right of each terminal (cables enter from the top edge); label the silkscreen before ordering; mating cable plugs are NOT assembled by JLCPCB (a BOM with plug lines fails the quote: "fee item calculate failed"): buy C5188249/50/51 separately (~$0.13 each). |
| D1 | J23 (RS-485, 3-pin) | same part as Rev-C1 (C5188296), moved to the bottom edge | - | - |

## E. Kept on purpose

ESP32 net names, TMC2209, RT7272, L2, MAX40200, ADS1115 (stock to be re-checked), PESD3V3L1BA, PSD12C, 0.1 % 100 R sense resistors R3/R41, 0.11 R TMC2209 sense resistors R57/R60, JST-SH I2C header J2, 2x3 servo headers J1/J6, mSMD260 polyfuse F2. These remain Extended (fee-bearing) lines; see `GOALS.md`.

## F. Manufacturing / assembly facts (JLCPCB Economic PCBA)

- Economic requires top-side parts only and qty 2 or 5. THT parts (sockets, terminals, fuse holder, headers, buzzer) are hand/wave soldered at extra cost ($3.61 hand-soldering + $7.97 manual assembly on the 5-board quote).
- The **socket BOM line comes up unselected** on JLCPCB ("multiple types of parts") and must be ticked manually; otherwise the sockets are not assembled.
- **CPL rules learnt the hard way:** (1) JLCPCB expects the *centre* of a part, KiCad's position file gives the pin-1 origin: the 3.5 mm terminals are written with the pin-row centre (`tools/make_jlc.py`); (2) the 1x22 socket rows need rotation 90, otherwise they lie horizontally in JLC's viewer; (3) other THT parts (J1/J6 headers, buzzer, fuse holder, electrolytics) have not been checked against JLC's viewer.
- Each extended line is charged $3.09 per order; 14 lines are charged ($43.26): C3342, C3349 (e-caps), C2687129 (PESD3V3L1BA), C5199854 (PSD12C), C70129 (mSMD260), C394425 (ferrites), C160390 (JST-SH), C177249 (L2), C728670 (R3/R41), C327071 (R57/R60), C37593 (ADS1115), C127866 (RT7272), C2649430 (MAX40200), C2150710 (TMC2209).

## G. Verification status of the layout

- Schematic ERC: 0 errors (432 warnings, not compared one-by-one with Rev-C1).
- PCB DRC (`baseline/rev_d_step15_drc.json`): **0 unconnected, 0 shorts, 0 clearance, 0 crossing**; remaining: 4 hole-clearance + 4 mask-bridge warnings (the four standoff pads, also present in Rev-C1), 2 copper slivers, 2 dangling track stubs and 1 dangling via, silkscreen overlaps. Parity: only 199 stale `LCSC` field mismatches in the PCB footprint properties (netlist and BOM come from the schematic; no part or net mismatch).
- Routing was done with Freerouting + a scripted grid router; **no human has reviewed the layout yet**. Look at: the power cluster (Q9/Q10/D56/R78, x 134-145, y 52-64), the +12V link from J3/J18 to the main rail (inner-layer and long B.Cu route), the +5V plane extension under the terminal strip, and the new bottom edge near J23.

## H. Open items before ordering anything beyond 2 prototypes

1. Human review of the layout in KiCad. 2. Datasheet re-confirmation of every **DS** number above (AO3401A, AO3400A, SMBJ16CA, TMC2209/RT7272 absolute maxima, buzzer current, 3V3 budget of the dev board). 3. Bench test per `BRINGUP_TEST_PLAN.md`. 4. 12 V ONLY silkscreen warning; terminal pin-order labels. 5. New case. 6. Check J1/J6/F1/BZ1/C21/C23/C57 placement in JLC's viewer. 7. Re-upload the regenerated gerbers (`mfg/rev_d_screw_gerbers.zip`) - older zips are stale.
