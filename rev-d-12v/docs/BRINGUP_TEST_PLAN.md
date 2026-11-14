# Rev D bring-up test plan (first 2 boards, current-limited bench supply)

Do not order a larger batch until every line is ticked. Use a lab supply with current limit; start at 0 V. Dev board NOT plugged in until step 5.

0. **Part orientation, before any power** (review B2, step 24): from JLCPCB's assembly photos or on the boards, every SOT-23 part (Q1, Q2, Q4-Q7, Q9, Q10, D4, D6, D9, D24, D35, D42, D44), U1, U3 (eFuse, step 25), U4, U9, U10, every diode (D56 above all: reversed, it leaves Q9/Q10 almost off; D49 is vertical since step 25), every LED and C21/C23/C57: the pin-1 or cathode mark matches the silkscreen.
1. **Visual / continuity**: no shorts between +12V, +5V, +3.3V, GND (multimeter, unpowered). Check D56/Q9/Q10 orientation: Q9/Q10 drain (pin 3) on the connector side (PRE_24), source (pin 2) on PFET_OUT, the eFuse input (step 25; before: the +12V rail).
2. **Reverse polarity**: connect -12 V (reversed) with a 100 mA current limit. Expected: < 1 mA, F1 intact, +12V rail stays ~0 V. Then repeat at -15 V.
3. **Forward power-up**: 12.0 V, limit 200 mA, no dev board. Measure PRE_24, PFET_OUT (drop across the FETs, expect < 50 mV at no load), +12V (eFuse output: ramps up in about 25 ms; PGOOD goes high once it is up and only then does the 5 V buck start), PFET gate (expect ~ PFET_OUT minus 10 V = ~2 V), +5V = 4.93 V +/-3 %, 5V_HIGH_POWER.
4. **Load drop**: 3 A resistive load on +12V for 30 min: P-FET and U3 temperature, drop PRE_24 -> PFET_OUT < 100 mV and PRE_24 -> +12V < 250 mV (MOSFETs + eFuse, calculated at most about 0.23 V), buck input ripple. Input copper (step 24): voltage from F1 pin 2 to the Q9 and Q10 drains < 15 mV (calculated 7-8 mV), and no spot between F1 and the MOSFETs more than 10 C above the board around it (IR camera or thermocouple). At step 23 this path was 34-45 mOhm of thin track.
5. **Dev board**: plug an ESP32-S3-DevKitC-1 **v1.1**. Check +3.3V from its regulator, current draw during Wi-Fi, 5V pin voltage (~4.6 V expected). Plug USB at the same time: no backfeed (D57), board still runs; unplug 12 V with USB connected: ESP runs, loads off.
6. **Brown-out**: ramp 12 V down to 6 V and back: record where the buck/ESP drop out (no practical UVLO: U3 switches on above about 5.4 V and off below about 5.0 V, owner's decision M3).
7. **Overvoltage**: slowly to 15.5 V (supply limited): TVS must not conduct (leakage). Then on to at most 17.5 V with a 100 mA limit: +12V must switch off between 16.2 and 17.5 V (U3 overvoltage cut-off, step 25) and come back below about 15.8 V. Do NOT apply 24 V.
8. **Outputs**: each relay output on/off with a 3 A resistive load, indicator LEDs, flyback with an inductive load, repeat output 2 (Q4 ground island was a routing fault - verify).
9. **Stepper**: TMC2209 at 12 V, current setting, torque at speed vs the old 24 V board.
10. **Sensors**: 4-20 mA inputs with a calibrator at 4/12/20 mA; check the loop sensor still works at 11 V supply; flowmeter inputs (2.2 nF RC) with a pulse generator; TDS; DS18B20; I2C (J2); RS-485 with the SP3485EN; servo outputs; buzzer.
11. **Buck**: 5 V ripple and load step 0->1 A (compensation C18 2.2 nF).
12. **Later swaps**: AO3400A output FETs (B4): temperature at 3 A for 30 min per output and gate threshold; red LED brightness (B5); buzzer + 1N4148W flyback (B6); C57 47 uF input ripple at 3 A and stepper start-up (C3); BAV99 ADC offset at 50-60 C (B2).
13. **Connectors**: wire a 3-pin and a 4-pin terminal with real cables, check pin order against the silkscreen; ESP32-S3-DevKitC-1 **v1.1** seats fully in the sockets and the USB port stays accessible.
14. **eFuse current limit** (step 25): electronic load on +12V, supply limit 6 A. Step the load from 3.0 A to 4.5 A: U3 limits between 3.45 and 4.21 A, switches off after about 162 ms and retries (R75 fitted). F1 must not open.
15. **Short on +12V**: supply limit 6 A, short +12V to GND through a switch for a few seconds: U3 limits and retries, Q9/Q10 and F1 survive, +12V comes back by itself when the short is removed. Repeat from a stiff source (charged 12 V battery through F1) only after this passes.
16. **IMON**: voltage across R77 at 1.0 A and 3.0 A load: 0.56 V and 1.67 V (+-10 %).
17. **Latch-off option**: on one board, remove R75: after a short, U3 stays off until the supply is cycled. Decide which behaviour the installation should have (default: auto-retry, as Rev-C1).
18. Record results here before releasing any order.
