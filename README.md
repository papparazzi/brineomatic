# Brineomatic Rev D-12V: a lower-cost 12 V remix of Brineomatic Rev-C1

This fork of [hoeken/brineomatic](https://github.com/hoeken/brineomatic) holds **Rev D-12V**, a remix of the Brineomatic **Rev-C1** watermaker controller for boats with a **12 V** supply. It aims to do everything Rev-C1 does at 12 V and to cost much less when JLCPCB assembles it. Brineomatic itself, its firmware and its documentation are hoeken's work: see [brineomatic.com](https://brineomatic.com).

> [!WARNING]
> **Status on 14 Nov 2026: design proposal. No board has been built or bench-tested.**
>
> This is not upstream's Rev D: upstream is designing its own 24 V Rev D on `main`.
>
> The latest design is on branch [`rev-d-12v-c57-100uf`][branch] (step 27). Read [Before you order](#before-you-order) first.

![Rev D-12V, top side (KiCad render, unchanged since step 26)][render]

## Contents

- [At a glance](#at-a-glance)
- [Why Rev-C1 is expensive to assemble](#why-rev-c1-is-expensive-to-assemble)
- [Cost comparison](#cost-comparison)
- [Every change, and why](#every-change-and-why)
- [Independent review](#independent-review)
- [Before you order](#before-you-order)
- [Branches and documents](#branches-and-documents)
- [Credits and license](#credits-and-license)

## At a glance

| | Rev-C1 (hoeken) | Rev D-12V (this fork) |
|---|---|---|
| Supply | 12-30 V DC | **12 V only** (9-15 V) |
| Controller | ESP32-S3-WROOM-1 module soldered on, USB-C on the board | ESP32-S3-DevKitC-1-N16R8 v1.1 dev board in two sockets, USB on the dev board |
| Input protection | TPS26630 eFuse with an N-channel reverse-polarity MOSFET | two P-channel reverse-polarity MOSFETs, then a TPS16630 eFuse (step 25) |
| Connectors | JST-PH, a 5.08 mm terminal, two 2x3 pin headers | one family: 3.5 mm pluggable screw terminals |
| Board | 106 x 63.5 mm, 4 layers | 160 x 90 mm, 4 layers |
| JLCPCB assembly | Standard PCBA (three parts are "Standard only") | Economic PCBA, top side only |
| BOM lines | 80 | 59 |
| Line fees | US$1.38 on each of 80 lines: US$110.05 | US$3.09 on each of 15 charged Extended lines: US$46.35 |
| 5 assembled boards | about US$376, US$75 each | about US$223 with the dev boards, US$45 each |
| Firmware | Rev C firmware | the same GPIO numbers, so the Rev C firmware should run unchanged (not tested) |
| Field record | 433 running hours reported by its author | none: untested |

The cost comes down in four moves:

1. **A plug-in ESP32 dev board** instead of the soldered module, USB-C and their support parts. This removes two "Standard only" parts and 8 charged lines.
2. **12 V only.** 16 V TVS diodes and 30 V MOSFETs are available as parts that JLCPCB loads free.
3. **Fee-free parts everywhere else.** 15 charged Extended lines are left. Rev-C1's BOM had 42 in an Economic trial quote.
4. **Economic PCBA.** Setup and stencil cost US$9.79 instead of US$34.02, and Basic parts carry no line fee.

What it costs in return: a bigger board, no 24 V, no USB socket on the board, a new case, and no field record yet.

## Why Rev-C1 is expensive to assemble

JLCPCB offers two assembly services:

| | Standard PCBA | Economic PCBA |
|---|---|---|
| Limits | none that matter here | top side only, 2 or 5 boards |
| Setup + stencil (5 boards) | US$25.75 + US$8.27 | US$8.24 + US$1.55 |
| Line fee | about US$1.38 for **every** BOM line, Basic or not | US$3.09 per charged Extended line; Basic and promotional parts are free |
| Parts | all | not the parts marked "Standard only" |

Rev-C1 cannot use Economic PCBA as designed. Three of its parts are "Standard only":

- the ESP32-S3-WROOM-1 module (U5);
- the 220 uF electrolytic capacitors C21 and C23 (LCSC C2977551);
- the WS2812B status LED D40, which also has to be baked before assembly.

With those three left off, an Economic trial quote (12 Nov 2026) still charged 42 Extended lines (US$129.78) and came to US$296.65. The module, the capacitors and the LED would then still have to be bought and soldered by hand.

So the remix has two goals: no "Standard only" parts, and as few charged Extended lines as possible. Running at 12 V only and plugging in the controller are the two design decisions that make both possible.

## Cost comparison

Real JLCPCB quotes for five assembled boards, read on the quote pages. Nothing was ordered, and prices change daily.

| USD, 5 boards | Rev-C1, Standard PCBA, 12 Nov 2026 | Rev D-12V, Economic PCBA, 13 Nov 2026 (step 21) |
|---|---:|---:|
| Bare PCB, 4 layers (engineering fee 25.00 in both) | 52.40 (106 x 63.5 mm, blue, ENIG) | 33.90 (160 x 90 mm, green, HASL) |
| Setup and stencil | 34.02 | 9.79 |
| Components | 144.16 (80 lines) | 69.89 (57 lines) |
| Line fees | 110.05 (feeder loading, 80 lines) | 43.26 (14 charged Extended lines) |
| SMT, hand soldering, manual assembly, X-ray, packaging | 23.91 | 15.70 |
| **Quote total** | **364.54** | **172.54** |
| Billed after JLCPCB's review | about 11.25 (baking 7.94, depaneling 3.31) | - |
| Added since the quote, not re-quoted | - | about 17.04 (step-25 eFuse: 5 x 2.79 plus its Extended line, 3.09) |
| Bought separately | - | about 33 (five ESP32-S3-DevKitC-1-N16R8 v1.1, October estimate) |
| **Estimated total** | **about 376, or 75 per board** | **about 223, or 45 per board** |

Both totals leave out shipping, the fuse insert and the cable plugs.

- **Colour and finish.** Part of the PCB difference comes from Rev-C1's blue solder mask and ENIG finish. In green with leaded HASL, Rev-C1 quoted US$341.34 at Standard. Rev D-12V is still about 37 % cheaper than that.
- **eFuse supply.** The Rev-C1 quote already uses a second-source TPS26630 (US$5.79) because TI's part was out of stock. With TI parts, the October quote was US$434.45. On 13 Nov 2026 TI's TPS26630 cost US$11.89 with 2 in stock. The TPS16630 used in Rev D-12V cost US$2.79 with 2,760 in stock.
- **Rev D-12V quote history** (5 boards, Economic): US$187.73 (30 Oct, first quote), 175.20 (sockets added to the BOM, fee-bearing parts swapped), 177.52 (screw terminals), 178.51 (servo and TDS terminals), 172.54 (13 Nov, 160 x 90 mm board). Details in the [working log][plan] and the [parts check][partscheck].

## Every change, and why

Rev-C1 has 302 parts and Rev D-12V has 272. 180 parts are identical; 130 are changed, added or removed. Every one of them has an ID in the [change register][register], with datasheet figures, calculations and open items. The [audit][audit] is generated by a script that fails if any part difference has no register ID; it finds none. The sections below summarise each change and what it does to cost. Register IDs are given in brackets.

### 1. Controller: a plug-in dev board instead of a soldered module (A2)

**Removed:** the ESP32-S3-WROOM-1 module (U5), the USB-C socket (J19), the boot and reset buttons (SW1, SW2), USB ESD protection (U6), the WS2812B status LED (D40), the level shifter (U8), the 3.3 V regulator (U7), and their support parts (C37-C43, R43-R53, D36-D38, FB1, J20, J24, TP27-TP29).

**Added:** two 1x22 sockets for an Espressif **ESP32-S3-DevKitC-1-N16R8, board v1.1**, and a diode (D57, SS34) in the dev board's 5 V feed.

**Why it saves money:**
- The module and the status LED are "Standard only" at JLCPCB. Without them the board can use Economic PCBA.
- 8 fewer charged lines.
- The dev board costs about US$6.60 and plugs in, so a failed or outdated controller can be swapped in a minute without soldering.

**Trade-offs:**
- Only board v1.1 works as is: its RGB LED is on GPIO38. On v1.0 and on some clones the LED is on GPIO48, which is RS-485 transmit on this board.
- The dev board's regulator now feeds every 3.3 V load: about 65 mA for the board's own parts, plus the ESP32.
- USB is on the dev board. D57 stops USB power from back-feeding the board's 5 V rail.
- All 22 pin assignments of the Rev C firmware (v2.9.0) match the sockets, so the firmware should run unchanged. This was checked on paper, not on hardware ([pin audit][pinaudit]).

### 2. 12 V only (A4, B1, B4)

| Part | Rev-C1 | Rev D-12V | Why |
|---|---|---|---|
| Main supply rail | +24V, 12-30 V input | +12V, 9-15 V input; "12V ONLY" printed twice on the board | Most boats, including this build, have a 12 V house bus. |
| TVS diodes D15, D19, D27, D30, D33, D48 | SMBJ30CA | SMBJ16CA, bidirectional | Loads free. The 16 V standoff is above a 14.8 V charge voltage, and the clamp is about 26 V instead of about 48 V, so the stepper driver, the buck converter and the MOSFETs see less in a surge. |
| N-channel MOSFETs Q1, Q2, Q4-Q7 | Si2318, 40 V | AO3400A, 30 V | Basic part; turns on better from a 3.3 V gate. 30 V is enough once the rail is 12 V and clamped at about 26 V. |

**Trade-off:** a 24 V supply destroys the input TVS diode, the MOSFETs and the fuse.

### 3. Input protection: two MOSFETs, then a smaller eFuse (A1, K1)

| | Rev-C1 | Rev D-12V, steps 1-24 | Rev D-12V, step 25 (now) |
|---|---|---|---|
| Parts | TPS26630 eFuse (QFN-24, Extended), CSD19537 N-channel MOSFET, BSS138, R21, R72-R77, C15, test points TP50-TP52 | two AO3401A P-channel MOSFETs (fee-free), 10 kOhm gate pull-down, BZT52C10 zener gate clamp | the two MOSFETs, then a TI **TPS16630** eFuse (HTSSOP-20) with six resistors and two capacitors |
| Reverse polarity | blocked | blocked | blocked |
| Current limit | 4 A | none: fuse only | 3.8 A; a short is cut off within about 1 us |
| Overvoltage cut-off | yes | none: TVS diodes only | above 16.9 V |
| Soft start | yes | no | 25 ms |
| Undervoltage lockout | yes | no | no (owner's decision) |
| Reverse-current blocking | yes | no | no |
| eFuse price, stock (13 Nov 2026) | TPS26630: US$11.89, 2 in stock | - | TPS16630: US$2.79, 2,760 in stock |

Steps 1-24 dropped the eFuse to save its charged line and its many support parts. The independent review then pointed out that nothing limited a short any more (finding M2), so step 25 put a smaller eFuse back after the MOSFETs. It loads at Economic and adds about US$17 per five boards, its line fee included. Detail: [EFUSE.md][efuse].

### 4. Semiconductor swaps to fee-free parts (B2, B3, B5, B6, C4)

| Parts | Rev-C1 | Rev D-12V | Why it saves money | Effect |
|---|---|---|---|---|
| D1, D2, D4, D6, D9, D10, D24, D35, D42, D44, D50-D55 | SMF30CA, SMAJ5.0A, PSM712, BAT54S, BAV199 | the same parts from fee-free sources; BAV99 instead of BAV199 | no line fee | BAV99 leaks more; at most about 0.3 mV on the ADC inputs at 25 C |
| D14, D26, D29, D32, D47, D49 | SS54, 5 A | SS34, 3 A, 40 V | Basic part | outputs are limited to 3 A anyway |
| D13, D21, D22, D25, D28, D31, D39, D46 | green LEDs | red LEDs | red 0603 is Basic, green is not | status LEDs are red |
| D18 | B5819W | 1N4148W | Basic; an SS34 would collide with the buzzer | 0.7 V clamp instead of about 0.3 V, harmless |
| U10 | MAX3485 | SP3485EN | Basic part | pin-compatible 3.3 V RS-485 transceiver |

### 5. Passive parts (C1-C4)

| Parts | Rev-C1 | Rev D-12V | Why | Effect |
|---|---|---|---|---|
| C3, C24 (flow-meter filter), C18 (buck compensation) | 2.7 nF | 2.2 nF | Basic value | filter corner and compensation zero 20 % higher |
| C52, C53, C55, C56 | 47 pF part in the BOM (470 pF intended, [upstream issue 4](https://github.com/hoeken/brineomatic/issues/4)) | 470 pF, 50 V | fixes the BOM mistake with a Basic part | - |
| C11-C14, C22, C46, C49 | 10 uF, 1210 | 10 uF, 50 V, 1206 | Basic part | - |
| C21, C23 | 220 uF, 16 V, "Standard only" | 220 uF, 16 V, C3342 | loads at Economic | 2.3 mm taller; still a charged line |
| R26 | 11.8 kOhm | 12 kOhm | Basic value | 5 V rail at 4.93 V instead of 5.00 V |
| R27 | 100 kOhm | 47 kOhm | the power LED gets the same current at 12 V as Rev-C1's at 24 V | - |
| R23, R25 | 82 kOhm, 62 kOhm | same values, other LCSC parts | R25's original part was short of stock | - |

C57, the 100 uF bulk capacitor of the stepper driver's supply, was 47 uF from October to step 26 to avoid a line fee. JLCPCB's line-by-line test on 1 Nov 2026 showed that line is charged anyway, and none of the 1,146 100 uF SMD electrolytics at JLCPCB is fee-free, so step 27 put Rev-C1's part back. This also closes the review's minor finding m6: the TMC2209 datasheet recommends at least 100 uF near the driver.

### 6. Connectors: one family of 3.5 mm pluggable screw terminals (D1, D2)

| Connector | Rev-C1 | Rev D-12V |
|---|---|---|
| Power in, J10 | 5.08 mm terminal | 3.5 mm 2-pin terminal |
| Sensors and stepper: J3, J18 (2-pin), J4, J5, J11, J22 (3-pin), J21 (4-pin) | JST-PH, crimped | 3.5 mm 2-, 3- and 4-pin terminals |
| RS-485, J23 | 3.5 mm 3-pin terminal | the same part, moved to the bottom edge |
| Servos and TDS sensors, J1 and J6 | two 2x3 pin headers | four 3-pin terminals on the east edge: J6 and J29 for servos 1 and 2, J1 and J28 for the brine and product TDS sensors |

**Why:** one connector family, field wiring without crimp tools, 8 A per pin instead of 2 A for JST-PH, and the 2x3 headers could not be placed correctly in JLCPCB's viewer.

**Cost effect:** connectors load free at Economic either way. The terminals cost about US$2.32 more per five boards than JST-PH (31 Oct quotes). JLCPCB does not assemble the cable plugs: buy them separately (LCSC C5188249, C5188250, C5188251, about US$0.13 each).

**Trade-off:** the TDS signals now run about 94 and 101 mm instead of about 15 mm. The [analysis][tds] finds noise is not a concern, and their ESD diodes D8 and D41 were moved next to the terminals (step 17).

### 7. Board outline, mounting holes and case (A3, steps 20, 21, 23)

- The outline grew from 106 x 63.5 mm to **160 x 90 mm**: a strip on the west side for the dev board, and strips along the top and east edges for the screw terminals.
- The mounting holes moved to the four corners (152 x 82 mm pattern), and the power plug lines up with the bottom row of plugs.
- **Cost:** the bare boards cost US$8.90 instead of US$4.90 per five; the US$25 engineering fee is the same.
- **The Rev C case does not fit.** A new case is being designed in [`rev-d-12v/case`][case]: a base, and a cover with plug notches and a window for a 2.42" OLED. The firmware has no display support yet.

### 8. Silkscreen and usability (I1, steps 19 and 21)

- Every dev-board pin is labelled, and 15 breakout pads sit beside the unused dev-board pins.
- Every plug has its name and a legend for each pin (for example S, 5V, 12V, GND) in white boxes.
- The dev-board type is printed inside the socket outline, with a credits block for the remix and the original design, and "12V ONLY" warnings.
- **Cost:** none; the silkscreen is free.

### 9. Layout fixes and checks (steps 22, 24, 25 and 26)

- Step 22: no copper fill under the Wi-Fi antenna end of the dev board.
- Step 24: the path from the fuse to the MOSFETs is rebuilt with wide copper (2.3 and 3.1 mOhm instead of 34 and 45 mOhm), and the placement file now carries JLCPCB's rotation corrections, as Rev-C1's did ([review fixes][fixes]).
- Step 25: the eFuse area (section 3).
- Step 26: the servo 5 V supply moves from 0.25 mm inner-layer tracks to 1.8-4.0 mm top-layer copper, 13 mOhm from F2 to each servo terminal instead of 161-230 mOhm ([SERVO_POWER.md][servo]). No part moved.
- Step 27: C57 back to Rev-C1's 100 uF (section 5; review finding m6). Copper and silkscreen do not change.
- After every step: KiCad DRC with schematic parity, ERC, an independent copper trace from every plug pin, and the audit against Rev-C1.

### 10. Manufacturing files and scripts

- [`rev-d-12v/mfg`][mfg]: BOM and placement file for JLCPCB Economic PCBA, with and without cable plugs, and the gerbers of the latest step.
- [`rev-d-12v/tools`][tools]: every schematic and PCB change was made by a script (KiCad 10 Python), so each step can be re-run and checked.
  - `make_jlc.py` writes the BOM and placement file using JLCPCB's centre and rotation rules.
  - `audit_changes.py` fails if any difference to Rev-C1 has no register entry.
  - `trace_connectors.py` follows the copper from every plug pin without relying on KiCad's DRC.

### 11. Kept from Rev-C1 on purpose (E)

Every ESP32 net name and GPIO number; the TMC2209 stepper driver; the RT7272 5 V buck converter and its inductor; the MAX40200 ideal diode; the ADS1115 ADC; the PESD3V3L1BA and PSD12C ESD parts; the 0.1 % 100 Ohm shunts of the 4-20 mA inputs; the stepper sense resistors; the JST-SH I2C header; the F2 polyfuse; and the 4-20 mA sensor circuit.

These include the 14 charged lines for which no fee-free part with the same function was found: two electrolytic-capacitor lines, PESD3V3L1BA, PSD12C, the mSMD260 polyfuse, the ferrites, the JST-SH header, the 6.8 uH inductor, the 0.1 % and 0.11 Ohm resistors, ADS1115, RT7272, MAX40200 and TMC2209. The TPS16630 eFuse is the 15th since step 25.

### 12. What this remix gives up

- 24 V operation.
- The USB-C socket and the 3.3 V regulator on the board (the dev board has both).
- Undervoltage lockout and reverse-current blocking. Current limit, overvoltage cut-off and soft start are back since step 25.
- Green status LEDs (they are red).
- The fit in the Rev C case, and the smaller board.
- Rev-C1's field record: none of these changes has been tested yet.

## Independent review

An independent design review of step 22 (13 Nov 2026, by an AI model in a separate session; the brief is in [INDEPENDENT_REVIEW_BRIEF.md][brief]) found two blockers, four major findings and eleven minor ones. All six blockers and majors are now fixed or closed by the owner's decision; of the minor findings, m6 is fixed and the rest are open.

| Finding | Status |
|---|---|
| B1: the path from the fuse to the MOSFETs was signal-width copper | fixed in step 24 |
| B2: the placement file lacked JLCPCB's rotation corrections | fixed in step 24 |
| M1: the servo 5 V supply ran on 0.25 mm inner-layer tracks (161-230 mOhm) | fixed in step 26: 1.8-4.0 mm top-layer copper, 13 mOhm |
| M2: nothing limited a short after the eFuse was removed | fixed in step 25 (TPS16630) |
| M3: no undervoltage lockout | accepted by the owner |
| M4: 4-20 mA sensor headroom at low battery | dropped: the circuit is the same as Rev-C1's, and the battery is assumed to stay at 12 V or above |
| m6: C57 halved to 47 uF, against the TMC2209 datasheet's 100 uF minimum | fixed in step 27: 100 uF again, as Rev-C1 |
| Other minor findings (m1-m5, m7-m11), note N1 | open |

Detail: [REVIEW_FIXES.md][fixes], [EFUSE.md][efuse], [SERVO_POWER.md][servo] and section M of the [change register][register].

## Before you order

1. **Nothing has been built.** Follow the [bring-up test plan][bringup], from part orientation to the eFuse and servo-supply tests.
2. **No human has reviewed the layout yet.** It was routed with Freerouting and scripts.
3. **At JLCPCB:** choose Economic PCBA, 2 or 5 boards, top side. Upload the gerbers, `BOM-rev_d.csv` and `CPL-rev_d.csv` from [`rev-d-12v/mfg`][mfg].
   - Tick the dev-board socket line by hand; it comes up unselected.
   - In the placement preview, check every MOSFET, diode, LED, IC and electrolytic capacitor against its pin-1 or cathode mark, U3 and D49 above all.
   - Tick the option to confirm the placement before production.
4. **Buy separately:**
   - five ESP32-S3-DevKitC-1-N16R8, board v1.1 (not v1.0, not clones with the LED on GPIO48);
   - the cable plugs;
   - a 5 x 20 mm 3.15 A time-lag fuse.
5. **12 V only.** Never connect 24 V.

## Branches and documents

| Branch | Steps | Content |
|---|---|---|
| `main` | - | upstream's `main` (hoeken's work after Rev-C1, including his own Rev D) plus this page |
| [`rev-d-12v`][b-17] | 1-17 | the remix up to the TDS ESD fix (31 Oct 2026) |
| [`rev-d-12v-stepper-socket`][b-18] | 18 | an alternative with a plug-in TMC2209 module, branched off `rev-d-12v`; not adopted |
| [`rev-d-12v-labels`][b-23] | 19-23 | labels, breakout pads, 160 x 90 mm board, corner holes, antenna keep-out, power plug alignment, case design |
| [`rev-d-12v-review-fixes`][b-24] | 24 | the review's two blockers fixed |
| [`rev-d-12v-efuse`][b-25] | 25 | the TPS16630 eFuse |
| [`rev-d-12v-servo-power`][b-26] | 26 | the servo 5 V supply on wide copper |
| [`rev-d-12v-c57-100uf`][branch] | 27 | C57 back to Rev-C1's 100 uF: **latest design** |

Each step branch builds on the one above it, so the latest branch contains every step. Rev D-12V starts from the **Rev-C1 tag** (`dd1f660`), not from upstream's `main`, which has moved on since (18 commits as of 14 Nov 2026). In the KiCad project in `brineomatic/`, `git diff Rev-C1` shows every change.

Documents (all in `rev-d-12v/docs/` on the latest branch):

| Document | Content |
|---|---|
| [GOALS.md][goals] | goals, what is given up, relationship to upstream |
| [CHANGE_REGISTER.md][register] | every change with datasheet figures, calculations and open items |
| [CHANGE_AUDIT.md][audit] | the complete generated part diff against Rev-C1 |
| [REDESIGN_PLAN.md][plan] | the working log, with every JLCPCB quote |
| [VETTING.md][vetting] | power-stage calculations and fee-free part searches |
| [PARTS_CHECK_2026-11-13.md][partscheck] | stock check and the 13 Nov 2026 quote |
| [LABELS_BREAKOUT.md][labels] | steps 19-23: labels, breakout pads, outline, holes |
| [DEVBOARD_PIN_AUDIT.md][pinaudit] | dev-board pins against the firmware |
| [TDS_SIGNAL_ANALYSIS.md][tds] | the long TDS signal routes |
| [REVIEW_FIXES.md][fixes] | step 24 and the review's findings |
| [EFUSE.md][efuse] | step 25 |
| [SERVO_POWER.md][servo] | step 26 |
| [BRINGUP_TEST_PLAN.md][bringup] | bench tests for the first boards |
| [INDEPENDENT_REVIEW_BRIEF.md][brief] | the brief given to the reviewer |

## Credits and license

- **Brineomatic** is designed by [hoeken](https://github.com/hoeken/brineomatic) and is part of the Yarrboard ecosystem. Documentation: [brineomatic.com](https://brineomatic.com). Upstream's own README for this repository points there for all documentation.
- **Rev D-12V** is a remix of the Rev-C1 tag by [papparazzi](https://github.com/papparazzi). It is not an official Brineomatic revision.
- **License:** the same terms as upstream. The repository's [LICENSE](LICENSE) file is the GNU LGPL v2.1. Upstream's Rev-C1 README names GPLv3 for the firmware and an Open Hardware License for the hardware.

[branch]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-c57-100uf
[render]: https://raw.githubusercontent.com/papparazzi/brineomatic/rev-d-12v-c57-100uf/rev-d-12v/docs/rev_d_pcb_step26_top.png
[b-25]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-efuse
[b-26]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-servo-power
[servo]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/SERVO_POWER.md
[b-17]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v
[b-18]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-stepper-socket
[b-23]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-labels
[b-24]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-review-fixes
[mfg]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-c57-100uf/rev-d-12v/mfg
[tools]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-c57-100uf/rev-d-12v/tools
[case]: https://github.com/papparazzi/brineomatic/tree/rev-d-12v-c57-100uf/rev-d-12v/case
[goals]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/GOALS.md
[register]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/CHANGE_REGISTER.md
[audit]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/CHANGE_AUDIT.md
[plan]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/REDESIGN_PLAN.md
[vetting]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/VETTING.md
[partscheck]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/PARTS_CHECK_2026-11-13.md
[labels]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/LABELS_BREAKOUT.md
[pinaudit]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/DEVBOARD_PIN_AUDIT.md
[tds]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/TDS_SIGNAL_ANALYSIS.md
[fixes]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/REVIEW_FIXES.md
[efuse]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/EFUSE.md
[bringup]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/BRINGUP_TEST_PLAN.md
[brief]: https://github.com/papparazzi/brineomatic/blob/rev-d-12v-c57-100uf/rev-d-12v/docs/INDEPENDENT_REVIEW_BRIEF.md
