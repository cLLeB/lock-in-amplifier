# Project 1: lock-in amplifier for an optical sensor

Design started 2026-10-03, board added 2026-10-04, last updated 2026-10-06. Simulated in LTspice (generic op amp model) and in ngspice (Microchip's own op amp model), drawn as a KiCad schematic and laid out as a board. Built and working since 2026-10-28: the measured results are in `README.md`. Every number in this file is a calculation or a simulation unless it says otherwise.

## What it does

An LED blinks at 1024 Hz. A photodiode picks up that light together with far stronger room light and lamp flicker. The circuit outputs a DC voltage proportional only to the light that blinks in step with the LED.

Target for the first build: detect a 10 nA photodiode signal in the presence of 5 uA of steady ambient light and 1 uA of 100 Hz flicker.

## Signal chain

```
 9 V battery -> protection diode -> 5 V regulator -> 2.5 V virtual ground (buffered)

 32.768 kHz crystal -> 74HC4060 divider -> 1024 Hz reference --+--> MOSFET -> LED
                                                              |
 photodiode -> [1 TIA] -> [2 high-pass + gain 11] -> [3 +1/-1 switch] -> [4 low-pass] -> buffer -> output
                                                              ^
                                                     reference controls switch
```

## Stage by stage

All signal voltages are measured relative to the 2.5 V virtual ground.

### 1. Transimpedance amplifier (TIA)

- Converts photodiode current to voltage: `V = I x Rf`, with Rf = 100 kohm.
- 5 uA of ambient light gives 0.5 V, so the stage clips at about 24 uA of ambient light.
- Cf = 100 pF sets the bandwidth: `1 / (2 pi Rf Cf)` = 15.9 kHz. It also keeps the amplifier stable against the photodiode's capacitance (about 70 pF for a BPW34 at low bias).
- The photodiode anode goes to ground, so it sits at 2.5 V reverse bias.

### 2. High-pass filter and gain

- 10 nF and 100 kohm give a 159 Hz corner: `1 / (2 pi R C)`.
- It blocks the ambient DC completely and reduces 100 Hz flicker to about half.
- Gain is 11: `1 + 10k / 1k`.
- Why not more gain: the flicker reaches +/-0.6 V here (simulated). More gain would clip it against the 5 V supply, and clipping destroys the measurement. This headroom is the design's "dynamic reserve".

### 3. Synchronous demodulator

- An op amp with two 10 kohm resistors has gain +1 or -1 depending on where its non-inverting input is connected.
- One section of a 74HC4053 analog switch connects it to the signal (gain +1) while the LED is on, and to virtual ground (gain -1) while it is off.
- The wanted signal is rectified into DC. Anything at another frequency is turned into AC that averages to zero.

### 4. Low-pass filter and buffer

- Two RC sections, 100 kohm and 1 uF each, 1.6 Hz corner per section.
- Equivalent noise bandwidth of the pair: 0.83 Hz.
- Settling to a new reading takes roughly one second. Slower filter means less noise but slower response.

### Reference clock and LED

- A 74HC4060 with a 32.768 kHz watch crystal, divided by 32, gives 1024 Hz at exactly 50 % duty.
- Exact 50 % duty matters: see the duty-cycle row in the error table below.
- The LED is powered from the 9 V battery side, not the 5 V rail, so its current pulses do not appear on the amplifier supply. Any LED current that leaks into the amplifier is at exactly the reference frequency and cannot be filtered out.

## Simulation results

Files: `sim/lockin_tran.asc` (drawn schematic, open in LTspice) and `sim/lockin_tran.cir` (the same circuit as text). Interference present in every run: 5 uA ambient, 1 uA flicker at 100 Hz. All LTspice runs were repeated on 2026-10-06 with the switch buffer (U3B) included; the numbers moved by less than 0.1 %.

| Signal | Output | Note |
|--------|--------|------|
| 0 nA | 0.000 mV | Interference alone gives no output |
| 10 nA | 5.22 mV | |
| 100 nA | 52.19 mV | Linear |

- Sensitivity: 0.522 mV per nA. The ideal figure is 0.55 mV per nA (`Rf x 11 / 2`); the high-pass filter rounds the square wave and costs about 5 %.
- Output ripple: 0.05 mV peak to peak.

## Error budget

File: `sim/lockin_offset.cir`, 10 nA signal, 0.5 mV offset applied to one op amp at a time.

| Error source | Output shift | Equivalent signal | Why |
|--------------|--------------|-------------------|-----|
| Offset in gain stage | +0.01 mV | 0.02 nA | The demodulator turns this DC into AC, which the filter removes |
| Offset in demodulator op amp | +1.00 mV | 1.9 nA | Comes after the switching, at a gain of 2 |
| Offset in output buffer | +0.50 mV | 1.0 nA | Passes straight to the output |
| Offset in the switch buffer (U3B) | +0.50 mV | 1.0 nA | Reaches the demodulator input for half of each cycle, at a gain of 2 |
| 49 % duty clock with gain-stage offset | -0.10 mV | 0.2 nA | Unequal half-cycles stop the offset averaging to zero |

Calculated noise:

| Source | Current noise |
|--------|---------------|
| Shot noise of 5 uA ambient light, `sqrt(2 q I)` | 1.27 pA/rtHz |
| Feedback resistor thermal noise, `sqrt(4 k T / Rf)` | 0.41 pA/rtHz |
| Op amp voltage noise (8.7 nV/rtHz) across Rf | 0.09 pA/rtHz |
| Total | 1.33 pA/rtHz |

- Output noise in 0.83 Hz: about 1.3 uV rms, equal to a 2.6 pA signal.
- Ambient light, not the electronics, sets the noise floor.

Noise simulation (`sim/lockin_noise.cir`, 2026-10-05), front end up to the demodulator input, op amps set to MCP6022 datasheet noise figures:

| Case | Noise at demodulator input, 1024 Hz | Referred to the photodiode |
|------|-------------------------------------|----------------------------|
| Everything | 1.45 uV/rtHz | 1.34 pA/rtHz |
| Without ambient-light shot noise | 0.48 uV/rtHz | 0.44 pA/rtHz |
| With noiseless op amps | 1.44 uV/rtHz | 1.33 pA/rtHz |

- The simulation agrees with the hand calculation (1.33 pA/rtHz) to within 1 %.
- The noise is flat to within 4 % out to the fifth harmonic, so the output noise is 1.45 uV/rtHz x sqrt(0.83 Hz) = 1.3 uV rms, equal to 2.5 pA.
- The op amps add under 1 % to the total. A quieter op amp would not improve this circuit; less ambient light would.
- The op amp here is LTspice's generic model with the datasheet's noise figures entered, not Microchip's own model. The 1/f corner (555 Hz) is derived from the datasheet's 0.1 to 10 Hz figure.

What actually limits the first build, largest first:

1. Static offsets of the demodulator, switch buffer and output buffer, up to about 2 mV (4 nA) at 0.5 mV per op amp. Removed by reading the output with the LED covered and subtracting.
2. Offset drift with temperature after that subtraction.
3. Ripple, 0.05 mV (0.1 nA).
4. Random noise, 0.0013 mV (0.003 nA).

Possible second-version improvement: move gain ahead of the demodulator by sharpening the filter in stage 2, so offsets after the switch matter less.

## Check with Microchip's own op amp model (2026-10-05, rerun 2026-10-06)

Files: `sim/lockin_tran_ng.cir`, run by `sim/ngrun_lockin.py`; results in `sim/lockin_tran_ng.log`. The model (`sim/mcp6021_model/MCP6021.txt`, REV B) is written for PSpice. LTspice solves one stage with it but stalls on the whole circuit, so these runs use ngspice, the simulator inside KiCad, which loads the model unmodified. A 3 s run takes about 10 minutes.

Results for the circuit as drawn in KiCad (switch fed from U3B):

| Case | Output | Change from its reference run | Generic model gave |
|------|--------|-------------------------------|--------------------|
| 0 nA | 1.670 mV | n/a | 0.000 mV |
| 10 nA | 6.887 mV | 5.217 mV above 0 nA | 5.22 mV |
| 100 nA | 53.839 mV | 52.168 mV above 0 nA | 52.19 mV |
| 10 nA, 10 degrees late | 6.412 mV | 4.741 mV above 0 nA | 4.74 mV |
| 10 nA, 0.5 mV offset added at the demodulator op amp | 5.887 mV | 1.000 mV from the 10 nA run | 1.00 mV |
| 10 nA, 0.5 mV offset added at the gain stage | 6.876 mV | 0.011 mV from the 10 nA run | 0.01 mV |

- Sensitivity, linearity, timing sensitivity and the offset behaviour all agree with the generic model to better than 0.1 %.
- The 1.67 mV at 0 nA is the model's own input offset, about 0.42 mV per op amp, appearing as the error budget predicts: twice from the demodulator op amp, once from the switch buffer and once from the output buffer. It is removed by the LED-covered reading.
- Output ripple is 2.4 mV peak to peak: narrow spikes at the switching edges. The generic model, with its ideal output, shows 0.05 mV. The average is unaffected, and a multimeter reads the average.
- Solver note: with this model ngspice sometimes stops with "timestep too small" at a switching edge. The 10 nA and gain-stage-offset runs stopped that way with a 20 us maximum step and completed with 15 us. The other runs used 20 us.

What this check found. In the first version the switch took its 2.5 V directly from VREF. With Microchip's model that put spikes of about 0.2 V peak to peak on VREF at every switching edge, and 0.22 V peak to peak on the output. Cause: each time the analog switch connects the demodulator input to 2.5 V, that input's capacitance is recharged from whatever feeds the switch, and VREF has no stiff capacitance on it. The generic model hid this.

Fix, applied to the schematic and board on 2026-10-05: the switch's 2.5 V input (U5 pin 12) is fed from the spare op amp half (U3B, a follower of VREF, net VSW). Spikes on VREF drop from 226 mV to 3 mV peak to peak, and output ripple from 222 mV to 2.4 mV. Cost: no parts; the spare half's offset (about 0.4 mV) adds to the static output offset, which the LED-covered reading already removes. The log file keeps the before-fix results for comparison.

## Timing error and response time

File: `sim/lockin_phase.cir`. The 10 nA signal is delayed against the reference.

| Delay | Output | Relative |
|-------|--------|----------|
| 0 deg | 5.22 mV | 1.00 |
| 10 deg | 4.74 mV | 0.91 |
| 20 deg | 4.26 mV | 0.82 |
| 45 deg | 2.97 mV | 0.57 |
| 90 deg | 0.43 mV | 0.08 |

- About 1 % of reading is lost per degree of timing error. One degree at 1024 Hz is 2.7 us.
- The circuit's own filters shift the signal by a few degrees (the high-pass leads by about 9 deg, the TIA lags by about 4 deg). That is the 5 % gap between 0.522 and the ideal 0.55 mV per nA.
- Response to a signal switched on: 10 % to 90 % in 0.58 s, within 1 % after 1.16 s.

## Expected signal level (estimate, not measured)

Assuming a red LED giving about 5 mW per steradian at 10 mA, and a BPW34 (7.5 mm2, about 0.35 A/W in red):

| LED distance | Photocurrent | Output |
|--------------|--------------|--------|
| 0.1 m | about 1.3 uA | about 0.7 V |
| 0.3 m | about 150 nA | about 76 mV |
| 1 m | about 13 nA | about 7 mV |
| 3 m | about 1.5 nA | about 0.8 mV |

The inverse-square fall-off with distance is a clean experiment for the lab. The LED figure is an assumption until a real LED is measured; the largest signal before clipping is about 3 uA.

## Schematic

Files are in `kicad/`. Open `lockin.kicad_pro` in KiCad.

- `lockin.kicad_sch`: the schematic. `lockin-schematic.pdf` and `.png` are exports for viewing.
- `bom.csv`: parts list exported from the schematic.
- `gen_schematic.py`: the script that drew the schematic. Rerunning it overwrites `lockin.kicad_sch`, so stop using it once the schematic is edited by hand in KiCad.
- `check_netlist.py`: compares KiCad's exported netlist with the intended connections.

Checks, last run 2026-10-06:

- All 27 nets in KiCad's exported netlist match the intended connections.
- KiCad's electrical rule check reports 0 violations.
- The schematic has not been simulated from KiCad; the LTspice files use the same values and connections. The table below lists which LTspice part is which KiCad part.

| Reference | Part | Role |
|-----------|------|------|
| D1 | BPW34 | Photodiode |
| U1A, R1, C1 | MCP6022, 100k, 100p | Transimpedance amplifier |
| C2, R2 | 10n, 100k | 159 Hz high-pass |
| U1B, R3, R4 | MCP6022, 10k, 1k | Gain of 11 |
| U2A, R5, R6, U5 | MCP6022, 10k, 10k, 74HC4053 | Synchronous demodulator |
| R7, C3, R8, C4 | 100k, 1u film, 100k, 1u film | Low-pass filter |
| U2B, R9, R17, J2 | MCP6022, 100, 100, header | Output buffer and connector; R17 is in series with the VREF pin |
| D2, U4, C5, C6, J1 | 1N4148, LP2950-5.0, 1u, 10u electrolytic, header | 5 V supply from the 9 V battery, with reverse-battery protection |
| R10, R11, C7, U3A | 10k, 10k, 10u, MCP6022 | 2.5 V virtual ground |
| U3B | MCP6022 | Separate copy of VREF (net VSW) for the analog switch input, U5 pin 12 |
| U6, Y1, R12, R13, C8, C9 | 74HC4060, 32.768 kHz, 330k, 10M, 22p, 22p | 1024 Hz reference |
| Q1, R14, R15, R16, J3 | 2N7000, 100, 100k, 680, header | LED driver, LED on a lead |
| C10 to C14 | 100n | Decoupling, one per IC |
| TP1 to TP6 | Test loops | TIA output, AC, DEM, REF, VREF, GND: the nodes to probe in the lab |

Names differ between the two tools because the LTspice drawing was made first.

| LTspice name | KiCad name |
|--------------|------------|
| U1, U2 | U1A, U1B |
| U3, U4 | U2A, U2B |
| U5, U6 | U3A, U3B |
| S1, S2 | U5 (74HC4053; one section, two positions) |
| Vclk, Bnb | U6 (74HC4060) and the complement the switch makes internally |
| Rf, Cf | R1, C1 |
| Chp, Rhp | C2, R2 |
| Rg2, Rg1 | R3, R4 |
| Ra, Rb | R5, R6 |
| Rl1, Cl1, Rl2, Cl2 | R7, C3, R8, C4 |
| Rv1, Rv2, Cv | R10, R11, C7 |
| Isig, Iamb, Iflick, Cpd | D1 with its light sources |

Not in the LTspice drawing: the regulator (a 5 V source stands in), the crystal oscillator and LED driver (Vclk stands in), the protection diode D2, R9, R17, decoupling capacitors, connectors and test points.

Design choices worth being able to explain:

- C6 is an electrolytic on purpose: the LP2950 is an older regulator that needs some resistance in its output capacitor to stay stable.
- Unused switch inputs on U5 are grounded, so nothing floats.
- The analog switch takes its 2.5 V from its own buffer (U3B), not from VREF. Each switching edge pulls a small charge from whatever feeds the switch; with a shared VREF that put 0.2 V spikes on the reference of every stage (seen with Microchip's op amp model).
- R9 isolates the output op amp from cable capacitance.
- R17 does the same for the VREF pin of the output connector. The op amp's datasheet says a follower needs a series resistor once the load passes about 60 pF, and multimeter leads can exceed that. Without R17 the meter's leads would hang directly on the 2.5 V reference that every stage uses. Added 2026-10-06.
- D2 is in series with the battery. A 2-pin header is easy to connect backwards, the regulator's datasheet does not mention reverse-battery protection, and a reversed battery could destroy every chip. D2 costs about 0.7 V: the LED current drops from about 10 mA to about 9 mA, and the battery is usable down to about 6.1 V instead of 5.4 V. Added 2026-10-06.
- R15 keeps the MOSFET off if the clock is missing.

## Board (2026-10-04, last regenerated 2026-10-06)

`kicad/lockin.kicad_pcb` is placed and routed by `kicad/gen_board.py`. It is a machine-routed layout: correct and rule-clean, not hand-optimised.

- 90 x 60 mm, 2 layers, four M3 mounting holes.
- Signal chain along the top, virtual ground bottom left, clock bottom centre, regulator, battery connector and LED driver together bottom right so the LED current loop stays local.
- Tracks 0.3 mm, clearance 0.2 mm, vias 0.7 mm with 0.3 mm drill. About 1.10 m of track and 49 vias, 54 footprints.
- Bottom layer is a ground plane. Each surface-mount ground pad has its own via to it. A few signal tracks cross on the bottom where the top was blocked.
- Pin names are printed beside J1, J2, J3 and the photodiode cathode.
- U4 and Q1 use the wide TO-92 footprint (2.54 mm lead spacing), easier to solder by hand.
- C7 is now the same through-hole 10 uF electrolytic as C6.
- D1's holes are 1.0 mm, larger than the library footprint's 0.7 mm, to take the BPW34's flat leads.

Checks: KiCad design rule check reports 0 errors, 0 unconnected items and 0 differences between board and schematic. It reports one expected warning: D1's footprint differs from the library copy, because its holes were enlarged on purpose (see below). Not checked: a manufacturer's own online preview, and the parts in the hand (compare them against a 1:1 printout before soldering).

### Board checked against the datasheets (2026-10-06)

The datasheets are in `datasheets/`. Each row compares the manufacturer's drawing with the pads on the board.

| Part | Datasheet says | Board has | Result |
|------|----------------|-----------|--------|
| U4 regulator, LP2950ACZ-5.0 (TO-92) | Pin 1 output, 2 ground, 3 input | Pad 1 +5V, pad 2 GND, pad 3 +9V | Matches |
| Q1 MOSFET, 2N7000 (TO-92). Diotec datasheet read 2026-10-06; onsemi datasheet NDS7002A/D rev. 11 read 2026-10-09 (the ordered part is onsemi): pin 1 source, 2 gate, 3 drain | Source, gate, drain, left to right facing the flat | Pad 1 GND, pad 2 gate, pad 3 drain to the LED | Matches |
| U1, U2, U3 op amp, MCP6022 (SOIC-8) | Out A 1, in- A 2, in+ A 3, VSS 4, in+ B 5, in- B 6, out B 7, VDD 8 | Same pins as drawn in the schematic | Matches |
| U5 switch, 74HC4053D | 1Y0 pin 12, 1Y1 pin 13, 1Z pin 14, S1 pin 11, enable pin 6, VEE 7, GND 8 | Same pins as drawn in the schematic | Matches |
| U6 divider, 74HC4060D | Oscillator pins 11, 10; reset 12; divide-by-32 output on pin 5 | Same pins; REF taken from pin 5 | Matches |
| D1 photodiode, Vishay BPW34 | Lead spacing 5.1 mm; flat leads 0.7 to 0.8 mm wide, 0.3 mm thick | Spacing 5.08 mm; holes were 0.7 mm | Fixed: holes enlarged to 1.0 mm, pads to 1.8 mm |
| C3, C4 film, KEMET R82DC4100AA60J | Body 7.2 x 5.0 mm, lead spacing 5.0 mm, lead 0.5 mm | Outline 7.2 x 4.5 mm, spacing 5.0 mm, hole 0.8 mm | Fits: the part is 0.25 mm wider per side than drawn, inside the keep-clear area |
| D2 diode, 1N4148 (DO-35) | Glass body up to 4.25 x 1.85 mm, leads up to 0.56 mm, band marks the cathode (Nexperia datasheet; the onsemi one could not be downloaded, the package is a standard) | Holes 0.8 mm, 7.62 mm apart, band printed at the cathode end, cathode to the regulator side | Matches |
| Y1 crystal, Abracon AB26T | Can 2.1 x 6.2 mm, leads 0.26 mm thick and 0.8 mm apart | Holes 0.5 mm, 1.9 mm apart | Fits: spread the two leads slightly, as the footprint intends |

- C6, C7 electrolytic, Panasonic ECA-1HM100: the datasheet gives a 5 mm can, 11 mm tall, 0.5 mm leads 2.0 mm apart. The board has a 5 mm outline, 0.8 mm holes 2.0 mm apart. Matches.
- Regulator stability. The LP2950-N datasheet asks for at least 1 uF on the output, says most aluminium electrolytics work, and recommends 10 uF or more against overshoot. Its stability graph (figure 37, drawn for 2.2 uF) allows a capacitor series resistance up to roughly 30 to 40 ohms at 10 mA of load, falling to about 17 ohms at 25 mA. This circuit draws about 7 mA from the 5 V rail (the LED runs from 9 V). The Panasonic datasheet gives only a loss factor of 0.12 at 120 Hz, which works out to at most 16 ohms at that frequency; it gives no figure at higher frequencies, where the resistance is normally lower. So C6 is inside the datasheet's stable region as far as the two datasheets can show. It is not a guarantee, because the graph is for 2.2 uF and C6 is 10 uF; the build guide has a scope check on the 5 V rail and a fallback.
- The op amp datasheet is `MCP6021-Data-Sheet-DS20001685.pdf` in the project folder.

### Manufacturing files checked against the board (2026-10-06)

The gerber and drill files inside `lockin-gerbers.zip` were read back as plain text by a separate script and compared with the board file:

- 12 files: two copper layers, two solder masks, two silkscreens, two paste layers, the outline, two drill files and the job file.
- All 86 drilled holes in the drill files match a pad, via or mounting hole on the board in position and size, and none is missing: 49 vias of 0.3 mm, 2 of 0.5 mm, 16 of 0.8 mm, 15 of 1.0 mm, 4 mounting holes of 3.2 mm.
- All 143 copper pads on the top side and all 49 vias appear on the top copper layer at the same coordinates.
- The outline is 90.00 x 60.00 mm and every hole is inside it; the closest hole edge is 2.4 mm from the board edge.
- Track width 0.3 mm and clearance 0.2 mm are wider than the 0.127 mm minimum JLCPCB lists for 2-layer boards; vias of 0.7 mm with 0.3 mm holes meet its 0.3 mm minimum hole. Those limits come from a web search, not from the maker's own page.

This checks that the files say what the board says. It does not replace looking at the maker's preview after uploading.

Outputs in `kicad/`: `lockin-gerbers.zip` (files to order the board), `lockin-board.png` (copper view), `lockin-board-3d.png` (rendered view), `drc.rpt`.

`build_all.ps1` regenerates all of this. Do not run it, or `gen_board.py`, after editing the board by hand in KiCad: they overwrite it.

Build and test steps are in `BUILD-GUIDE.md`.

## Layout guidelines the placement follows

1. Keep the photodiode, R1, C1 and U1 pin 2 as close together as possible. This node carries nanoamps and picks up anything nearby.
2. Keep the 1024 Hz clock trace and the LED driver on the opposite side of the board from that node.
3. Keep the LED current loop short and away from the amplifiers: the LED driver sits next to the battery connector.
4. Put each 100 nF capacitor right at its IC's supply pins.
5. Use a ground plane on the bottom layer.
6. Place the six test points along one board edge where a scope probe can reach them.

## Lab measurements to plan for

1. Stage by stage with a signal generator in place of the photodiode: gain and corner frequencies against the numbers above.
2. Output against LED distance or a series of neutral filters: linearity.
3. Output with LED covered: offset and its drift over ten minutes.
4. Room lights on and off with LED running: interference rejection.
5. Output noise with a multimeter logging over a minute.

## Not yet done

- Noise simulation with Microchip's model (done only with datasheet figures in the generic model).
- Measured LED output, to replace the assumed figure.
- A manufacturer's online preview of the gerber files.
- Board ordered, built and measured. There is no breadboard build: the board is assembled and tested in stages (see `BUILD-GUIDE.md`).
