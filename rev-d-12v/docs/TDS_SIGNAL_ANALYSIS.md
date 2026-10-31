# Is the long TDS signal route a problem? (analysis 2026-10-31)

## What the signal is
- The TDS sensors are DFRobot **SEN0244** modules. The module does the probe excitation and signal conditioning itself and outputs a **slow analog voltage, 0-2.3 V** (3.3-5.5 V supply, 3-6 mA); the board never sees the AC probe signal. (DFRobot wiki / retailer pages; source impedance of the module output is not published.)
- On our board each TDS input is: connector pin 1 -> ESD diode D8/D41 (PESD3V3L1BA) and test point -> **R10/R56 10 kOhm** -> node ADC0/ADC1 with **C5/C50 100 nF to GND** and a BAV99 clamp -> ADS1115 input. That is a 159 Hz low-pass filter (the schematic note says so). The ADS1115 is a 16-bit delta-sigma ADC (input range +/-2.048 V or +/-4.096 V; one LSB = 62.5 / 125 uV).
- Rev-C1 had the connector next to the ADC (about 15 mm of copper). Rev D has the terminals on the east edge: BRINE_TDS is now **85 mm**, PRODUCT_TDS **97 mm** of copper (3 layers, 1-2 vias), between connector and R10/R56.

## Why trace length can matter at all (and why here it mostly does not)
A long trace matters for three reasons:
1. **Transmission-line effects**: only for signals with edges of nanoseconds (a 50 mm trace becomes "long" for roughly 1 ns edges). This is a DC-like signal with a 159 Hz filter: **no issue**.
2. **Noise pick-up from neighbours** (capacitive/inductive coupling): the amount depends on the source impedance of the victim, how long and close the aggressor runs and how fast it switches. Low-impedance, low-frequency signals are insensitive (forum/TI guidance: "low impedance signal lines are less likely to pick up stray interference"). The long segment is *before* the 10 kOhm / 100 nF filter, which attenuates anything above ~159 Hz (a 500 kHz buck ripple by ~3000x).
3. **Shared-ground voltage drops**: the sensor's ground comes from the connector, the ADC measures against the ground at the ADS1115. If big return currents (stepper, relays, servos) flow in the plane between the two points, the sensor output is shifted by that drop. TI's ADS111x layout notes stress good ground return paths and small loop area. Size of the effect: the SEN0244 gives 2.3 V for roughly 1000 ppm, so **1 mV is about 0.4 ppm**; a 1-2 mV ground shift is irrelevant for brine (tens of thousands of ppm) and small for product water (tens to hundreds of ppm).
4. **ESD / surge protection** (the only real concern, below).

## Measured exposure on the actual layout (`kicad/brineomatic.kicad_pcb`)
Segments of the two TDS nets that run within 0.4 mm of another net on the same layer:
| TDS net | neighbour | length exposed | nature of the neighbour |
|---|---|---|---|
| BRINE_TDS | WATER_TEMPERATURE | ~8.7 mm | slow 1-wire DS18B20 line |
| BRINE_TDS | MOTOR_TEMPERATURE | ~0.7 mm | slow 1-wire line |
| PRODUCT_TDS | 5V_HIGH_POWER | ~11.4 mm | servo supply (current steps when servos move) |
| PRODUCT_TDS | TMC2209_TX | ~6.7 mm | 3.3 V UART edges (the fastest aggressor) |
| PRODUCT_TDS | +5V | ~4.4 mm | supply |
| PRODUCT_TDS | MOTOR_TEMPERATURE | ~1.7 mm | slow 1-wire line |
No run next to the buck switch node, the stepper outputs (OA1/OA2/OB1/OB2), relay/solenoid drains or the RS-485 pair. Rough coupling estimate for the worst case, 6.7 mm parallel to the UART: mutual capacitance ~0.2 pF/cm -> ~0.15 pF; charge from a 3.3 V edge Q = C*dV = ~0.5 pC, which on the 100 nF filter capacitor is **~5 uV, below one ADS1115 LSB (62.5 uV)** (and the series 10 kOhm + the sensor's output impedance spread it over time). This is an order-of-magnitude estimate, not a measurement.

## The real weakness: ESD diode placement
D8 and D41 (PESD3V3L1BA) sit next to the ADC, so the **entire 85-97 mm run is unprotected copper between the connector and the diode**. Toshiba, TI (ESD341) and ROHM all say the same: put the TVS at the connector, with a short via-free trace and a low-impedance ground return; ROHM estimates ~52 nH for 50 mm of 0.5 mm trace, so 85-97 mm is ~90-100 nH, and an IEC 61000-4-2 pulse (8 kV contact, ~30 A peak, ~1 ns rise) develops hundreds to thousands of volts across that inductance before the diode can clamp; the unprotected trace also radiates/couples the pulse into neighbours (Toshiba: protected lines must not run parallel to unprotected ones). With Rev-C1 the diode was within a few mm of the connector. A sensor cable plugged by hand next to the RO plumbing is exactly where such events occur.

## Resolution (same day): ESD diodes moved to the connectors
D8 and D41 now sit 4.55 mm from J1 pin 1 / J28 pin 1 (rotation 0, signal pad facing the terminal, direct 0.3 mm track on F.Cu, no via), each with its own GND via 1.4 mm from the ground pad (`tools/pcb_move_tds_esd.py`). The ~94 mm / ~101 mm run (mostly on In1, which is surrounded by GND copper) now starts *after* the diode, so a discharge at the terminal is clamped before it reaches the long copper. Re-measured neighbours (<0.4 mm gap, same layer): BRINE_TDS runs 13.6 mm beside the SERVO 1 signal (50 Hz PWM, edges slowed by R11), 3.6 mm beside PRODUCT_TDS, 2.5 mm beside 5V_HIGH_POWER; PRODUCT_TDS runs 16.1 mm beside BRINE_TDS (both slow DC analog), 5.4 mm beside +5V and 3.7 mm beside TMC2209_TX - same order of magnitude as before, estimated pick-up still below one ADC LSB. DRC after the move: 0 unconnected, no new violations; parity and ERC unchanged; netlist identical to the previous step. Remaining bench check: log ADC0/ADC1 with sensors connected and servos/stepper active.

## Conclusion (original, before the move)
- **Noise/accuracy: not a problem** for this slow 0-2.3 V signal (estimated < 1 LSB of crosstalk, neighbours mostly slow, filter before the ADC). Verify on the bench anyway: log ADC0/ADC1 with the sensor connected and the stepper/relays/servos active.
- **ESD protection: a real regression.** Recommended fix (done, see Resolution): move D8 and D41 (and their test points if wanted) next to J1 pin 1 / J28 pin 1, ground return via several vias, keep R10/R56 and C5/C50 at the ADC. Alternative without layout work: shielded sensor cable with the shield bonded to chassis/GND at the board and a note that the sensors should be connected with power off.
- The same reasoning applies to the **servo terminals J6/J29** (long tracks to the servo drivers) and any other connector whose protection diode is far from its new terminal; the other terminals (J3-J5, J11, J18, J21-J23) stayed in the top strip close to their original positions.

## Sources
- DFRobot SEN0244 wiki and retailer pages: output 0-2.3 V, 3.3-5.5 V supply, 3-6 mA (wiki.dfrobot.com/sen0244).
- TI ADS1115 datasheet layout guidelines (SBAS444): good ground return paths, small signal/return loop area.
- All About Circuits thread "PCB Layout Advice" (near-DC sensing: crosstalk minor, ground-return voltage drops matter; low-impedance lines less susceptible).
- Toshiba FAQ "board design considerations for adding ESD protection diodes", TI ESD341 datasheet layout section, ROHM application note "PCB layout for TVS diodes": place the TVS at the connector, short via-free path, low-impedance ground; 50 mm of trace ~52 nH.
