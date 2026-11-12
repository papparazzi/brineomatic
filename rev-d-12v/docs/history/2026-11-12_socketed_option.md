# Brineomatic "socketed" fork — would plug-in modules make Economic assembly pay?

12 Nov 2026. Analysis only: no design files, cart or orders changed. Cost figures marked ~ are estimates built from the two real JLCPCB quotes of 12 Nov
(Standard 364.54; Economic trial 296.65 with 77 lines, Extended fee 129.78 = 42 charged lines x 3.09). They need a real quote before any decision.

## 1. Plug-in stepper driver (AliExpress, 12 Nov 2026)
- BIGTREETECH TMC2209 V1.3, listing 33028050145: **S$4.78** (1 pc), 4,000+ sold, 4.9 stars. 15.24 x 20.32 mm, two 1x8 rows at 2.54 mm,
  motor supply 5.5-28 V, logic 3-5 V, Rsense 110 mOhm (same as R57/R60 on the board), 2.0 A RMS, StallGuard.
- Cheaper generics from S$1.46 (3,000+ sold) and TENSTAR 4-packs around S$1.6-1.8 each; clone quality unknown.
- Not confirmed from the listing: which pins carry UART (PDN) and DIAG. The firmware needs both (UART on Serial1, DIAG for homing). Check BTT's pinout before layout.

What it removes from the board:
| Removed | Lines | Parts |
|---|---|---|
| U9 TMC2209, R57/R60 0.11R, C48 22 nF, C47 4.7 uF, VREF divider, decoupling | 4 (U9, 0.11R, 22 nF, 4.7 uF after C37 moves to 10 uF) | ~12 |
| Optional: output filter FB2-5, C52-56, D50-55 | 3 | 14 |
| Added: two 1x8 sockets | +1 | 2 |
Must stay on the carrier: the 100 uF bulk capacitor next to the module (C57) and the 4-pin motor connector.
Net: 3 to 6 fewer lines. The bigger gain is a driver you can swap in a minute.

## 2. Plug-in ESP32-S3 dev board (as on the bilge alarm)
Removes: U5 module, U6 USB ESD, J19 USB-C, SW1/SW2, R43-46 0R, U7 3.3 V LDO, C40/42/43 100 uF, C33 22 uF, D36 SS34, FB1 PTC, D40 RGB LED, U8 level shifter,
plus the EN/BOOT RC and ESD parts on shared lines. **12 lines and about 35 parts.** Adds two 1x22 sockets (+1 line, C41376161 on the bilge alarm).

Pins: the Rev C firmware uses GPIO 1, 2, 4-18, 21, 38-42, 47, 48. A DevKitC-1 breaks all of them out, and an N16R8 board keeps the octal-PSRAM pins (35-37) free of
firmware use. If the carrier wires the same GPIO numbers, the **stock firmware release should run unchanged** (not tested). DevKitC-1 v1.1 has its RGB LED on GPIO38, the pin the
firmware already drives; many clones use GPIO48.

## 3. Does that unlock Economic assembly?
Standard-only parts today: U5 (gone with the socket), D40 (gone, the dev board has its own LED) and **C21/C23 220 uF electrolytic (C2977551)**.
The 100 uF 35 V electrolytic C57 (C2836442) was accepted by Economic in the trial, so C21/C23 would move to that part (also saves a line; 6.3 mm can, taller; footprint to check).
With those three handled, nothing blocks Economic. 4-layer, green, HASL or ENIG are all Economic options.

## 4. Cost estimate, 5 boards
Economic charges ~3.09 per Extended line (Basic and "promotional" Extended are free), so the lever is the number of charged Extended lines.

| Step | Charged Extended lines | PCBA + PCB (USD) |
|---|---|---|
| Economic trial of today's BOM (without ESP32 module, 220 uF, D40) | 42 | 296.65 (real quote) |
| + socketed ESP32 (-6 charged, +1 socket) | 37 | ~265 |
| + socketed TMC2209, filter dropped (-5, +1) | 33 | ~235 |
| + Tier-0 trims: RS485, QWIIC, standoffs unpopulated; B5819W and BAT54S merged | 25 | ~205 |
| + one connector family (-3) | 22 | ~195 |
| + simple input protection instead of the eFuse (U3, Q3, Q8, six resistors) | ~15 | ~160 |
Add the plug-in modules: 5 dev boards (~US$6.7 each on the bilge alarm) and 5 TMC2209 modules (~US$3.7 each) = ~US$52.

- Realistic first target (rows 1-4 + modules): **~US$255 for 5, about US$51 per board**, against US$376 today (US$75 per board).
- Aggressive (all rows + modules): **~US$210, about US$42 per board**.
- Further levers, each a design decision: a 12 V-only variant (30 V Basic FETs and capacitors instead of 40-50 V Extended ones), Basic/promotional substitutes for the LEDs,
  ESD and TVS diodes, and a board <=100 x 100 mm (2-layer was US$4.00 on the bilge alarm against US$29.20 for this 4-layer 106 mm board). Plausible floor: US$35-40 per board at 5 pieces.
- It will not reach the bilge alarm's ~US$16 per board: that board has 22 lines; this one would still have 45-55.

Uncertainty: I do not know which 12 Extended lines JLCPCB waived in the trial, so the per-step line counts could be off by a few lines (about +-US$15 overall).

## 5. What it costs you
- It is a new PCB layout (dev board is about 26 x 70 mm, modules are taller), so a fork, not Rev C1. Rev C1's 433 hours do not carry over.
- New checks: 3.3 V budget from the dev board's regulator, USB back-feed (U4 already blocks it), socket retention under vibration, module height in the enclosure.
- Losing the eFuse means losing electronic current limit and over-voltage cut-off; fuse + TVS + reverse-polarity FET remain.
