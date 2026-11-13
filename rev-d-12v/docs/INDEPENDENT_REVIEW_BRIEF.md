# Brief for an independent design review: Brineomatic remix "Rev D-12V"

You are asked to review a circuit board design that you did not work on. Nobody involved in the design should be trusted over the files:
treat every statement in this brief and in the project's own documents as a claim to check, not as a fact.

## 1. What this is and why the review matters

Brineomatic is an open-source controller board for a boat watermaker (reverse-osmosis desalinator). It switches pumps and valves, drives a
stepper-motor valve, and reads pressure, flow, temperature and salinity sensors. The original design, **Rev-C1** by GitHub user `hoeken`,
is reported by its author to have run for 433 hours.

The design under review is a **remix of Rev-C1** made to be cheaper to assemble at JLCPCB and to run on a 12 V boat. It changes the power
input stage, about 26 component choices, the way the microcontroller is mounted, every connector, the board outline and the silkscreen.
**No remix board has been built or powered.** The owner is about to order assembled boards for a boat. A fault found now costs nothing;
a fault found after ordering costs the batch, and a fault found at sea can damage a pump, flood a compartment or leave the boat without water.

The remix was produced by an AI assistant through scripts, over several sessions, with an autorouter for part of the layout.
No human engineer has reviewed the schematic or the layout. That is the reason for this review.

## 2. What to review

Review **every difference between the remix and Rev-C1**, and say for each one whether it is correct, safe and likely to work.
Then look for anything the designers did not notice at all.

The goal is not to confirm the project's own documents. The most useful result is a problem nobody has found yet.

## 3. Where the files are

| What | Link |
|---|---|
| Remix, branch `rev-d-12v-labels` (design under review, commit `32b05db` or later) | https://github.com/papparazzi/brineomatic/tree/rev-d-12v-labels |
| Remix as one zip | https://github.com/papparazzi/brineomatic/archive/refs/heads/rev-d-12v-labels.zip |
| Original Rev-C1 (tag `Rev-C1`, commit `dd1f660`) | https://github.com/hoeken/brineomatic/tree/Rev-C1 |
| Original as one zip | https://github.com/hoeken/brineomatic/archive/refs/tags/Rev-C1.zip |
| File-by-file comparison on GitHub | https://github.com/hoeken/brineomatic/compare/Rev-C1...papparazzi:brineomatic:rev-d-12v-labels |
| Firmware the board must run unchanged (tag `v2.9.0`) | https://github.com/hoeken/brineomatic-firmware/tree/v2.9.0 |
| Firmware pin configuration for this board | https://raw.githubusercontent.com/hoeken/brineomatic-firmware/v2.9.0/src/configs/config.brineomatic-rev-c.h |
| Original author's statement on Rev-C1 status | https://github.com/hoeken/brineomatic/issues/3 |
| Dev board the remix plugs in (Espressif ESP32-S3-DevKitC-1 v1.1) | https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html |

Inside the remix repository:

| Path | Content |
|---|---|
| `brineomatic/brineomatic.kicad_pcb`, `brineomatic/*.kicad_sch` (13 sheets), `brineomatic/brineomatic.kicad_pro` | KiCad 10 design files. The same paths in Rev-C1 are KiCad 9 files |
| `brineomatic/brineomatic_local.pretty/` | footprint added for the dev-board sockets |
| `rev-d-12v/mfg/BOM-rev_d.csv`, `CPL-rev_d.csv`, `gerbers-rev_d_step22.zip` | what would be sent to JLCPCB (Economic assembly, top side only) |
| `rev-d-12v/docs/GOALS.md` | what the remix set out to do |
| `rev-d-12v/docs/CHANGE_REGISTER.md` | the project's own list of every change with its stated justification |
| `rev-d-12v/docs/CHANGE_AUDIT.md` | machine-generated part-by-part difference against Rev-C1 |
| `rev-d-12v/docs/VETTING.md`, `TDS_SIGNAL_ANALYSIS.md` | the project's own calculations |
| `rev-d-12v/docs/LABELS_BREAKOUT.md`, `DEVBOARD_PIN_AUDIT.md`, `PARTS_CHECK_2026-11-13.md` | the most recent steps: labels, breakout pads, 160 x 90 mm outline, moved plugs, mounting holes, antenna keep-out, pin audit, stock check, quote |
| `rev-d-12v/docs/BRINGUP_TEST_PLAN.md` | the bench test plan that has not been run |
| `rev-d-12v/baseline/*.json` | KiCad ERC and DRC reports |
| `rev-d-12v/tools/*.py` | the scripts that made the changes. Paths inside are those of the author's machines |

If you cannot reach GitHub, the same material is in the zip package described in section 9.

## 4. The changes, as the project describes them

Use this list to plan the work, then verify it against the files. If you find a difference that is not on this list, that is a finding.

1. **Supply range.** 12 V only (stated 9-15 V) instead of 12-24 V.
2. **Input protection.** The TPS26630 eFuse with its MOSFETs and resistors is removed. In its place: two AO3401A P-channel MOSFETs in parallel as a
   reverse-polarity stage, a 10 V zener gate clamp, a 10k gate resistor, the 5x20 mm fuse and a bidirectional TVS. Under-voltage lockout,
   over-voltage cut-off, active current limit and soft-start no longer exist.
3. **Microcontroller.** The soldered ESP32-S3-WROOM-1-N16R8 module, its USB-C port, buttons, USB protection, 3.3 V regulator, status LED and level shifter
   are removed. Two 1x22 sockets take an Espressif ESP32-S3-DevKitC-1-N16R8 v1.1 dev board. The carrier feeds the dev board's 5V pin through a series
   diode and takes the whole board's 3.3 V supply from the dev board's regulator.
4. **Semiconductor substitutions** chosen for JLCPCB "Basic" fee-free status: 30 V TVS -> 16 V TVS, Si2318 -> AO3400A, SS54 -> SS34, BAV199 -> BAV99,
   green LEDs -> red, buzzer flyback diode, RS-485 transceiver, and second-source ESD/TVS parts.
5. **Passive changes.** Several capacitor and resistor values and packages, including the buck converter's feedback divider and compensation capacitor,
   and the bulk capacitor on the supply rail halved.
6. **Connectors.** Every sensor and output connector is now a 3.5 mm pluggable screw terminal; the 2x3 servo/TDS headers became four 3-pin terminals.
   Pin numbering is claimed unchanged; physical pin order on the board may differ from Rev-C1.
7. **Board.** 106 x 63.5 mm -> 160 x 90 mm. Parts moved, large areas re-routed with Freerouting and a scripted grid router.
8. **Latest steps (no net change claimed).** Breakout pads beside unused dev-board pins, implemented as extra pads of the socket footprint;
   the seven top-edge plugs moved 5.5 mm with a plated hole left at each old pin position and a top and bottom track to the new pin;
   mounting holes moved to the corners with ground tie tracks; copper-fill keep-out under the dev board's antenna; silkscreen labels and warnings.

A separate branch `rev-d-12v-stepper-socket` replaces the stepper driver chip with a plug-in module. It was **not adopted** and is out of scope,
unless you have a reason to recommend it.

## 5. What "working" has to mean

The board must do everything Rev-C1 does, with the unmodified firmware v2.9.0, on a boat's 12 V system:

- 12 V lead-acid or lithium house bank, roughly 10.5 V to 14.8 V in normal use, with engine cranking dips, alternator and charger noise,
  inductive loads on the same bus, and the possibility of a reversed connection during installation.
- Five low-side switched outputs for relays, contactor coils and solenoid valves, up to 3 A each according to the project.
- A bipolar stepper motor on a TMC2209 driver (UART-configured, with stall detection).
- Two 4-20 mA pressure sensors, two pulse-output flow meters, two DS18B20 temperature sensors, two analog salinity (TDS) inputs,
  two RC servo outputs, RS-485 (Modbus), I2C expansion, a buzzer, and Wi-Fi from the dev board.
- Assembly by JLCPCB Economic PCBA with the BOM and CPL as given.

## 6. How to work

You cannot power the board, so "testing" here means analysis from primary sources. Do as much of the following as your tools allow, and say which you did.

1. **Rebuild the difference yourself.** Extract netlists from both designs (KiCad's `kicad-cli sch export netlist` if you have KiCad 9/10, otherwise parse the
   `.kicad_sch` / `.kicad_pcb` files) and compare part by part and net by net. Do not rely on `CHANGE_AUDIT.md`.
2. **Check that the remix board matches its own schematic**, and that the BOM and CPL match both. Re-run ERC and DRC if you can, and read the existing
   reports critically: note which warnings were accepted and whether that was reasonable.
3. **Read the manufacturer datasheet for every part that differs from Rev-C1**, and for every part whose operating conditions changed because of the 12 V
   supply or the new 3.3 V source. Check absolute maximum ratings, behaviour at the corners of the supply range, footprint and pin order against the
   KiCad footprint, and orientation in the CPL where it matters (diodes, MOSFETs, ICs, electrolytics, LEDs).
4. **Recalculate.** At minimum:
   - the reverse-polarity stage: orientation, gate drive and losses from 9 V to 15 V and at -15 V, behaviour during a supply dip and a fast reconnect,
     what the zener and gate resistor do, current sharing of the two MOSFETs, and what protects the board now that the eFuse is gone;
   - the TVS choices against charging voltage, load dump and the ratings of everything downstream;
   - the buck converter with its changed feedback divider, compensation and input capacitance: output voltage, stability, ripple, start-up at low input;
   - the 3.3 V budget: every load on the dev board's regulator, including Wi-Fi transmit peaks, against that regulator's rating and thermal limit,
     and the voltage at the dev board's 5V pin after the series diode;
   - each switched output with the AO3400A at 3.3 V gate drive: resistance, dissipation, flyback path and clamp energy for a real solenoid or contactor coil;
   - the 4-20 mA inputs at the lowest supply voltage: headroom for the sensor, shunt, protection parts, and the ADC range;
   - the effect of BAV99 instead of BAV199 on every analog node, over temperature;
   - LED, buzzer and pull-up currents with the changed parts;
   - current capacity of the tracks, vias and plated holes that carry motor, output and supply current, on every layer, including the tracks added when the
     top plugs were moved and the inner-layer tracks to the stepper plug.
5. **Check the firmware fit.** Every pin in the firmware configuration against the dev board's header and the carrier's nets; boot-time states of the
   output pins; strapping pins; pins reserved by the module's memory; the status LED pin on different dev-board versions; anything the firmware expects
   from the removed eFuse or status LED.
6. **Review the layout as layout.** Return paths and ground continuity after the pours were cut by socket rows, moved plugs and keep-outs; the split planes on
   the inner layers; switching-node and motor-current loops near analog inputs; creepage; thermal relief on high-current pins; test-point access;
   the breakout pads sharing nets with strapping, USB and UART pins; silkscreen correctness of every pin legend against the actual net.
7. **Check manufacturability.** JLCPCB Economic constraints, through-hole parts and their hand-soldering, part rotation and origin in the CPL
   (the project found several errors of this kind earlier), stock and lifecycle risk, the board outline and mounting holes.
8. **Look at the system, not only the board.** Marine environment, vibration and socketed parts, a 1.5 kW pump contactor on a relay output, what happens to
   each output and valve if the controller resets or loses power mid-cycle.

Go deep where the consequence of an error is large (power input, outputs, anything that can overheat or leave a valve or pump in the wrong state)
and stay brief where it is small (indicator brightness, label wording).

## 7. Rules of evidence

- Prefer primary sources: manufacturer datasheets, Espressif documentation, the design files themselves. Distributor summaries and forum posts are leads, not proof.
- Mark every statement as one of: **verified** (you read it in a primary source or computed it from the files, and you say where), **inferred**
  (reasoned, with the reasoning shown), or **not checked**.
- Show the numbers and the formula for every calculation, with the datasheet value used and the page or table it came from.
- Do not guess a value you could look up. If you cannot find it, say so; an honest "unknown" is more useful than a plausible figure.
- If two sources disagree, report both.
- Do not soften a finding because the design looks otherwise careful, and do not inflate one to have something to report.

## 8. What to deliver

One report with these parts:

1. **Verdict** in a few sentences: would you order this board as it is, and if not, what must change first.
2. **Findings**, most serious first. For each: what is wrong or doubtful, where (sheet, reference designators, net, coordinates if layout), the evidence,
   the consequence on the boat, your confidence, and the smallest change that fixes it. Use four levels:
   - **Blocker**: will not work, or can cause damage or a hazard.
   - **Major**: likely to fail in normal use or under foreseeable abuse.
   - **Minor**: works, but worse than Rev-C1 or than it should be.
   - **Note**: cosmetic or documentation.
3. **Change-by-change table**: every difference from Rev-C1, your judgement (correct / acceptable with a condition / wrong / could not determine), and the evidence.
4. **Differences you found that the project's documents do not mention.**
5. **Corrections to the project's documents**: any claim in `CHANGE_REGISTER.md`, `VETTING.md` or the other documents that you found to be wrong or unsupported.
6. **What you did not check and why**, so the owner knows what is still unreviewed.
7. **Additions to the bench test plan**: the measurements you would insist on with the first two boards, in order, with pass limits.

Write for an owner who is technically capable but is not an electronics engineer: plain sentences, define a term when you first use it, and put the
conclusion before the reasoning.

## 9. Offline package

`brineomatic-review-package.zip` contains this brief, the remix at commit `32b05db` plus this brief, the original at tag `Rev-C1`, and the firmware
pin configuration file. It is built with `git archive` from the two commits, so it holds exactly what the links above show.

## 10. Constraints

- This is a read-only review. Do not order, quote, publish, open issues or contact anyone on the owner's behalf.
- Do not modify the design. Propose changes in the report.
- The original design is LGPL-2.1 licensed according to GitHub; the remix keeps attribution on the board. Licence compliance is in scope as a note only.
