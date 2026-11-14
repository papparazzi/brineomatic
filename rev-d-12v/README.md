# Rev D (12 V) variant

Start with [`docs/GOALS.md`](docs/GOALS.md), then [`docs/CHANGE_REGISTER.md`](docs/CHANGE_REGISTER.md) (every change + due diligence) and [`docs/CHANGE_AUDIT.md`](docs/CHANGE_AUDIT.md) (complete generated diff vs Rev-C1).

`mfg/` holds the JLCPCB Economic PCBA files (BOM, CPL, gerbers). `tools/` are the Python scripts that edited the KiCad files and generated BOM/CPL (they need KiCad 10's Python, `kiutils` and, for routing, Freerouting; paths inside are those of the author's machine). `baseline/` has the Rev-C1 and Rev D netlists and the DRC/ERC reports.

**Status: untested design proposal.** See the open items at the end of the register.

**Branch `rev-d-12v-labels` (13 Nov 2026):** silkscreen labels for every dev-board pin and every plug, plus breakout pads for the unused dev-board pins. No net change. See [`docs/LABELS_BREAKOUT.md`](docs/LABELS_BREAKOUT.md).

**Branch `rev-d-12v-review-fixes` (step 24, 13 Nov 2026):** the two blockers of the independent review fixed (wide fuse-to-MOSFET-to-rail copper, CPL rotation corrections). No net change. See [`docs/REVIEW_FIXES.md`](docs/REVIEW_FIXES.md).

**Branch `rev-d-12v-efuse` (step 25, 13 Nov 2026):** a 12 V eFuse (TI TPS16630, U3) back between the reverse-polarity MOSFETs and the rail: current limit, overvoltage cut-off, soft start (review finding M2). See [`docs/EFUSE.md`](docs/EFUSE.md).

**Branch `rev-d-12v-servo-power` (step 26, 14 Nov 2026):** the servo 5 V supply re-routed from thin inner-layer tracks onto 1.8-4.0 mm top-layer copper, 13 mOhm instead of 161-230 mOhm (review finding M1). No net or part change. See [`docs/SERVO_POWER.md`](docs/SERVO_POWER.md).
