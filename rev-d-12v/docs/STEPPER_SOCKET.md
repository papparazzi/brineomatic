# Rev D step 18: TMC2209 chip -> socketed BIGTREETECH TMC2209 V1.3 module

12 Nov 2026. Branch `rev-d-12v-stepper-socket`, on top of `rev-d-12v` (217fe22). **Untested. No human has reviewed the layout. The schematic is not updated yet (see Open items).**

Goal: the stepper driver becomes a plug-in part like the ESP32 dev board, so a dead driver is swapped in a minute, and two fee-bearing lines
(TMC2209-LA C2150710, 0.11R C327071) leave the assembly BOM. Rule used: no part leaves the board unless its replacement is named here.

## 1. Evidence

| Fact | Source |
|---|---|
| Module 15.24 x 20.32 mm; two 1x8 rows 12.70 mm apart, 2.54 mm pitch; two extra pins on the EN edge at +2.54 and +5.08 mm from EN, on the same line as EN | BTT drawing `datasheets/btt-tmc2209-v1.3-size.pdf` (to scale; 15.24 mm = 714 px, measured pin centres give 2.54 / 5.08 / 12.72 mm) |
| Pin order, top view. Left row: EN, MS1, MS2, RX, TX, CLK, STEP, DIR. Right row: VM, GND, A2, A1, B1, B2, VIO, GND. "DIAG" is printed at the +5.08 mm pin | BTT picture `datasheets/btt-tmc2209-v1.3-pin.jpg` and the size drawing |
| RX pin = PDN_UART (UART is the factory default), 110 mOhm sense resistors, "Voltage Range: DC 12V - DC 28V" | BTT TMC2209 V1.3 user manual |
| DIAG = connector pin 18, INDEX = pin 17 | bookmark names inside the size PDF (weak evidence) |
| Firmware pins (STEP 17, DIR 18, EN 11, DIAG 21, UART TX 9 / RX 10) | `brineomatic-firmware` `config.brineomatic-rev-c.h`; nets unchanged |

Not verified: whether BTT ships the DIAG pin soldered pointing down, and the physical width of the sockets that will be fitted.

## 2. Replacement ledger

| Removed | Function | Replaced by |
|---|---|---|
| U9 TMC2209-LA | driver | same chip on the module |
| R57, R60 0.11R | current sense | 110 mOhm on the module |
| C48 22 nF, C45 100 nF | charge pump | on the module |
| C47 4.7 uF | 5VOUT capacitor | on the module |
| R58 20k, R59 10k | fixed VREF 1.67 V | module trimmer. **Commissioning: set the trimmer to 1.67 V**, otherwise the motor current differs from Rev-C1 at the same firmware setting |
| nets SPREAD, INDEX | unused chip pins | not brought out (INDEX pin of the module has a hole, no net) |

Kept, same nets: output filter FB2-FB5, C52/C53/C55/C56, D50-D55, TP40/44/45/46, J21; bulk and decoupling C46, C49, C51, C54, C57; C44 (VIO); R1, R2 (MS1/MS2 pull-downs);
R54 (1k between TMC2209_TX and TMC2209_RX); R55 (EN pull-up, driver off at boot).

### Module pin -> net (footprint `brineomatic_local:BTT_TMC2209_V1.3_Socket`, ref U9)

| Pad | Pin | Net | | Pad | Pin | Net |
|---|---|---|---|---|---|---|
| 1 | EN | TMC2209_EN | | 16 | VM | +12V |
| 2 | MS1 | /Stepper Driver/MS1 | | 15 | GND | GND |
| 3 | MS2 | /Stepper Driver/MS2 | | 14 | A2 | /Stepper Driver/OA2 |
| 4 | RX (PDN_UART) | TMC2209_TX | | 13 | A1 | /Stepper Driver/OA1 |
| 5 | TX | not connected | | 12 | B1 | /Stepper Driver/OB1 |
| 6 | CLK | GND (internal clock, as U9 pin 13) | | 11 | B2 | /Stepper Driver/OB2 |
| 7 | STEP | TMC2209_STEP | | 10 | VIO | +3.3V |
| 8 | DIR | TMC2209_DIR | | 9 | GND | GND |
| 17 | INDEX | not connected | | 18 | DIAG | TMC2209_DIAG |

## 3. Layout

The driver corner had no free 15 x 21 mm area, so the module sits **above the output filter** on 8.5 mm sockets, turned 90 deg clockwise:
control row at y 28.70 (EN east), motor row at y 41.40 (VM east), INDEX/DIAG at x 160.90, y 31.24 / 33.78. B2, B1, A1, A2 line up west->east with the filter and J21, so no output crosses another.
The motor row uses the strip the sense resistors R57/R60 occupied.

Parts moved (nets unchanged): FB3, FB4 (to the south side of the motor row, their filter-side connection passes between the socket pins as 0.4 mm tracks), FB5 (0.3 mm west),
D53, C55, TP45, C54 (to C45's old pads), C44 (next to VIO), R1, R2 (next to MS1/MS2), C46, C49 (0.3 mm north).

Copper changed outside the removed parts:
- Filter -> J21 inner tracks re-run between the control-row pins and widened 0.25 -> 0.40 mm. (They carry the motor phase current; 0.25 mm was thin.)
- +5V inner track (to the TDS terminals) moved 0.66 mm north along the motor row; it passes between the GND and VM pins and then rejoins its old path.
- 15 GND stitching vias and 9 +12V vias that sat under the new pins or tracks removed; one GND via added at C51; two In2 links re-join the +12V plane island under C46 (the pin row cuts the plane).
- F.Cu pours that fed U9's pads removed; the two filter "finger" pours end at y 39.95.
- TMC2209_EN/STEP/DIR/TX/DIAG routed by Freerouting 2.1.0 on F/B/In1 only (In2 forbidden: a first run on In2 split the +12V plane, caught by DRC). Stored in `baseline/rev_d_step18_autoroute.json`;
  one hand edit: the DIAG track passes 0.34 mm further from fiducial FID3.

## 4. Verification done

- KiCad 10 DRC (`baseline/rev_d_step18_drc.json`): **0 unconnected, 0 clearance, 0 shorts.** Unchanged from before: 4 hole-clearance + 4 mask-bridge (standoff pads), silkscreen warnings, 1 dangling track, 1 dangling via.
  New: 5 courtyard overlaps, all with the socket strips (see 5).
- Pad-net audit against the previous board: 0 net changes on any kept part; removed parts exactly the 7 passives + chip above; U9 pads as in the table.
- Not done: ERC / schematic parity (schematic not updated), 3D fit check, any bench test.

## 5. Tight fits to check before ordering

| Where | Gap (computed from footprints) |
|---|---|
| Motor-row socket body (2.54 mm wide) to D54/D55 pads | 0.28 mm |
| Motor-row socket body to C46/C49 pads | 0.24 mm |
| Motor-row socket body to C57 can (6.6 mm base) | 0.43 mm |
| Motor-row socket body to FB4 / C51 pads | 0.4 mm |
| DIAG/INDEX 2-pin socket to the H3 standoff pad | 0.13 mm (a wide screw head may touch: fit a 1-pin socket on DIAG only, or a smaller screw) |
| Control-row socket body to R1/R2 | 0.5 mm |

Solder the sockets after the SMD parts. Height under the module: filter parts are below 2 mm, the socket gives about 8.5 mm.

## 6. Manufacturing files

- `mfg/BOM-rev_d*.csv`: U9, R57, R60, C48, C45, C47, R58, R59 removed (57 -> 53 lines; the charged Extended lines C2150710 and C327071 are gone: 14 -> 12 charged lines, about US$6 less fee, **not re-quoted**).
- `mfg/CPL-rev_d*.csv`: the 8 parts removed, 11 moved parts updated from the PCB.
- **Not in the BOM yet: two 1x8 and one 1x2 female headers (2.54 mm, 8.5 mm high) for the module.** No LCSC part has been chosen and checked; until then they are hand-soldered.
- Gerbers in `mfg/` are **stale** (still step 17). Regenerate before any order.
- Modules: BIGTREETECH TMC2209 V1.3, about S$4.78 each on AliExpress (12 Nov 2026).

## 7. Open items

1. **Schematic `tmc2209.kicad_sch` still shows the chip.** PCB and schematic disagree until it is redrawn; BOM/CPL were edited directly. Do this before the next change.
2. Human review of this corner in KiCad (motor row x 143-161, y 41.4; pours around C46/C51; the long EN/STEP/DIR runs on the west side and TX/DIAG on the east side, 60-75 mm each).
3. Choose and verify socket parts; add them to BOM/CPL; regenerate gerbers; re-quote.
4. On the first module: check which of the two extra pins is DIAG (meter to the chip pin), and that it is soldered pointing down.
5. BTT rates the module from 12 V; a sagging battery is at the bottom of that range (the chip itself works from 4.75 V). Bring-up step 9 covers it.
6. Add to `BRINGUP_TEST_PLAN.md`: VREF trimmer to 1.67 V; UART read of the driver; DIAG stall signal; motor phase order/direction against Rev-C1.

## 8. Reproduce

KiCad 10 Python, from the repository root, starting from the step-17 board (`git show 217fe22:brineomatic/brineomatic.kicad_pcb`):

    python rev-d-12v/tools/pcb_stepper_socket.py step17.kicad_pcb step18a.kicad_pcb
    python rev-d-12v/tools/pcb_apply_route_spec.py step18a.kicad_pcb rev-d-12v/baseline/rev_d_step18_autoroute.json brineomatic/brineomatic.kicad_pcb

`pcb_merge_routed_nets.py` is the helper that extracted the five autorouted nets from the Freerouting result.

## 9. How this came about

`history/` holds the 12 Nov 2026 analyses that led here: Rev-C1 cost reduction at JLCPCB, the review of all 80 Rev-C1 BOM lines, the socketed-module study,
and the "E1" ledger (a conservative fork from Rev-C1 that was dropped in favour of this branch because `rev-d-12v` already had the socketed dev board).
