# Lab day: what to prepare at home, what to bring

Written 2026-10-24, when the PCBWay boards arrived (5 lock-in, 5 smart socket, checked from photos).
Everything here is done WITHOUT soldering, so the lab visit is only soldering and the checks in
`BUILD-GUIDE.md` (lock-in) and `smart-socket/BUILD-GUIDE.md`.

IDX = the line number printed on each DigiKey bag (order 102158958).

## 1. Bare-board checks (multimeter on resistance, nothing fitted)

Use one board of each; any of the 5.

| Board | Between | Must read |
|---|---|---|
| Lock-in | J1 pin +9V and J1 pin GND | open (display shows 1) |
| Lock-in | TP5 (VREF) and TP6 (GND) | open |
| Smart socket | J1 hole GND (square, labelled) and J1 hole VBUS | open |
| Smart socket | J2 +5V and J2 GND | open |

A low reading on a bare board means a manufacturing short: stop and tell Claude.

## 2. Dry fit on a spare board (push parts in, no solder, then take them out)

The point is to find any part whose legs do not match the holes before the lab.

Lock-in board:
- D1 photodiode (IDX 26): flat legs into the two D1 holes, cathode (tab leg) at K.
- Y1 crystal (IDX 1): legs spread gently to reach the holes.
- U4 regulator, Q1 2N7000: outer legs bent slightly outward (holes 2.54 mm apart).
- C3, C4 film 1 uF (IDX 29), C6, C7 10 uF (IDX 28, long leg at +), D2 1N4148 (IDX 27, band at the printed band).
- Header pins for J1 (2), J2 (3), J3 (2).

Smart socket board:
- **Most important: the two modules.** Push the header strips into the board, then sit the XIAO
  (IDX 18) on the 2 x 7 pins with its USB port at the edge labelled "U1 USB this edge", and the
  USB-C socket board (IDX 48) on the 8 pins, parts up, socket out of the left end, its GND pad on
  the hole labelled GND. Both must drop on without forcing. Tell Claude if they do not.
- One resistor lying flat on the underside, legs bent to the hole spacing (7.62 mm).
- D1 1N5817 (IDX 49), C1 to C3 discs (IDX 32), Q2 2N7000 (IDX 2), LED1 (IDX 3).
- Q1 SI4435 (IDX 50): only lay it on its 8 pads to see it lines up (dot at the pad by the triangle).

## 3. Sort the parts into two kits

Measure each loose leaded resistor with the meter (the colour bands are hard to read) and write the
value on its strip. Keep the tiny 0805 parts in their labelled tape: the capacitors carry no marking
and cannot be told apart once loose.

### Lock-in kit

| Refs | Part | IDX | Qty |
|---|---|---|---|
| R1, R2, R7, R8, R15 | 100 k, 0805 | 40 | 5 |
| R3, R5, R6, R10, R11 | 10 k, 0805 | 39 | 5 |
| R4 | 1 k, 0805 | 38 | 1 |
| R9, R14, R17 | 100 ohm, 0805 | 36 | 3 |
| R12 | 330 k, 0805 | 41 | 1 |
| R13 | 10 M, 0805 | 42 | 1 |
| R16 | 680 ohm, 0805 | 37 | 1 |
| C1 | 100 pF, 0805 | 44 | 1 |
| C2 | 10 nF, 0805 | 45 | 1 |
| C5 | 1 uF, 0805 | 47 | 1 |
| C8, C9 | 22 pF, 0805 | 43 | 2 |
| C10 to C14 | 100 nF, 0805 | 46 | 5 |
| C3, C4 | 1 uF film | 29 | 2 |
| C6, C7 | 10 uF electrolytic | 28 | 2 |
| U1, U2, U3 | MCP6022 SOIC-8 (chips marked 6022) | 17 | 3 |
| U5 | 74HC4053D SOIC-16 | 34 | 1 |
| U6 | 74HC4060D SOIC-16 | 35 | 1 |
| U4 | LP2950-5.0: **the good one from the breadboard** (not the one that drew 19 mA) | 4 | 1 |
| Q1 | 2N7000 | 2 | 1 |
| Y1 | 32.768 kHz crystal | 1 | 1 |
| D1 | BPW34 photodiode | 26 | 1 |
| D2 | 1N4148 | 27 | 1 |
| LED | red 5 mm, on two twisted wires about 10 cm long | 3 | 1 |
| J1, J2, J3 | pin header strip, 2 + 3 + 2 pins | owned | 7 pins |
| TP1 to TP6 | loops of offcut wire | | 6 |
| | 9 V clip and battery | 5, 22 | 1 each |

### Smart socket kit

| Refs | Part | IDX | Qty |
|---|---|---|---|
| R1, R2, R6 | 330 k leaded | 13 | 3 |
| R3 | 33 k leaded | 21 | 1 |
| R4 | 12 k leaded | 20 | 1 |
| R5 | 4.7 k leaded | 23 | 1 |
| R7, R8 | 100 k leaded | 30 | 2 |
| R9 | 680 ohm leaded | 10 | 1 |
| R10 | 1 k leaded | 11 | 1 |
| C1, C2, C3 | 100 nF disc | 32 | 3 |
| D1 | 1N5817 | 49 | 1 |
| Q1 | SI4435DDY SOIC-8 (marked 4435) | 50 | 1 |
| Q2 | 2N7000 | 2 | 1 |
| LED1 | red 5 mm | 3 | 1 |
| J1 | USB-C socket board + 8-pin header | 48 | 1 |
| U1 | XIAO ESP32-C3 + two 7-pin headers, antenna | 18 | 1 |
| J2 | USB-C to USB-C cable (USB 2.0, 3 A / 60 W), cut, three wires found | buy | 1 |

## 4. Bring to the lab

Both kits, one board of each plus one spare, the multimeter, the breadboard (for the good LP2950,
and as the working reference), side cutters, tweezers for the 0805 parts, the laptop, a USB-C
charger with its cable, the phone, and both build guides (`BUILD-GUIDE.md`,
`smart-socket/BUILD-GUIDE.md`). The lab has the soldering iron, solder and flux.

## 5. Done on the computer before the lab

- XIAO plugged into the laptop: load the firmware fix (wrong-PIN upload no longer restarts it), try
  the Windows app's "Set up over USB" and "Load a new program" on the real socket.
