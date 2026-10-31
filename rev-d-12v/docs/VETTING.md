# Vetting worksheet - power stage (draft, 2026-10-28)

Envelope (decided): ~3 A board, 3.15 A time-lag input fuse, 12 V house bus (charge up to 14.8 V; 14.6 V LiFePO4), no 24 V.
Status key: VERIFIED = checked against a live source today; CALC = my arithmetic, needs datasheet confirmation; OPEN = not yet checked.

## What the existing power stage actually does (from the Rev-C1 netlist)
| Part | Function | Fate at 12 V |
|---|---|---|
| F1 3.15 A 5x20 | Over-current protection (whole board) | KEEP |
| D19 SMBJ30CA (on PRE_24) | Surge clamp at input | RE-RATE |
| Q3 CSD19537 + Q8 BSS138 + U3 gate drive | Reverse-polarity series N-FET (driven by the eFuse) | REPLACE (P-FET) |
| U3 TPS26630 + R72-R77, R21, R75, C15 | UVLO / OVP / 4 A current limit / PGOOD | REMOVE; PGOOD function must be replaced (see below) |
| D49 SS54 (+24V to GND, cathode on rail) | Reverse-voltage clamp on rail | KEEP (or drop; see C-01 note) |
| U2 RT7272 + L2 6.8 uH, D20, C19/C20 | 24 V -> 5 V buck; EN pin = PGOOD via R22 24k pull-up to +24V | KEEP; EN pull-up now to +12V |
| F2 mSMD260 + U4 MAX40200 | 5V_HIGH_POWER (servos) polyfuse + ideal-diode OR into +5V | KEEP unchanged (5 V side, not touched by 12 V change) |
| D21 / D22 + R27 100k / R28 10k | Power LEDs | R27 re-check for 12 V (CALC) |

**What is lost by removing the eFuse** (must be accepted explicitly by Sascha): active 4 A electronic current limit (fuse 3.15 A remains, but it is slow), UVLO/OVP thresholds, soft start (dV/dt), and reverse-current blocking from the rail back to the battery. Of these, firmware never reads IMON/FLT/SHDN (they only go to test points).

## C-01 Reverse-polarity stage
- Proposed: P-channel MOSFET high-side in series after F1/TVS, gate to GND through R (~10k) with a ~10 V zener from source to gate to protect Vgs. Standard "ideal diode" topology; body diode points toward the load so normal polarity conducts once Vgs < Vth, reversed polarity keeps it off.
- Candidate: **AO3401A, LCSC C15127, Basic, 671,956 in stock** (VERIFIED on jlcpcb.com today). 30 V, 4 A, Rds(on) 47 mOhm @ -10 V, 60 mOhm @ -4.5 V.
- **Gate limit**: AO3401A Vgs max is +/-12 V (CALC from memory of AO datasheet - OPEN, confirm). Bus reaches 14.8 V, so a gate clamp is mandatory, a bare gate-to-GND tie would exceed it.
- **Current**: a 3.15 A time-lag fuse carries 100 % indefinitely and ~135 % (4.25 A) for up to an hour, exceeding a single AO3401A's 4 A rating. Use **two AO3401A in parallel** (same LCSC line, no extra fee): 3.15 A / 2 -> conduction loss about 2 x (1.6 A)^2 x 0.05 ohm = 0.26 W total (CALC), ~65 mV drop at 3.15 A with both.
- Compare with Rev-C1: Q3 CSD19537 conducted via eFuse drive. New circuit has no active current limit and no OVP; protection above 16 V comes from the TVS and the fuse only.
- Test (V6): apply reversed 14.8 V on a current-limited supply, expect < 1 mA; apply normal, measure drop at 1 A / 3 A; check FET temperature at 3 A for 30 min.

## C-02 Input surge clamp
- Need unidirectional, standoff >= 15.5 V so it does not conduct at a 14.8 V charge voltage, clamp below the lowest absolute-max downstream. 16 V standoff (SMBJ16A: breakdown ~17.8-19.7 V, clamp ~26 V at 23 A) fits.
- **VERIFIED: every SMBJ16A on JLCPCB today is Extended** (93 hits, none Basic or Promotional) -> costs a ~$2.3 feeder fee. A Promotional-Extended equivalent (the Liown family used for SMBJ30CA C2925441) is OPEN - need to search "SMBJ16" for Liown/other promo parts, or choose SMBJ15A/SMBJ17A if only those are promo.
- Downstream limits to check against clamp voltage (OPEN): TMC2209 VS abs max, RT7272 VIN abs max, Si2318 Vds (40 V), 220uF 16 V caps (C21/C23 are on the 5 V rail, unaffected).

## PGOOD / buck enable replacement
- Rev-C1: U3 PGOOD (open-drain) pulled up by R22 24k to +24V, enabling RT7272. Without U3, EN is pulled up permanently by R22, so the buck starts as soon as VIN rises. RT7272 has its own VIN UVLO; at battery undervoltage it simply stops. Net effect: **no external UVLO threshold any more** (RT7272 internal UVLO ~4 V in CALC, OPEN). Consequence: at a deeply discharged battery the controller keeps running down to a few volts, and the 4-20 mA loops and solenoids see low voltage. Needs a decision: accept, or add a small voltage-supervisor on EN (resistor divider + Zener, costs 2-3 cheap Basic parts).
- RT7272 EN pin absolute max vs pulling through 24 kOhm from 14.8 V: OPEN (datasheet check).

## Fee-free (Basic) candidates confirmed so far
| Need | Part | LCSC | Status |
|---|---|---|---|
| Reverse-polarity P-FET | AO3401A | C15127 | VERIFIED Basic, stock 671,956 |
| Input TVS 16 V | SMBJ16A | various | VERIFIED NOT Basic; promo equivalent OPEN |

## Open items needing Sascha
1. Accept loss of the eFuse functions listed above (esp. UVLO and active 4 A limit).
2. Accept buck running down to the RT7272 UVLO, or add an EN supervisor.
3. Sensor minimum supply voltage (still unanswered; applies to the 4-20 mA loops).

## Update 2026-10-28 (later) - gate clamp and tooling
- VERIFIED today: BZT52C10 (10 V zener) has **no Basic/Promotional listing**; AO4407A (30 V, +/-20 V gate P-FET) is **Extended only** (all 8 listings). So the only fee-free P-FET found is AO3401A (+/-12 V gate), which needs a gate clamp, and the cheapest clamp part found so far costs a feeder fee. OPEN: search a Promotional zener (e.g. Liown) or a Basic 2-diode/transistor clamp; otherwise accept one ~$2.3 line for the zener (and one for the 16 V TVS).
- Tooling VERIFIED: kiutils (in scratchpad venv) round-trips all 12 sheets; the re-exported netlist is identical to the Rev-C1 baseline (netdiff: no parts/nets changed). So scripted schematic edits are safe to apply and diff.
- Edit plan for power_supply.kicad_sch (coordinates mm): delete U3, Q3, Q8, R72-R77, R21, R75, C15, TP50-52 and the wires between x=133..195 on y 38..72 (keep the GND bus y=76.2, the rail stub x>=195.58, R22 and the PGOOD label); insert two AO3401A (source on PRE_24, drain to rail), 10 k gate-to-GND resistor and the gate clamp between x=133 and 176; rename the +24V power symbols to +12V last.

## Update 2026-10-28 (fee-free search, resolves the two open items above)
Searched inside JLCPCB's own fee-free list (jlcpcb.com/parts/basic_parts, "$0 Feeder Loading Fees in Economic PCBA"). NOTE: the normal parts search labels these parts plain "Extended", so the Basic/Promo filter there is unreliable; only the basic_parts page is authoritative.
| Need | Part | LCSC | Source / stock | Status |
|---|---|---|---|---|
| 16 V unidirectional TVS (replaces SMBJ30CA on input) | SMBJ16A, hongjiacheng, SMB, 16 V standoff, 19.7 V min breakdown, 26 V clamp @ 23 A | **C19077571** | in fee-free list, 115,431 | VERIFIED fee-free; datasheet limits still to check (CALC) |
| 10 V zener for P-FET gate clamp | BZT52C10, hongjiacheng, SOD-123, 350 mW, 9.5-10.5 V | **C19077408** | in fee-free list, 580,479 | VERIFIED fee-free |
| P-FET | AO3401A | C15127 | Basic | VERIFIED |
Same family also available fee-free for re-rating other TVS: SMBJ12A C19077565, SMBJ13A -67, SMBJ15A -69, SMBJ18A -73 (output-driver TVS can use SMBJ16A as well, but the bidirectional SMBJ16CA variant is not yet checked).
Zener check: Rb = 10 k, worst surge 26 V -> I = (26-10)/10k = 1.6 mA, zener dissipation 16 mW (CALC, fine). Normal 14.8 V: 0.5 mA.
