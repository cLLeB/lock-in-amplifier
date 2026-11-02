# Breadboard guide: lock-in amplifier

Written by `breadboard/gen_breadboard.py`, which also checks that the wiring below gives exactly the
connections of the schematic (27 nets). Do not edit the tables by hand: change the script and run it again.

Nothing has been built yet. Every expected value comes from calculation or simulation.

Picture of the finished breadboard: `breadboard/breadboard-layout.png`. Keep it open while building.

## How to read a hole name

- Hold the breadboard upright, row 1 at the top. Columns are lettered a to j, left to right.
- A hole is a column letter and a row number: `e12` is column e, row 12.
- In one row, holes a to e are joined together, and holes f to j are joined together. The two halves
  are not joined across the centre gap.
- The four long rails at the sides are used like this:

| Rail | Position | Carries |
|---|---|---|
| L+ | left, outer | VREF (2.5 V) |
| L- | left, inner | ground |
| R- | right, inner | ground |
| R+ | right, outer | +5 V |

Your breadboard's rails may be printed in a different left-to-right order. What matters is that the two
rails on each side are the two listed, and that you always use the same one for the same purpose.

## Before you start

1. **Check the rails.** On many breadboards each rail is cut in the middle. With the multimeter on
   continuity, test from the top hole to the bottom hole of each of the four rails. If one does not beep,
   join its two halves with a short wire across the break.
2. **Prepare the battery clip.** Its wires are soft and will not push into the holes. At the lab, solder
   each wire to one pin snapped off your pin header strip. Do not connect the battery yet.
3. **Chips.** Each chip sits across the centre gap with its notch (or dot) toward row 1. Pin 1 is then at
   the top left. Straighten the legs gently against the table first so they drop into the holes.
4. **Three-leg parts** (U4 and Q1): spread the three legs slightly so each goes in its own row.
5. **Short links.** Three wires join two neighbouring rows. A bent offcut of resistor leg does the same
   job and saves your jumper wires.
6. **Measuring.** The black lead of the multimeter and the ground clip of the scope probe go on the
   L- rail: push a wire into the rail and clip onto it. To measure a row, push a wire into any free
   hole of that half-row and touch or clip onto the wire.

Rules: disconnect the battery before adding parts. Do not go on until the check of the stage passes.
If a check fails, stop and send a photo and the reading.

The whole build uses 42 parts and 37 wires.

## Stage 1: 5 V supply

Turns the 9 V battery into a steady 5 V on the R+ rail.

| Part | Value | Goes in | Note |
|---|---|---|---|
| U4 | LP2950-5.0 | h3 and h4 and h5 | flat face toward the centre gap |
| C6 | 10 uF | g3 and g4 | long leg (+) in g3 |
| C5 | 10 uF | i5 and i4 | long leg (+) in i5 |
| D2 | 1N4148 | f5 and f8 | black band end in f5 |

| Wire from | To | What it does |
|---|---|---|
| L- | R- | joins the two ground rails (at row 62) |
| j3 | R+ | +5V to the right rail |
| j4 | R- | regulator ground |

Check:

- With the multimeter on continuity, R+ to R- must not beep.
- Battery: red wire into **g8**, black wire into the **R-** rail. If the battery is the wrong way round,
  the diode blocks it and nothing happens.
- R+ rail reads 4.95 to 5.05 V. L- and R- read 0 V between them.
- Scope on the R+ rail, AC coupling, 10 mV per division: flat. A steady sine wave means the regulator is
  oscillating: send a screenshot.

## Stage 2: 2.5 V reference

Makes VREF, the 2.5 V that every amplifier stage uses as its zero, and puts it on the L+ rail.

| Part | Value | Goes in | Note |
|---|---|---|---|
| U3 | MCP6022 | rows 23 to 26, across the centre gap, pin 1 in e23 | notch toward row 1 |
| R10 | 10 k | the R+ rail and j27 |  |
| R11 | 10 k | a25 and the L- rail |  |
| C7 | 10 uF | c25 and c26 | long leg (+) in c25 |
| C12 | 100 nF | the R+ rail and the R- rail, level with row 23 | plugs into the two right-hand rails |

| Wire from | To | What it does |
|---|---|---|
| j23 | R+ | U3 supply |
| a26 | L- | U3 ground |
| b23 | b24 | U3 pin 1 to pin 2 (short link) |
| a23 | L+ | VREF to the left rail |
| L+ | g26 | VREF to U3 pin 5. Go round the bottom end of U3 |
| g27 | b25 | R10 to U3 pin 3. Go round the bottom end of U3 |
| h24 | h25 | U3 pin 7 to pin 6 (short link) |

Check:

- L+ rail reads 2.45 to 2.55 V.
- Row 24, right half (U3 pin 7): the same as L+ to within a few millivolts. This is VSW, the separate
  copy for the switch.

## Stage 3: 1024 Hz clock

The crystal and U6 make the 1024 Hz square wave that drives both the LED and the switch.

| Part | Value | Goes in | Note |
|---|---|---|---|
| U6 | 74HC4060 | rows 10 to 17, across the centre gap, pin 1 in e10 | notch toward row 1 |
| C14 | 100 nF | the R+ rail and the R- rail, level with row 10 | plugs into the two right-hand rails |
| R13 | 10 M | g16 and g20 |  |
| R12 | 330 k | h21 and h16 |  |
| Y1 | 32.768 kHz | f21 and f20 | either way round; spread the two legs |
| C9 | 22 pF | i20 and i22 | spread the legs to span two rows |
| C8 | 22 pF | j21 and j22 |  |

| Wire from | To | What it does |
|---|---|---|
| j10 | R+ | U6 supply |
| a17 | L- | U6 ground |
| j14 | R- | U6 reset held low |
| i15 | j20 | U6 pin 11 to the crystal |
| g22 | R- | ground for C8 and C9 |

The crystal's legs are very thin. Push them straight down and check the crystal does not wobble.

Check: scope on row 14, left half (U6 pin 5): square wave, 0 to 5 V, 1024 Hz, half the time high.

If there is no square wave:

1. Press the crystal, R12, R13, C8 and C9 down and look again.
2. If it still does not start, pull the crystal out. Set the signal generator to a square wave, 0 to 5 V,
   32.768 kHz, and connect it to row 15, right half (U6 pin 11), generator ground to L-. Row 14 then shows
   1024 Hz. Carry on; the rest of the circuit does not care where the clock comes from.

## Stage 4: LED driver

The MOSFET switches the LED on and off 1024 times a second.

| Part | Value | Goes in | Note |
|---|---|---|---|
| R16 | 680 | g5 and d5 | crosses the centre gap |
| LED | red LED | c5 and c6 | long leg in c5 |
| Q1 | 2N7000 | b6 and b7 and b8 | flat face toward the centre gap |
| R15 | 100 k | a7 and the L- rail |  |
| R14 | 100 | c14 and c7 | lies over rows 8 to 13 |

| Wire from | To | What it does |
|---|---|---|
| a8 | L- | MOSFET source to ground |

Check:

- The LED looks steadily lit (it blinks too fast to see).
- Scope on row 6, left half: a square wave at 1024 Hz.
- If the LED is dark, it is probably the wrong way round: swap its two legs.

## Stage 5: Photodiode amplifier and gain

U1 turns the photodiode's current into a voltage, removes the steady part and amplifies the rest 11 times.

| Part | Value | Goes in | Note |
|---|---|---|---|
| U1 | MCP6022 | rows 30 to 33, across the centre gap, pin 1 in e30 | notch toward row 1 |
| C10 | 100 nF | the R+ rail and the R- rail, level with row 30 | plugs into the two right-hand rails |
| R1 | 100 k | d31 and d30 | stand it on end (rows next to each other) |
| C1 | 100 pF | c31 and c30 |  |
| C2 | 10 nF | b30 and b29 |  |
| R2 | 100 k | a29 and the L+ rail |  |
| R3 | 10 k | g32 and g31 | stand it on end |
| R4 | 1 k | h32 and h36 |  |
| D1 | BPW34 | b31 and b33 | leg with the small tab (cathode) in b31 |

| Wire from | To | What it does |
|---|---|---|
| j30 | R+ | U1 supply |
| a33 | L- | U1 ground |
| a32 | L+ | VREF to U1 pin 3 |
| d29 | g33 | high-pass output to U1 pin 5. Go round the top end of U1 |
| g36 | L+ | VREF to R4. Go round the bottom end of U1 |

The photodiode faces up. Start with the LED pointing up as well and hold a sheet of white paper about
10 cm above the board, so the photodiode sees the LED by reflection. Pointing the LED straight at the
photodiode from a few centimetres is too strong and overloads the amplifier.

Check:

- Row 30, left half (TIA) with the photodiode covered: equal to L+ (2.5 V).
- Same row in room light: above 2.5 V, by 0.1 V for each microamp of light. If it sits near 5 V the light
  is too bright: shade the photodiode. If it goes below 2.5 V, the photodiode is the wrong way round.
- With the paper in place: a small 1024 Hz square wave on row 30, left half, and the same wave 11 times
  larger on row 31, right half (AC), centred on 2.5 V. The 100 Hz ripple from the room lights is also
  visible there; that is expected.

## Stage 6: Demodulator

The switch U5 and the op amp U2 flip the signal in step with the clock, so the LED's light becomes a steady level.

| Part | Value | Goes in | Note |
|---|---|---|---|
| U5 | 74HC4053 | rows 37 to 44, across the centre gap, pin 1 in e37 | notch toward row 1 |
| C13 | 100 nF | the R+ rail and the R- rail, level with row 37 | plugs into the two right-hand rails |
| U2 | MCP6022 | rows 48 to 51, across the centre gap, pin 1 in e48 | notch toward row 1 |
| C11 | 100 nF | the R+ rail and the R- rail, level with row 48 | plugs into the two right-hand rails |
| R5 | 10 k | d45 and d49 |  |
| R6 | 10 k | c49 and c48 | stand it on end |

| Wire from | To | What it does |
|---|---|---|
| j37 | R+ | U5 supply |
| a42 | L- | U5 pin 6 to ground |
| a43 | L- | U5 pin 7 to ground |
| a44 | L- | U5 pin 8 to ground |
| j43 | R- | U5 pin 10 to ground |
| j44 | R- | U5 pin 9 to ground |
| h31 | h40 | AC signal to U5 pin 13 |
| i25 | i41 | VSW to U5 pin 12 |
| b14 | j42 | 1024 Hz clock to U5 pin 11. Lay it along the right-hand edge |
| j48 | R+ | U2 supply |
| a51 | L- | U2 ground |
| g40 | c45 | AC signal to R5 |
| h39 | c50 | U5 pin 14 to U2 pin 3 |

The clock wire (b14 to j42) is the one wire to keep away from the photodiode end of U1: lay it out
past the right-hand edge of the board.

Check: with the paper in place, row 48, left half (DEM) shows the square wave folded to one side of 2.5 V
(always above it), with short spikes at each switching edge. If it is always below 2.5 V, U5 is not
switching: check row 42, right half (U5 pin 11) for the 1024 Hz clock.

## Stage 7: Filter and output

Two slow filters keep only the steady level. The meter reads it between OUT and VREF.

| Part | Value | Goes in | Note |
|---|---|---|---|
| R7 | 100 k | b48 and b54 |  |
| C3 | 1 uF film | c54 and c56 |  |
| R8 | 100 k | d54 and g51 | crosses the centre gap |
| C4 | 1 uF film | h51 and h53 |  |
| R9 | 100 | j50 and j56 |  |
| R17 | 100 | g58 and g53 |  |

| Wire from | To | What it does |
|---|---|---|
| h49 | h50 | U2 pin 7 to pin 6 (short link) |
| a56 | L+ | VREF to C3 |
| b56 | i53 | VREF to C4 and R17 |

Multimeter on DC volts: red lead on a wire in **i56** (OUT), black lead on a wire in **i58** (VREF).

Check:

- LED pulled out or covered: within about 2 mV of zero. Write this number down: it is the offset to
  subtract from every later reading.
- LED back, paper in place: a steady positive voltage, 0.52 mV for each nanoamp of signal. It settles
  in about a second. Move the paper closer and the reading rises.
- Room lights on and off: the reading should not change. This is the result the project exists to show.

Send me the three readings and scope screenshots of rows 30 (left), 31 (right), 48 (left) and 14 (left).

## What is different from the circuit board

| On the breadboard | On the board | Why |
|---|---|---|
| C5 is a 10 uF electrolytic | 1 uF ceramic | Saves buying one more type with legs |
| The five 100 nF capacitors sit across the right-hand rails | One at each chip's supply pins | Their legs are too short to reach from a chip to a rail |
| U5 pins 1, 2, 3 and 5 are left open | Tied to ground | They are the ends of unused switches; open is harmless and saves four wires |
| C2 (10 nF) is a less precise type | Precise type | The precise one with legs was out of stock; the reading may be a few percent off |
| No test points | TP1 to TP6 | Any free hole of a row does the job |

A breadboard adds stray capacitance and picks up more hum than a board. Expect the same behaviour and
roughly the same numbers, not identical ones.

## Not checked

- Nothing here has been built.
- The pin numbers of the plug-in 74HC4053 are taken to be the same as the flat version (they are the
  same chip in another package); only the 74HC4060's were read from the plug-in datasheet.
- Whether the breadboard you receive has its rails cut in the middle (step 1 above finds out).
