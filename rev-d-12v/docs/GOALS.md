# Goals of the Rev D (12 V) variant

Fork of [hoeken/brineomatic](https://github.com/hoeken/brineomatic) at tag **Rev-C1**. Not an official revision: an experiment to see how far the controller can be simplified and cheapened without changing what it does.

## Why
1. **Cheap, low-risk assembly at JLCPCB.** Rev-C1 needs the *Standard* PCBA service (parts on both feeders, many Extended parts with a per-line feeder fee, a bare ESP32 module, USB-C and a QFN eFuse). The goal is a board that qualifies for **Economic PCBA** (top side only, 2 or 5 boards) and pays as few paid "Extended" lines as possible:
   - Rev D quote (5 boards, Economic, top side): **$177.52** total, of which the Extended-component fee is **$43.26** (14 charged lines). See `mfg/` and `docs/REDESIGN_PLAN.md` for the quote history ($187.73 -> $175.20 -> $177.52 after the connector change).
   - Every part was re-checked for *Basic* or *Promotional-Extended* status (fee-free). 14 lines remain that are genuinely charged; no fee-free alternative with the same function was found (ADS1115, RT7272, MAX40200, TMC2209, L2, mSMD260, PESD3V3L1BA, PSD12C, 0.1 % / 0.11 R resistors, ferrites, JST-SH, two electrolytic families). Details in `docs/REDESIGN_PLAN.md` (2026-11-01 entry).
2. **12 V only.** Most boats (and the intended use of this variant) run a 12 V house bus. Dropping the 24 V design point lets us:
   - use 16 V-class TVS diodes and 30 V MOSFETs (cheap, Basic) instead of 30 V TVS / 40 V FETs;
   - drop the TPS26630 eFuse (QFN, Extended, 8+ support parts) in favour of a P-FET reverse-polarity stage + the existing 3.15 A fuse;
   - keep the 3 A-per-output envelope, so outputs, fuse and connectors stay the same size.
3. **Replaceable controller.** The soldered ESP32-S3 module, USB-C, boot/reset buttons and level shifter are replaced by two 1x22 sockets for an **ESP32-S3-DevKitC-1 v1.1**. This removes 8 paid lines, makes Economic assembly possible and lets the user swap or update the controller.
4. **Fewer connector families, field-wirable.** All sensor and output connectors are 3.5 mm pluggable screw terminals (one family, 2/3/4 pin), so the board can be wired without crimping.

## Non-goals / what is knowingly given up
- **No 24 V operation.** A 24 V input will destroy the input TVS, FETs and fuse.
- **No electronic input protection beyond reverse-polarity, TVS and the fuse**: UVLO, OVP, 4 A active current limit, soft-start and reverse-current blocking of the Rev-C1 TPS26630 are gone (the firmware never read IMON/FLT/PGOOD; they only went to test points).
- **No on-board USB-C**: use the dev board's own USB port (a series diode, D57, prevents back-feeding when both 5 V and USB are present).
- **Mechanics changed**: the board is 135 x 84.5 mm (Rev-C1: 106 x 63.5 mm); three of the five mounting holes moved, so the **Rev C case in `models/` does not fit**.
- **Untested hardware.** Nothing in this branch has been built or bench-tested yet (`docs/BRINGUP_TEST_PLAN.md`). Treat it as a design proposal.

## How to read this branch
| File | Content |
|---|---|
| `docs/GOALS.md` | this file |
| `docs/CHANGE_REGISTER.md` | every change vs Rev-C1 with risk class, due diligence and open items |
| `docs/CHANGE_AUDIT.md` | machine-generated, complete part/net diff vs Rev-C1 (`tools/audit_changes.py`, fails if any difference has no register ID) |
| `docs/VETTING.md` | power-stage calculations and fee-free searches |
| `docs/BRINGUP_TEST_PLAN.md` | first-board bench checklist |
| `docs/REDESIGN_PLAN.md` | chronological working log incl. quotes |
| `brineomatic/` | the KiCad project (modified in place, so `git diff Rev-C1` shows the changes) |
| `mfg/` | BOM, CPL, gerbers for JLCPCB Economic PCBA |
| `tools/` | scripts used to edit schematic/PCB and generate BOM/CPL |
| `baseline/` | netlists of Rev-C1 and Rev D, DRC/ERC reports |
