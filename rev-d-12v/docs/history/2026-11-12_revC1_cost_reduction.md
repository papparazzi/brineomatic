# Brineomatic Rev C1 — cost reduction analysis (JLCPCB, 5 boards)

12 Nov 2026. Baseline is the cart order in `jlcpcb-order.md`: Standard PCBA, Blue, ENIG, **US$364.54** + ~11.25 billed after review (bake 7.94, depanel 3.31) + hand-insert remark.
Nothing in the cart was changed by this analysis. A separate trial quote (Economic, green, HASL) exists as an unsaved JLCPCB project draft.

## Where the money goes (Standard, 5 boards)
| Block | USD | Scales with |
|---|---|---|
| Components, 80 lines | 144.16 | boards |
| Feeder loading, 80 lines x ~1.376 | 110.05 | number of unique parts (Basic and Extended alike) |
| PCB: engineering 25.00, ENIG 17.50, blue 5.00, board 4.90 | 52.40 | mostly fixed |
| Setup 25.75 + stencil 8.27 | 34.02 | fixed |
| SMT 7.12, hand-solder 3.61, manual 4.42, X-ray 8.25, packaging 0.51 | 23.91 | mixed |
Fixed per order: about 173 of 364 (47 %).

## Economic PCBA — tested, not worth it for this board
- Accepted for 4-layer, 1.6 mm, green, HASL (blue + ENIG is not an Economic combination; green + ENIG is).
- "Standard Only" parts (cannot be placed in Economic): **U5 ESP32-S3-WROOM-1-N16R8 (C2913202)**, **C21/C23 220 uF electrolytic (C2977551)**, **D40 WS2812B-MINI-V3J (C22371519)**.
- Trial quote without those three: PCB 29.20 + PCBA 267.45 = **296.65** (setup 8.24, stencil 1.55, components 113.12 for 77 lines,
  **Extended components fee 129.78** = 42 charged lines x 3.09, SMT 5.82, hand-solder 3.61, manual 4.42, nitrogen reflow 0.91).
- Economic charges ~3.09 per Extended line; Standard charges ~1.38 per line of any type. With 56 Extended lines the Economic fee (129.78) is
  higher than the Standard feeder fee (110.05). Like for like (green, leaded HASL) Standard is 341.34, so Economic saves ~45 but leaves the
  ESP32 module (~27 for five), two electrolytics per board and the LED to buy and hand-solder: net ~17 for a lot of rework risk.
- Bilge-alarm prices came from a 2-layer <=100x100 board, ~22 BOM lines and the ESP32 on a socketed dev board. Getting there needs a redesign.

## Savings without touching the design files (Standard PCBA)
| # | Change | Saves (USD) | Cost / risk |
|---|---|---|---|
| 1 | Green instead of blue | 5.00 | cosmetic |
| 2 | Lead-free HASL instead of ENIG (leaded HASL: 17.50) | 12.30 | Author specifies ENIG; HASL is less flat for the 0.5 mm QFNs (U3, U9) and the ESP32 module. Works for many, not guaranteed |
| 3 | Do not place D40 (status LED) | ~10.1 (bake 7.94 + line 1.38 + part 0.82) | No status LED unless hand-soldered. Assumes D40 is the only part that forces baking (JLCPCB's October notice named it) |
| 4 | Depanel yourself | 3.31 | snap off the edge rails |
| 5 | Generic SMAJ5.0A instead of SMAJ5.0A-13-F (D1, D2, D10; 5.76 for 17) | ~5 | same rating; price of the generic not looked up |
| 6 | Coupons shown on the quote page ("Save $30", "Save $20") | 20-30? | conditions not read |
| 7 | Merge BOM lines (each ~1.38): e.g. D36 SS34 -> SS54 | 1-5 | each merge needs a schematic check; low value |
| 8 | Hand-solder all 9 through-hole lines yourself | ~20 | 18 THT parts per board to buy and solder; LCSC shipping eats most of it |
| 9 | Buy fuse + plugs yourself, delete the assembly remark | unknown | removes the "quote after review" labour |

Items 1, 3, 4, 5: 375.79 (incl. after-review) -> about **352**. Adding item 2 (lead-free HASL): about **340**. Coupon on top if it applies.

## The lever that matters: quantity
Fixed fees ~173 do not grow with board count. Rough estimate (no price breaks assumed, not quoted):
5 boards ~73 each, 10 boards ~56 each, 20 boards ~47 each. A group buy does more than every item above combined.

## Invasive options (not recommended for a first build)
- Shrink the board from 106 mm to <=100 mm for JLCPCB's small-board 4-layer pricing (layout change; saving not measured).
- Socketed ESP32 dev board + fewer unique parts to make Economic pay (redesign; Rev D is not doing this).
