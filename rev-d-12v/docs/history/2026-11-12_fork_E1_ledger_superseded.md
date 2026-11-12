# Brineomatic fork "E1" — design ledger (socketed ESP32 + socketed stepper driver)

12 Nov 2026. Status: **proposal, nothing built**. Base: hoeken/brineomatic tag Rev-C1, untouched in `../repo`.
Rule for this fork: no part leaves the board unless its replacement is named here and the evidence is listed. Anything not listed in section 3 stays exactly as in Rev C1
(power input, eFuse, buck, all five outputs, all sensor inputs, ADC, RS485, buzzer, servos, connectors, the stepper output filter).

## 1. Evidence gathered
- Every Rev C1 footprint, its sheet and its nets were read from `brineomatic.kicad_pcb` with KiCad 9's Python.
- ESP32 module pad -> GPIO map (WROOM-1 datasheet order) cross-checked against the Rev C firmware config: 22 of 22 firmware pins match the board nets
  (relays 6/7/15/16/8, stepper 17/18/9/10/11/21, I2C 13/12, ADC alert 42, DS18B20 4/39, flow 1/2, servos 40/41, RS485 47/48/5, buzzer 14, RGB 38).
- Espressif ESP32-S3-DevKitC-1 v1.1 user guide: header tables J1/J3, RGB LED on GPIO38 (v1.0: GPIO48), GPIO35-37 unavailable on octal-memory modules,
  three "mutually exclusive" supply options (USB, 5V pin, 3V3 pin). The guide does **not** state the regulator part or whether a diode sits between USB VBUS and the 5V pin.
- BIGTREETECH TMC2209 V1.3 user manual (saved in `../research/datasheets/btt-tmc2209-v1.3-manual.pdf`): pinout, 15.24 x 20.32 mm, 110 mOhm sense resistors,
  "Voltage Range: DC 12V - DC 28V", UART is the factory default on the pin labelled RX, DIAG is an extra pin next to EN.
- Bilge-alarm notes (`../../bilge-alarm/docs/DEVBOARD_PINMAP_revC.md`): the DZQJ clone measures 27.94 x 57.15 mm with **25.40 mm** between rows (Espressif: 22.86 mm), socket part C41376161.

## 2. Connection tables
### 2a. Dev board (two 1x22 sockets). Net names are Rev C1's.
| J1 pin | Name | Net | | J3 pin | Name | Net |
|---|---|---|---|---|---|---|
| 1, 2 | 3V3 | **not connected** (see 3c) | | 1 | G | GND |
| 3 | RST | not connected | | 2 | TX (IO43) | not connected |
| 4 | IO4 | MOTOR_TEMPERATURE | | 3 | RX (IO44) | not connected |
| 5 | IO5 | RS485_DERE | | 4 | IO1 | PRODUCT_FLOWMETER |
| 6 | IO6 | SOLENOID1 | | 5 | IO2 | BRINE_FLOWMETER |
| 7 | IO7 | SOLENOID2 | | 6 | IO42 | ADC_ALERT |
| 8 | IO15 | SOLENOID3 | | 7 | IO41 | SERVO2 |
| 9 | IO16 | SOLENOID4 | | 8 | IO40 | SERVO1 |
| 10 | IO17 | TMC2209_STEP | | 9 | IO39 | WATER_TEMPERATURE |
| 11 | IO18 | TMC2209_DIR | | 10 | IO38 | status-LED data (to U8, kept as an option) |
| 12 | IO8 | SOLENOID5 | | 11-13 | IO37-35 | not connected (PSRAM on N16R8) |
| 13 | IO3 | not connected (strapping) | | 14 | IO0 | not connected (boot) |
| 14 | IO46 | not connected (strapping) | | 15 | IO45 | not connected (strapping) |
| 15 | IO9 | TMC2209_RX | | 16 | IO48 | RS485_DI |
| 16 | IO10 | TMC2209_TX | | 17 | IO47 | RS485_RO |
| 17 | IO11 | TMC2209_EN | | 18 | IO21 | TMC2209_DIAG |
| 18 | IO12 | SCL | | 19, 20 | IO20, IO19 | not connected (USB) |
| 19 | IO13 | SDA | | 21, 22 | G | GND |
| 20 | IO14 | BUZZER | | | | |
| 21 | 5V | +5V | | | | |
| 22 | G | GND | | | | |

### 2b. Stepper module (BTT TMC2209 V1.3, two 1x8 sockets + DIAG)
| Module pin | Net | Rev C1 equivalent |
|---|---|---|
| EN | TMC2209_EN (R55 20k pull-up to 3.3 V stays: driver off at boot) | U9 pin 2 |
| MS1, MS2 | /MS1, /MS2 (R1, R2 10k to GND stay: UART address 0) | U9 pins 9, 10 |
| RX (PDN_UART) | TMC2209_TX (R54 1k to TMC2209_RX stays) | U9 pin 14 |
| TX | not connected | - |
| CLK | GND (internal clock, as U9 pin 13) | U9 pin 13 |
| STEP, DIR | TMC2209_STEP, TMC2209_DIR | U9 pins 16, 19 |
| VM, GND | +24V, GND (C46, C49, C51, C54, **C57 100 uF** stay beside the socket) | U9 pins 22, 28 |
| A2, A1, B1, B2 | /OA2, /OA1, /OB1, /OB2 (filter FB2-5, C52-56, D50-55 and J21 stay) | U9 pins 21, 24, 26, 1 |
| VIO, GND | +3.3V (C44 100 nF stays), GND | U9 pin 15 |
| DIAG (extra pin) | TMC2209_DIAG | U9 pin 11 |
| INDEX (extra pin, if present) | not connected | U9 pin 12 |

## 3. Removal ledger
### 3a. ESP32 block
| Removed | What it did | Replacement | Confidence / check |
|---|---|---|---|
| U5 ESP32-S3-WROOM-1-N16R8 | Controller | Module on the dev board (buy the N16R8 variant) | Pin map verified against firmware. Stock Rev C firmware should run unchanged (not tested) |
| J19 USB-C, U6 USBLC6, R47/R48 5.1k, R43-R46 0R | USB port, ESD, CC resistors, shield link | Dev board's own "USB" port (GPIO19/20) | Clone's USB ESD protection unknown. Service port only |
| D36 SS34, FB1 1.5 A PTC | USB VBUS -> +5V power path with fuse | Dev board 5V pin wired straight to +5V. U4 (kept) still stops USB from feeding the buck | **Check on the first dev board**: diode between its USB VBUS and its 5V pin (meter, diode test). Without one, the buck could back-feed a connected PC |
| SW1, SW2, R49, R50, R52, R53, C38, C39, D37, D38 | Reset and boot buttons with RC and ESD | Dev board's RST and BOOT buttons | Standard on every DevKitC-1 |
| J20 (already unpopulated) | UART header | Dev board's "UART" USB port | - |
| C42, C43 (2 of 3 x 100 uF) | Bulk for the module's Wi-Fi current bursts | Module is now fed by the dev board's regulator | C40 stays on the carrier 3.3 V rail |
| TP27-TP31 | USB / EN / BOOT test points | Not needed | - |

Kept from this block: **U7 3.3 V regulator with C33, C34, C35, C36, C37, C40, C41** (see 3c), D39 + R51 (3.3 V LED), TP26, TP32, TP33.
Kept as footprints, unpopulated by default: **D40 + U8** (status LED). On a v1.1-type dev board the on-board RGB LED sits on GPIO38 and takes over. On clones with the LED on GPIO48 it does not,
and GPIO48 is RS485_DI; populate D40/U8 or accept no RGB status.

### 3b. Stepper block
| Removed | What it did | Replacement | Confidence / check |
|---|---|---|---|
| U9 TMC2209-LA | Driver | Same chip on the module | BTT manual |
| R57, R60 0.11R | Current sense | 110 mOhm on the module ("R110") | BTT manual photo |
| C48 22 nF, C45 100 nF | Charge pump | On the module | Required by the chip; module works stand-alone in printers |
| C47 4.7 uF | 5VOUT capacitor | On the module | Same |
| R58 20k, R59 10k | Fixed VREF 1.67 V | Module's trimmer | **Commissioning step: set the trimmer to 1.67 V**, or the motor current differs from Rev C1 at the same firmware setting |
| U9 SPREAD, INDEX nets | Unused chip pins | Not brought out | - |

Open for the stepper module: the exact X/Y of the DIAG pin is not dimensioned in the manual (take it from BTT's STEP/3D file or measure a module); BTT rates the module from 12 V,
so a sagging 12 V battery is at the bottom of its stated range (the chip itself works from 4.75 V).

### 3c. Decisions taken to stay conservative
1. **Carrier keeps its own 3.3 V regulator (U7).** The dev board's 3V3 pins stay unconnected. Sensors, ADC, RS485, buzzer and pull-ups run from U7 as in Rev C1, so nothing depends on the clone's regulator. Cost: one Extended line.
2. **Stepper output filter and TVS stay**, sitting under the socketed module.
3. **eFuse, buck, outputs, sensor inputs, connectors: untouched**, including their existing routing.

### 3d. Still blocking Economic assembly
- **C21, C23 220 uF 16 V (C2977551) are "Standard Only".** I do not yet understand the 5 V rail well enough to shrink them, so the value stays. To do: test other 220 uF 16 V parts with the same 6.3 mm footprint in JLCPCB's BOM tool until one is accepted; fallback is hand-soldering two capacitors per board.

## 4. Layout plan
- Rev C1 outline: 106.05 x 63.55 mm. The ESP32 module sits at the left edge with sensor inputs above it and RS485 below, so the dev board (27.94 x 57.15 mm clone) does not fit in the freed area.
- Plan: extend the outline about 32 mm to the left (to about 138 x 63.5 mm) and stand the dev board there, USB ports at a board edge. Everything right of the old module keeps its position and routing.
- Stepper module: 15.24 x 20.32 mm on 8.5 mm sockets over the old U9 area (x 148-162, y 40-50 mm); low parts may stay underneath.
- Re-routed nets: the 31 dev-board signals and the stepper module's 16 pins. All other tracks stay locked.
- Acceptance: KiCad DRC with 0 errors and 0 unconnected items, plus a net-by-net comparison against section 2 (script), plus renders.
- The schematic files will lag the PCB until they are redrawn; this ledger and the comparison script are the reference meanwhile.

## 5. Honest cost effect of this conservative version (5 boards, estimates)
- BOM: 80 -> about 71 lines. Economic charged Extended lines: 42 -> about 37.
- JLCPCB Economic about US$263 + modules about US$52 = **about US$315 (US$63 per board)**, against US$376 today. With RS485, QWIIC and standoffs left unpopulated: about US$281 (US$56 per board).
- The earlier US$42-51 figures assumed removing the regulator, the output filter, the eFuse and unifying connectors. Those remain possible later, one by one, each with its own ledger entry.

## 6. Tooling on this PC
- KiCad 9 and 10 with their Python: available (board edits, DRC, renders, fabrication files).
- Autorouter (Freerouting) needs Java: **not installed**. The bilge alarm was routed on a Mac. Needs your OK to install, or the changed nets are routed by hand in KiCad.
