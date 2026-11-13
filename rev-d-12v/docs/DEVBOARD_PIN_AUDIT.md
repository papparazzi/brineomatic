# Dev-board pin audit, 13 Nov 2026

Board: `rev-d-12v-labels` step 21. Dev board: Espressif ESP32-S3-DevKitC-1-N16R8, board v1.1.
Question: does the carrier use any pin that the dev board, its USB ports, LED, buttons, memory or Wi-Fi need for themselves?

Sources: Espressif user guide v1.1 (header tables, component list, revision note), ESP-IDF GPIO page (strapping, USB-JTAG, flash/PSRAM notes),
ESP-IDF ADC page (ADC2 and Wi-Fi), firmware `config.brineomatic-rev-c.h` at v2.9.0, and the pad nets of U5 read from the PCB.

## 1. Pins the dev board uses itself

| Dev-board function | Pins | Source | Carrier use | Result |
|---|---|---|---|---|
| "USB" port (native USB, also USB-JTAG) | GPIO19 (D-), GPIO20 (D+) | user guide J3 table; GPIO page: "used by USB-JTAG by default" | none, breakout pads only | OK |
| "UART" port (USB-to-UART bridge) | U0TXD GPIO43, U0RXD GPIO44 (the guide lists the names; it does not say in words that the bridge is on them) | user guide J3 table | none, breakout pads only | OK. A device wired to the TX/RX pads shares the line with the bridge chip |
| RGB LED | GPIO38 on v1.1, GPIO48 on the first version | user guide | GPIO38: not connected on the carrier. Firmware `YB_STATUS_RGB_PIN 38` drives it | OK on v1.1. **On a v1.0 board or a clone with the LED on GPIO48, the LED sits on RS485 transmit (GPIO48) and shows no status** |
| BOOT button | GPIO0 (strapping; the guide does not name the pin) | GPIO page | test point TP31 only | OK |
| RESET button | EN / RST | user guide J1 pin 3 | test point TP30 only | OK |
| Octal flash / PSRAM (N16R8) | GPIO35, 36, 37 "not available for external use"; GPIO33-37 and 26-32 not recommended | user guide note; GPIO page | 35-37: breakout pads only, no circuit | OK. The three pads are useless with this dev board |
| Strapping pins | GPIO0, 3, 45, 46 | GPIO page (it does not say what each does; that is in the chip datasheet, not re-read here) | none driven by the carrier; breakout pads only | OK. Anything wired to those pads can change how the chip boots |
| 3.3 V power LED, regulator | 3V3 pins | user guide | carrier 3.3 V rail is fed from the two 3V3 pins | see section 4 |

## 2. Every header pin against the carrier

West row (J1): 3V3, 3V3 -> +3.3V rail. RST -> TP30. 4 -> motor temperature (DS18B20). 5 -> RS485 DE/RE. 6, 7, 15, 16, 8 -> relays 1-5.
17 -> stepper STEP. 18 -> stepper DIR. 3 -> free. 46 -> free. 9 -> stepper UART TX. 10 -> stepper UART RX. 11 -> stepper EN.
12 -> I2C SCL. 13 -> I2C SDA. 14 -> buzzer. 5V -> from the carrier's 5 V rail through D57. G -> GND.

East row (J3): G -> GND. TX, RX -> free. 1 -> product flow meter. 2 -> brine flow meter. 42 -> ADC ready. 41 -> servo 2. 40 -> servo 1.
39 -> water temperature (DS18B20). 38 -> free (dev-board LED). 37, 36, 35 -> free (not usable). 0 -> TP31. 45 -> free.
48 -> RS485 transmit. 47 -> RS485 receive. 21 -> stepper DIAG. 20, 19 -> free (USB). G, G -> GND.

All 22 firmware pin assignments equal the carrier nets (relays 6/7/15/16/8, servos 40/41, DS18B20 4/39, buzzer 14, flow 1/2, I2C 13/12, ADC ready 42,
stepper 17/18/11/21 with UART 9/10, Modbus 47/48/5, status LED 38).

Notes:
- GPIO39-42 carry JTAG names (MTCK, MTDO, MTDI, MTMS) in the header table. Neither page read here warns against using them; by default JTAG runs over USB (GPIO19/20).
- GPIO15/16 also carry the 32 kHz crystal names; the dev board has no such crystal fitted according to the header table (they are ordinary header pins).
- Relay pins are not strapping pins. Each has a 10k resistor to ground on the carrier, so the outputs stay off while the chip is in reset.

## 3. Wi-Fi

- Wi-Fi needs no header pin. The radio and antenna are inside the module.
- **ADC2 is shared with Wi-Fi** (ESP-IDF: "ADC2 is also used by Wi-Fi"). ADC2 is GPIO11-20. The carrier uses 11-18 as digital signals only.
  All analog readings go through the external ADS1115 on I2C (`YB_ADC_DRIVER_ADS1115`). No conflict.
  A future add-on must not use GPIO11-20 for analog readings.
- **Finding: copper under the antenna.** The module's antenna is at the pin-1 end of the dev board (y 28.8-33.7 on the carrier, x 36.7-62.2).
  The carrier has ground fill on three layers and the 3.3 V plane there (70 % of that area is covered). The antenna sits about 11 mm above it on the sockets.
  Espressif's module design guidance asks for no copper under or near the PCB antenna (general guidance, not re-read today). Expect reduced Wi-Fi range; how much is unknown without a test.
  **Fixed in step 22** (`tools/pcb_antenna_keepout.py`): a rule area on all four copper layers, x 34.0-65.0, y 22.0-31.8, excludes copper fill from 6.8 mm beyond the dev board's antenna edge to 1.9 mm above the pin-1 row.
  Checked: 0 of 37,200 sample points inside it carry fill; DRC nothing new; trace 0 unreached. There were no tracks or vias in that area.
  Still there: the copper around the first pins (y 31.8-36), which the 3V3 and GND pins need, and the metal of the sockets themselves. The effect on range is untested either way.

## 4. Power, for completeness

- The guide lists three "mutually exclusive" ways to power the dev board: USB, the 5V pin, the 3V3 pin. The carrier feeds the 5V pin (through D57) and takes 3.3 V out of the 3V3 pins.
- With a USB cable plugged in while the carrier is on 12 V, both sources reach the dev board's 5 V node. D57 stops USB from feeding the carrier's 5 V rail.
  Whether the dev board has its own diode between USB and its 5 V pin is not stated in the guide (open since step 17; bring-up step 5 covers it).
- The whole carrier's 3.3 V load (ADC, RS485, buzzer, pull-ups, temperature sensors) runs from the dev board's regulator. Its current rating is one of the open datasheet gaps.

## 5. Plug J2

J2 is the 4-pin I2C expansion port (JST-SH, 1 mm pitch, the Qwiic / STEMMA QT pinout: GND, 3.3 V, SDA, SCL). It is on the same I2C bus as the on-board ADS1115.
Nothing on the board needs it; it is there to add an I2C sensor or display later.
