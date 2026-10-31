# Rev D (12 V) variant

Start with [`docs/GOALS.md`](docs/GOALS.md), then [`docs/CHANGE_REGISTER.md`](docs/CHANGE_REGISTER.md) (every change + due diligence) and [`docs/CHANGE_AUDIT.md`](docs/CHANGE_AUDIT.md) (complete generated diff vs Rev-C1).

`mfg/` holds the JLCPCB Economic PCBA files (BOM, CPL, gerbers). `tools/` are the Python scripts that edited the KiCad files and generated BOM/CPL (they need KiCad 10's Python, `kiutils` and, for routing, Freerouting; paths inside are those of the author's machine). `baseline/` has the Rev-C1 and Rev D netlists and the DRC/ERC reports.

**Status: untested design proposal.** See the open items at the end of the register.
