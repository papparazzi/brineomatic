# Brineomatic Rev C1 — component review (simplify and standardise)

12 Nov 2026. Source: `repo/brineomatic/brineomatic.kicad_pcb` at tag Rev-C1, read with KiCad's Python (every footprint, its sheet and its nets).
Nothing in the design files or the JLCPCB cart was changed. Values below come from the netlist; formulas marked (*) use datasheet constants from memory and should be re-checked before a change is made.

## 1. Why 243 parts for "an ESP32 with five switches"
The functional core is about 30 parts. The rest is protection, filtering and repetition.

| Block | Placed parts | Unique BOM lines it owns | What it is |
|---|---|---|---|
| 5 solenoid/relay outputs | 50 | 9 | Per channel: N-FET low-side switch, gate 220R + 10k pull-down, LED + 1k, flyback Schottky SS54 to supply, TVS SMBJ30CA, 2 x 1 uF, 2-pin 3.5 mm socket |
| Power input, eFuse, 5 V buck | 41 | 26 | Fuse holder, TVS, TPS26630 eFuse + reverse FET Q3 + Q8 + 8 setting resistors (UVLO ~9.1 V*, OVP ~33 V*, limit ~4.0 A*), RT7272B buck to 5.0 V with its 9 support parts, PTC, ideal diode U4, 2 x 220 uF, 2 LEDs |
| ESP32 core, USB, 3.3 V | 35 | 14 | Module, LDO, bulk caps, USB-C + ESD + CC resistors + shield links, USB power path (SS34 + PTC), EN/BOOT buttons with RC + ESD, power LED, RGB status LED + 5 V level shifter |
| Stepper driver | 31 | 9 | TMC2209, sense resistors, charge-pump and bulk caps, and a 14-part output filter (4 ferrites, 4 x 470 pF, 6 TVS) |
| Sensor inputs (2 flow, 2 pressure, 2 TDS, 2 temperature) + ADC | 54 | 10 | Each input: connector, series resistor, RC filter, clamp diode pair, ESD diode; pressure adds a 100R 0.1 % shunt; ADS1115 with I2C pull-ups |
| RS485 | 11 | 4 | MAX3485, two TVS parts, bias and pull-up resistors, 3-pin socket |
| Servos, buzzer, QWIIC, standoffs, 5 V TVS | 21 | 6 | |
| **Total** | **243** | **80** (shared lines counted once) | |

Three things drive the count:
1. **Every wire that leaves the board is protected**: 14 ESD diodes, 6 clamp pairs, 13 TVS diodes, series resistors and filter caps. That is roughly 70 parts.
2. **The power input is built for 12-30 V with surge, reverse and over-voltage cut-off**: 26 of the 80 BOM lines, 12 of the 23 resistor values.
3. **Repetition**: five identical output channels and eight near-identical sensor inputs.

Useful facts found on the way:
- Each relay output already has a **flyback diode (SS54) and a TVS** on the board. An external diode across a contactor coil is not required.
- Outputs are **low-side switched**: terminal pin 1 is permanently at supply voltage, pin 2 is switched to ground. (The bilge alarm switches the positive.)
- The 4-20 mA inputs feed the sensor from the board supply and drop up to 2.0 V in the 100R shunt. On a 12 V boat a transmitter that needs 10 V minimum has almost no margin; pick sensors rated from 8-9 V.
- BOM line 4.7 uF (C37/C47) and three more lines have no LCSC number in the PCB file for some refs (C34, C36, C41, D18, D40, FB1, J19, R47/48, SW1/2, U6); the BOM generator filled them from the schematic.

## 2. All 80 BOM lines, with a verdict
Verdict key: **K** keep · **M** merge into an existing line (value-only edit, same footprint, no layout change) · **D** leave unpopulated if the function is unused · **C** connector family (section 3) · **S** belongs to the stepper block · **R** belongs to RS485.

| # | Refs | Part | Qty | Role | Verdict |
|---|---|---|---|---|---|
| 1 | BZ1 | Buzzer QMB-09B-03 | 1 | Alarm | K |
| 2 | C1, C4, C6, C7, C25-C31, C35, C38, C39, C58, C61, C62 | 1 uF 0603 | 17 | Decoupling, output caps | K |
| 3 | C2, C5, C8, C10, C15, C16, C32, C34, C36, C41, C44, C45, C50, C51, C54, C60 | 100 nF 0603 | 16 | Decoupling, filters, buck boot | K |
| 4 | C11-C14, C22, C46, C49 | 10 uF 50 V 1210 | 7 | Input and stepper bulk | K |
| 5 | C3, C18, C24 | 2.7 nF 0603 | 3 | Buck compensation, flow filters | K |
| 6 | C19, C20 | 22 uF 25 V 1206 | 2 | Buck output | K |
| 7 | C21, C23 | 220 uF 16 V electrolytic | 2 | 5 V bulk | K (Standard-only at JLCPCB) |
| 8 | C33 | 22 uF 0603 | 1 | 3.3 V decoupling | **M** -> 10 uF 0603 (line 14) |
| 9 | C37, C47 | 4.7 uF 0603 | 2 | 3.3 V, TMC2209 5VOUT | K (C47 value is set by the TMC2209) |
| 10 | C40, C42, C43 | 100 uF 6.3 V 1206 | 3 | ESP32 bulk | K |
| 11 | C48 | 22 nF 50 V | 1 | TMC2209 charge pump | S |
| 12 | C52, C53, C55, C56 | 470 pF 100 V C0G | 4 | Stepper output filter | S |
| 13 | C57 | 100 uF 35 V electrolytic | 1 | Stepper bulk | S |
| 14 | C9, C59 | 10 uF 0603 | 2 | Decoupling | K |
| 15 | D1, D2, D10 | SMAJ5.0A | 3 | 5 V rail TVS | K (use a generic brand) |
| 16 | D3, D5, D7, D8, D11, D12, D16, D17, D23, D34, D37, D38, D41, D43 | PESD3V3L1BA | 14 | ESD on every signal pin | K |
| 17 | D13, D21, D22, D25, D28, D31, D39, D46 | Green LED 0603 | 8 | Indicators | K |
| 18 | D14, D26, D29, D32, D47, D49 | SS54 | 6 | Output flyback, supply clamp | K |
| 19 | D15, D19, D27, D30, D33, D48 | SMBJ30CA | 6 | Output and input TVS | K |
| 20 | D18 | B5819W | 1 | Buzzer flyback | **M** -> 1N4148W (line 21, same SOD-123) |
| 21 | D20 | 1N4148W | 1 | Buck bootstrap | K |
| 22 | D6, D24 | BAT54S | 2 | Flow input clamp | M optional -> BAV199 (weaker clamp, same pinout) |
| 23 | D4, D9, D35, D42 | BAV199 | 4 | Low-leakage ADC clamp | K |
| 24 | D36 | SS34 | 1 | USB power path | **M** -> SS54 (line 18, same SMA) |
| 25 | D40 | WS2812B-Mini | 1 | RGB status LED | **D** (forces baking; Standard-only substitute) |
| 26 | D44 | PSM712 | 1 | RS485 TVS | R |
| 27 | D45 | PSD12C | 1 | RS485 TVS | R |
| 28 | D50-D55 | SMF30CA | 6 | Stepper output TVS | S |
| 29 | F1 | 5x20 fuse holder | 1 | Main fuse | K |
| 30 | F2 | mSMD260 PTC 1812 | 1 | 5 V fuse | K |
| 31 | FB1 | nSMD150 PTC 1206 | 1 | USB power fuse | K |
| 32 | FB2-FB5 | Ferrite 50R 0603 | 4 | Stepper output filter | S |
| 33 | H1-H4 | SMT M3 standoff | 4 | Mounting | **D** (holes stay) |
| 34 | J1, J6 | 2x3 pin header 2.54 | 2 | TDS, servos | C |
| 35 | J10 | 5.08 mm 2-pin socket | 1 | Power in | C |
| 36 | J4, J5, J11, J22 | JST PH 3-pin | 4 | Flow, temperature | C |
| 37 | J7, J12, J14, J16, J25 | 3.5 mm 2-pin socket | 5 | Relay outputs | C (already the target type) |
| 38 | J3, J18 | JST PH 2-pin | 2 | Pressure | C |
| 39 | J19 | USB-C | 1 | Flash, serial | K |
| 40 | J2 | JST SH 4-pin (QWIIC) | 1 | I2C expansion | **D** |
| 41 | J21 | JST PH 4-pin | 1 | Stepper motor | C / S |
| 42 | J23 | 3.5 mm 3-pin socket | 1 | RS485 | R |
| 43 | L2 | 6.8 uH inductor | 1 | Buck | K |
| 44 | Q1, Q2, Q4-Q7 | Si2318 N-FET | 6 | Output and buzzer switches | K (40 V rating needed behind a 30 V TVS) |
| 45 | Q3 | CSD19537Q3 | 1 | eFuse reverse-blocking FET | K |
| 46 | Q8 | BSS138 | 1 | eFuse FET gate | K |
| 47 | R1, R2, R4, R10, R14, R16, R20, R28, R33, R36, R39, R42, R52, R53, R56, R59, R63-R65, R70 | 10k | 20 | Pull-ups/downs, filters | K |
| 48 | R9, R11, R12, R49, R50, R62 | 100R | 6 | Series protection | K |
| 49 | R13, R32, R35, R38, R54, R69 | 1k | 6 | LED series, UART | K |
| 50 | R15, R19, R34, R37, R40, R71 | 220R | 6 | FET gate series | **M** -> 100R (line 48) |
| 51 | R6, R17, R18, R30 | 2.2k | 4 | I2C pull-ups, flow divider | K |
| 52 | R21 | 56k 1 % | 1 | eFuse power-good threshold | K |
| 53 | R22, R24 | 24k | 2 | PGOOD pull-up, buck compensation | K |
| 54 | R23 | 82k 1 % | 1 | Buck current limit | K |
| 55 | R25 | 62k 1 % | 1 | Buck feedback (5.0 V*) | K |
| 56 | R26 | 11.8k 1 % | 1 | Buck feedback | K |
| 57 | R27 | 100k | 1 | 24 V LED series | **M** -> 20k (line 63) |
| 58 | R5, R29 | 1.2k | 2 | Flow sensor pull-up to 5 V | **M** -> 1k (line 49); divider gives 3.44 V instead of 3.24 V |
| 59 | R3, R41 | 100R 0.1 % 1206 | 2 | 4-20 mA shunts | K |
| 60 | R7, R8, R31, R61 | 4.7k | 4 | 1-wire pull-up, flow series | **M** -> 5.1k (line 62) |
| 61 | R43-R46 | 0R | 4 | USB shield to ground | K |
| 62 | R47, R48, R51 | 5.1k | 3 | USB CC, LED | K (USB needs 5.1k) |
| 63 | R55, R58, R66, R68 | 20k | 4 | Enable pull-up, stepper VREF, RS485 bias | K |
| 64 | R57, R60 | 0.11R 1 % 1206 | 2 | Stepper current sense | S |
| 65 | R72 | 820k 1 % | 1 | eFuse UVLO/OVP divider | K |
| 66 | R73 | 90.9k 1 % | 1 | eFuse divider | K |
| 67 | R74, R77 | 34k 1 % | 2 | eFuse divider, current monitor | K |
| 68 | R75 | 383k 1 % | 1 | eFuse power-good | K |
| 69 | R76 | 4.53k 1 % | 1 | eFuse current limit | K |
| 70 | SW1, SW2 | B3U-1000P | 2 | Reset, boot | K |
| 71 | U1 | ADS1115 | 1 | 4-channel ADC | K |
| 72 | U10 | MAX3485 | 1 | RS485 transceiver | R |
| 73 | U2 | RT7272B | 1 | 5 V buck | K |
| 74 | U3 | TPS26630 | 1 | eFuse | K |
| 75 | U4 | MAX40200 | 1 | Ideal diode (buck vs USB) | K |
| 76 | U5 | ESP32-S3-WROOM-1-N16R8 | 1 | Controller | K |
| 77 | U6 | USBLC6-2SC6 | 1 | USB ESD | K |
| 78 | U7 | LDL1117S33R | 1 | 3.3 V LDO | K |
| 79 | U8 | SN74LV1T34 | 1 | Level shifter for D40 | **D** with D40 |
| 80 | U9 | TMC2209 | 1 | Stepper driver | S |

## 3. Connectors
Today: 9 part numbers in 5 families.

| Function | Now | Pins |
|---|---|---|
| Power in | 5.08 mm pluggable screw (J10) | 2 |
| 5 relay outputs | 3.5 mm pluggable screw (J7, J12, J14, J16, J25) | 2 each |
| RS485 | 3.5 mm pluggable screw (J23) | 3 |
| 2 pressure | JST PH (J3, J18) | 2 each |
| 2 flow, 2 temperature | JST PH (J4, J11, J5, J22) | 3 each |
| Stepper | JST PH (J21) | 4 |
| 2 TDS, 2 servos | 2x3 pin headers (J1, J6) | 6 each |
| I2C expansion | JST SH (J2) | 4 |
| USB | USB-C (J19) | - |

Target: one family, 3.5 mm pluggable screw terminals (board socket + screw plug), in 2-, 3- and 4-pin. That is the type already used for the relays.
- Power, relays and pressure share the 2-pin part; flow, temperature, TDS, servos and RS485 share the 3-pin part; stepper uses the 4-pin part. **9 part numbers become 3, plus USB-C.**
- It does not drop in. JST PH is 2.0 mm pitch and the headers are 2.54 mm; a 3.5 mm socket needs a new footprint and more edge length.
- Edge length (approx. 3.5 mm per pin + 1.6 mm per housing): pressure 17 mm, flow 24 mm, temperature 24 mm, TDS 24 mm, servos 24 mm, stepper 16 mm = about 129 mm, against a 106 mm top edge with roughly 95 mm usable between the mounting holes. Sharing supply pins (TDS on one 4-pin, servos on one 4-pin) brings it to about 112 mm. Still too long.
- So an all-3.5 mm board needs one of: a longer board (about 125 mm), connectors on a second edge, or 2.5 mm pitch pluggable terminals on the sensor edge (about 85 mm, but a second family).
- Zero-layout alternative: keep the board, buy pre-crimped JST PH pigtails and land them on a DIN-rail screw terminal strip in the enclosure.

## 4. Options, in order of invasiveness
**Tier 0 — BOM-only, no layout change, files untouched except values / populate flags**
- 7 safe merges (lines 8, 20, 24, 50, 57, 58, 60), 1 optional (22).
- Leave unpopulated: RGB LED + level shifter (25, 79), standoffs (33), QWIIC (40), and RS485 if no VFD is used (26, 27, 42, 72).
- 80 lines -> **65**. About US$40 less at JLCPCB Standard for 5 boards (feeder fee ~1.38 per line, parts, and the baking fee).
- If the high-pressure valve is manual, the stepper block also goes (11, 12, 13, 28, 32, 41, 64, 80, and line 9 merges into line 14): -> **56 lines**, about US$70 less in total, and 30 fewer parts per board.
- Each merge still deserves a look at the schematic; none has been bench-tested. The 433-hour track record applies to the unmodified BOM.

**Tier 1 — small fork ("C1-S"), layout edits**
- Connector family as in section 3.
- High-side outputs if you want the boat convention.
- Needs KiCad work, a new DRC pass and a first-article test. Rev D upstream is changing the same areas.

**Tier 2 — redesign for Economic assembly**
- Socketed ESP32-S3 dev board (removes about 14 lines and every Standard-only part), plug-in TMC2209 module (removes 9 lines), simpler input protection (fuse + TVS + reverse FET instead of the eFuse, removes about 9 lines), 2-layer <=100x100 mm.
- Lands near 35-40 lines, which is bilge-alarm territory on price, but it is a new board with none of Rev C1's running hours.

## 5. Questions that decide the BOM
1. Will a stepper motor drive the high-pressure valve, or is the valve manual?
2. Any servo-driven valve (diverter or flush)? If not, J6 can stay empty.
3. RS485/VFD: not needed with the contactor design.
4. Is the RGB status LED wanted, given the web UI and the 24 V / 5 V / per-relay LEDs?
