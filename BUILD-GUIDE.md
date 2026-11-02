# Project 1 build guide

Rewritten 2026-10-06; updated 2026-10-16 after the breadboard build. The whole circuit was proven on
the breadboard on 2026-10-15 and 16 (see `../PLAN.md`), so the checks below now give the readings
the breadboard actually showed, measured with the DT-830B. Every check can be done with the
multimeter alone; the oscilloscope steps are optional extras for the lab.

Board ordered from PCBWay on 2026-10-16 (5 copies). Differences from the breadboard:
- U5 is the real 74HC4053 switch (SOIC). The breadboard used a 2N7000 in its place, so stage 6 is
  the one stage that runs on new hardware.
- Use the LP2950 that worked on the breadboard (the spare, drawing about 12 mA in total). Keep the
  first one, which drew 19 mA on its own, out of the board.
- No 100 ohm resistor in the battery lead: D2 already protects the board, and the board has no long
  legs that can touch.

## How this replaces the breadboard

The board is soldered and tested one section at a time. Each stage adds a few parts and ends with a
check. A fault then shows up while only a few parts are on the board, so it is easy to find, the
same benefit a breadboard gives.

Rules:

- Disconnect the battery while soldering.
- Do not go on to the next stage until the current stage passes its check.
- If a check fails, stop and send a photo of the board and the reading.

The board's pin order was checked against the datasheets of the parts on the buy list (see `DESIGN.md`).
If you receive an alternate part instead, check its pinout first: the regulator must be output, ground,
input and the MOSFET source, gate, drain, left to right facing the flat (a BS170 has a different order).

## Before soldering anything

1. Print `kicad/lockin-board.png` at 100 % scale, or hold the bare board itself, and lay each
   through-hole part over its holes: photodiode, crystal, regulator, MOSFET, diode, film capacitors,
   electrolytic capacitors. The legs must line up with the holes.
2. With a multimeter on resistance, measure between the two pins of J1 on the bare board (+9V and GND
   are printed beside them). It must read open circuit, not a short.

Part values are printed next to each part in `kicad/lockin-schematic.pdf`; the board shows only the
reference (R1, C1, ...). The value table is at the end of this guide.

Soldering notes:

- Surface-mount chips (U1, U2, U3, U5, U6): the small triangle printed on the board marks pin 1. The
  chip has a dot or a bevelled edge on the pin 1 side.
- Electrolytic capacitors (C6, C7): the longer leg goes in the hole marked +.
- Diode D2: the band printed on the diode goes at the end where the board outline shows a band.
- Regulator U4 and MOSFET Q1: match the flat face to the outline. Their holes are spread apart, so
  bend the outer legs slightly outward (the 2N7000 may arrive with its legs already spread).
- Crystal Y1: its two legs are closer together than the holes. Spread them gently before inserting.
- Photodiode D1: the cathode leg goes in the hole marked K. The cathode is the leg with the small tab
  near the body (see the drawing in `datasheets/BPW34.pdf`, page 4).

## Stage 0: test points and connectors

Fit: TP1 to TP6 (a small loop of offcut wire in each hole), J1, J2, J3 (2, 3 and 2 pins snapped
off the pin header strip).

TP6 is ground: clip the scope probe's ground lead and the multimeter's black lead there for every
check below.

## Stage 1: supply

Fit: D2, C5, U4, C6.

Check:

- Measure J1 again with the multimeter on resistance: still not a short.
- Connect the 9 V battery to J1. The clip's red wire goes to the pin marked +9V. (If it is connected
  backwards, D2 blocks it and nothing happens.)
- The + leg of C6 reads 4.9 to 5.05 V (the breadboard rail read 4.9 V on the DT-830B).
- Scope on the + leg of C6 (AC coupling, 10 mV per division): the trace must be flat. A steady sine
  wave of tens of millivolts means the regulator is oscillating. Fix: replace C6 with a 10 uF
  tantalum capacitor in the same holes.

## Stage 2: 2.5 V reference

Fit: R10, R11, C7, C12, U3.

Check:

- TP5 (VREF) reads 2.45 to 2.55 V.
- U3 pin 7 reads the same as TP5 to within a millivolt or so. This is VSW, the separate copy used
  by the switch.

## Stage 3: 1024 Hz clock

Fit: C14, U6, R12, R13, C8, C9, Y1.

Check with the multimeter on DC volts: TP4 (REF) reads about half the supply, 2.4 to 2.5 V (the
breadboard read 2.45 V). The meter averages the square wave: 0 V or about 4.9 V means the clock is
not running. Optional, with a scope: a square wave, 0 to 5 V, 1024 Hz, 50 % duty.

If there is no square wave:

1. Look at the solder joints on U6 pins 10, 11 and 16, and on R12, R13, C8, C9.
2. If it still does not start, remove Y1. Set the signal generator to a square wave, 0 to 5 V,
   32.768 kHz, and connect it to the Y1 hole nearer U6 (generator ground to TP6). U6 then divides
   that down and TP4 shows 1024 Hz. Carry on with the build; the rest of the circuit does not care
   where the clock comes from.

## Stage 4: LED driver

Fit: R14, R15, R16, Q1. Solder two wires about 10 cm long to the LED, twist them together, and
connect them to J3: the LED's long leg (anode) to the pin marked A, the short leg to K. The wires let
the LED sit right at the photodiode later, which the breadboard showed matters (170 to 176 mV with
the LED right at the photodiode, about 70 mV with it tilted away).

Check:

- The LED looks steadily lit (it is blinking too fast to see).
- The K pin of J3 reads somewhere between about 1 and 3 V on DC volts, not stuck near 0 V or near
  the supply (the meter averages the LED being switched on and off).
  Optional: a 1024 Hz square wave on the scope.
- Battery current, if you measure it: roughly 10 to 15 mA (the breadboard drew 12 mA). Much more
  means stop.

## Stage 5: photodiode amplifier and gain

Fit: R1, C1, C10, U1, C2, R2, R3, R4, D1.

Check (LED covered or pointed away first):

- TP1 with the photodiode covered: equal to TP5.
- TP1 in room light: above TP5 by 0.1 V for each microamp of light. If it sits near 5 V the light is
  too bright: shade the photodiode.
- If TP1 goes below TP5 in light, the photodiode is in backwards.
- Point the LED at the photodiode: on DC volts TP1 rises a little above TP5. Optional, with a
  scope: a 1024 Hz square wave on TP1, and 11 times larger on TP2, centred on 2.5 V.

## Stage 6: demodulator

Fit: R5, R6, C11, U2, C13, U5.

Check with the multimeter on DC volts: with the LED covered, TP3 (DEM) reads the same as TP5. With
the LED pointed at the photodiode, TP3 reads above TP5. If it reads below TP5, the LED wires are
swapped at J3. If it does not move at all, U5 is not switching: check that U5 pin 11 reads about
half the supply (the clock arrives), and the joints on U5 pins 6, 7, 8, 12, 13, 14 and 16.
Optional, with a scope: the square wave folded to one side of 2.5 V, with short spikes at each edge.

## Stage 7: filter and output

Fit: R7, R8, C3, C4, R9, R17.

Read the output with the multimeter on DC volts between the OUT pin (+) and the VREF pin (-) of J2.

Check:

- LED unplugged from J3: within about 2 mV of zero (the breadboard read 0.0 mV). Write this reading
  down: it is the offset to subtract from every later reading.
- LED right at the photodiode: a steady positive voltage that settles in about a second. The
  breadboard read 170 to 176 mV; the board should be in the same range (it depends on how close the
  LED is).
- LED tilted away: a smaller reading (the breadboard read 70 to 72 mV).
- Room light on and off, or dim daylight added: the reading changes by about 1 % or less (the
  breadboard: 176 to 178 mV). This is the result the project exists to show.

## Value table

| Reference | Value | | Reference | Value |
|-----------|-------|-|-----------|-------|
| R1, R2, R7, R8, R15 | 100 k | | C1 | 100 pF |
| R3, R5, R6, R10, R11 | 10 k | | C2 | 10 nF |
| R4 | 1 k | | C3, C4 | 1 uF film |
| R9, R14, R17 | 100 ohm | | C5 | 1 uF 0805 |
| R12 | 330 k | | C6, C7 | 10 uF electrolytic |
| R13 | 10 M | | C8, C9 | 22 pF |
| R16 | 680 ohm | | C10 to C14 | 100 nF |
| D2 | 1N4148 | | Y1 | 32.768 kHz crystal |

## Ordering the board

Ordered 2026-10-16 from PCBWay: `kicad/lockin-gerbers.zip`, 2 layers, 90 x 60 mm, 1.6 mm, HASL lead
free, green, 5 copies, together with the smart socket board. PCBWay read the file as a 2-layer
90 x 60 mm board and passed its automatic check. When the boards arrive, compare one with
`kicad/lockin-board.png` before soldering.

## What to bring back for debugging

A photo of the board and the multimeter reading from each check (and, if a scope is to hand,
screenshots of TP1, TP2, TP3 and TP4 with the LED pointed at the photodiode).
