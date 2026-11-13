# Rev D bring-up test plan (first 2 boards, current-limited bench supply)

Do not order a larger batch until every line is ticked. Use a lab supply with current limit; start at 0 V. Dev board NOT plugged in until step 5.

0. **Part orientation, before any power** (review B2, step 24): from JLCPCB's assembly photos or on the boards, every SOT-23 part (Q1, Q2, Q4-Q7, Q9, Q10, D4, D6, D9, D24, D35, D42, D44), U1, U4, U9, U10, every diode (D56 above all: reversed, it leaves Q9/Q10 almost off), every LED and C21/C23/C57: the pin-1 or cathode mark matches the silkscreen.
1. **Visual / continuity**: no shorts between +12V, +5V, +3.3V, GND (multimeter, unpowered). Check D56/Q9/Q10 orientation: Q9/Q10 drain (pin 3) on the connector side (PRE_24), source (pin 2) on the +12V rail.
2. **Reverse polarity**: connect -12 V (reversed) with a 100 mA current limit. Expected: < 1 mA, F1 intact, +12V rail stays ~0 V. Then repeat at -15 V.
3. **Forward power-up**: 12.0 V, limit 200 mA, no dev board. Measure PRE_24, +12V (drop across the FETs, expect < 50 mV at no load), PFET gate (expect ~ +12V minus 10 V = ~2 V), +5V = 4.93 V +/-3 %, 5V_HIGH_POWER.
4. **Load drop**: 3 A resistive load on +12V for 30 min: P-FET temperature, drop < 100 mV, buck input ripple. Input copper (step 24): voltage from F1 pin 2 to the Q9 and Q10 drains < 15 mV (calculated 7-8 mV), and no spot between F1 and the MOSFETs more than 10 C above the board around it (IR camera or thermocouple). At step 23 this path was 34-45 mOhm of thin track.
5. **Dev board**: plug an ESP32-S3-DevKitC-1 **v1.1**. Check +3.3V from its regulator, current draw during Wi-Fi, 5V pin voltage (~4.6 V expected). Plug USB at the same time: no backfeed (D57), board still runs; unplug 12 V with USB connected: ESP runs, loads off.
6. **Brown-out**: ramp 12 V down to 6 V and back: record where the buck/ESP drop out (no UVLO any more).
7. **Overvoltage**: slowly to 15.5 V (supply limited): TVS must not conduct (leakage). Do NOT apply 24 V.
8. **Outputs**: each relay output on/off with a 3 A resistive load, indicator LEDs, flyback with an inductive load, repeat output 2 (Q4 ground island was a routing fault - verify).
9. **Stepper**: TMC2209 at 12 V, current setting, torque at speed vs the old 24 V board.
10. **Sensors**: 4-20 mA inputs with a calibrator at 4/12/20 mA; check the loop sensor still works at 11 V supply; flowmeter inputs (2.2 nF RC) with a pulse generator; TDS; DS18B20; I2C (J2); RS-485 with the SP3485EN; servo outputs; buzzer.
11. **Buck**: 5 V ripple and load step 0->1 A (compensation C18 2.2 nF).
12. **Later swaps**: AO3400A output FETs (B4): temperature at 3 A for 30 min per output and gate threshold; red LED brightness (B5); buzzer + 1N4148W flyback (B6); C57 47 uF input ripple at 3 A and stepper start-up (C3); BAV99 ADC offset at 50-60 C (B2).
13. **Connectors**: wire a 3-pin and a 4-pin terminal with real cables, check pin order against the silkscreen; ESP32-S3-DevKitC-1 **v1.1** seats fully in the sockets and the USB port stays accessible.
14. Record results here before releasing any order.
