// Case for the lock-in amplifier, board kicad/lockin.kicad_pcb (90 x 60 x 1.6 mm), with its 9 V battery.
// Open in OpenSCAD (free), press F6, export STL. The same geometry is built without OpenSCAD by
// make_case_stl.py (Python, trimesh + manifold3d); keep the two files in step when changing a number.
//
// DRAFT: never printed. Positions come from the board file; heights are estimates from the parts'
// datasheets. Check them against the assembled board before printing.
//
// No screws, no extra parts:
// - Board: rests on 4 standoffs in the base; a pin on each standoff goes up through the M3 hole.
//   4 tubes under the lid come down onto the board around the holes and clamp it when the lid is on.
// - Battery: lies flat in a bay at the right (J1) end, behind a low divider wall. The wall has a
//   notch where the clip wires go over to J1. Change the battery by pulling the lid off.
// - Lid: a friction-fit lip into the base (as on the smart socket case), printed outer face down.
// - Light: a separate LED holder. Its flange sits on the lid; its tube goes down through a window
//   over the photodiode D1, and the LED pushed in from the top stops on a step inside, so its tip is
//   always led_gap above D1. The LED wires go back into the case through a 6.2 mm hole beside it
//   (6.2 rather than 4 mm so the LED, already soldered to its wires, can be threaded through it).
// - Output: one window over J2's three header pins (OUT, VREF, GND), labels engraved beside it. The
//   multimeter probes go in through the window and touch the pin tips. Nothing to solder.
// - Not light-tight: the lock-in rejects room light, so it does not need to be.
//
// Board coordinates (KiCad): x from the left edge, y DOWN from the top edge (the test point edge).
// Case coordinates: x to the right, y UP from the front wall (the board's bottom edge, H3/H4 side),
// z up from the bed. So y_case = 60 - y_kicad (plus the wall and gap), see cx(), cy() below.

$fn = 48;

// ---- from the board file ----
board_l = 90;
board_w = 60;
board_t = 1.6;
holes   = [[4, 4], [86, 4], [4, 56], [86, 56]];   // M3 mounting holes, 3.2 mm
d1_x    = 8;          // photodiode D1 centre (between its pads at y 10.97 and 16.05)
d1_y    = 13.51;
j2_x    = 86;         // J2 pads: OUT, VREF, GND, 1 mm holes
j2_y    = [12.05, 14.59, 17.13];
j2_name = ["OUT", "VREF", "GND"];
j1_y    = 48.32;      // J1 battery clip wires (pads at y 47.05 and 49.59, x 86)

// ---- estimates: measure on the assembled board ----
top_h   = 15;         // clearance above the board top (measured 2026-10-28: tallest part 13 mm, plus 2 mm room)
under_h = 5;          // standoff height (underside joints and cut legs up to ~2 mm)
d1_h    = 1.5;        // top of D1 above the board
led_gap = 3;          // LED tip to D1 top
led_d   = 5;          // LED body diameter
led_rim = 5.8;        // LED flange (rim) diameter
led_len = 7.6;        // LED from dome tip to the underside of its rim
bat     = [26.5, 48.5, 17.5];   // 9 V battery lying flat: across x, along y, height
pin_top = 8.5;        // J2 header pin tips above the board (2.5 mm plastic + 6 mm pin)

// ---- printing choices ----
wall   = 2.0;         // side walls and floor
lid_t  = 2.0;         // lid plate
gap    = 0.4;         // clearance around the board
lip    = 3.0;         // how far the lid lip drops into the base
lip_w  = 1.2;         // lip thickness
fit    = 0.15;        // lip to wall clearance (friction fit; sand or add tape if loose)
div_t  = 1.6;         // divider wall between board and battery
div_h  = 10;          // divider height above the floor
bay_l  = bat[0] + 1;  // battery bay width (x)
pin_d  = 2.9;         // locating pins in the 3.2 mm holes
pin_up = 2.5;         // pin tip above the board top
so_d   = 6.5;         // standoff diameter
tube_d = 6.0;         // lid pressing tubes, outside
tube_bore = 3.4;      // their bore, takes the pin tip
win    = 8.0;         // window over D1 (square)
wire_hole = 6.2;      // LED wires back into the case; big enough to pass the LED itself (rim 5.8)
wire_x = 18.2;        // its centre, board x (right of the window, towards J3)
j2_win  = [6, 9];     // window over J2 (x, y)
txt_h  = 2.2;         // label height
txt_d  = 0.6;         // engraving depth
flange_d = 13;        // LED holder flange
flange_t = 1.6;
holder_d = 7.6;       // LED holder tube, outside (window is 0.2 mm bigger each side)
rim_bore = 6.1;       // bore above the step, takes the LED rim
led_bore = 5.2;       // bore below the step, takes the LED body

in_l  = gap + board_l + gap + div_t + bay_l;
in_w  = gap + board_w + gap;
in_h  = under_h + board_t + top_h;
out_l = in_l + 2 * wall;
out_w = in_w + 2 * wall;
out_h = wall + in_h;              // base height; the lid plate sits on top of it

// board coordinates to case coordinates
function cx(x) = wall + gap + x;
function cy(y) = wall + gap + (board_w - y);
board_top = wall + under_h + board_t;   // z of the board's top surface
div_x = wall + gap + board_l + gap;     // left face of the divider

module base() {
    difference() {
        union() {
            difference() {
                cube([out_l, out_w, out_h]);
                translate([wall, wall, wall]) cube([in_l, in_w, out_h]);
            }
            // standoffs with locating pins
            for (h = holes) translate([cx(h[0]), cy(h[1]), wall - 0.01]) {
                cylinder(d = so_d, h = under_h + 0.01);
                cylinder(d = pin_d, h = under_h + board_t + pin_up, $fn = 32);
            }
            // divider between the board and the battery bay
            translate([div_x, wall - 0.01, wall - 0.01]) cube([div_t, in_w + 0.02, div_h]);
        }
        // notch in the divider for the battery clip wires, beside J1
        translate([div_x - 1, cy(j1_y) - 3, wall + under_h + 2]) cube([div_t + 2, 6, div_h]);
        // finger notch in the front wall to lift the lid
        translate([out_l / 2 - 6, -1, out_h - 1.5]) cube([12, wall + 2, 2]);
    }
}

// The lid, modelled the way it sits on the base, its underside at z = 0 (move it up by out_h).
module lid() {
    difference() {
        union() {
            cube([out_l, out_w, lid_t]);
            // lip ring that drops into the base
            translate([wall + fit, wall + fit, -lip]) difference() {
                cube([in_l - 2 * fit, in_w - 2 * fit, lip + 0.01]);
                translate([lip_w, lip_w, -1]) cube([in_l - 2 * fit - 2 * lip_w, in_w - 2 * fit - 2 * lip_w, lip + 2]);
            }
            // tubes that press the board down around the mounting holes
            for (h = holes) translate([cx(h[0]), cy(h[1]), -top_h]) cylinder(d = tube_d, h = top_h + 0.01);
            // two ribs that keep the battery from rattling (0.5 mm above it)
            for (dx = [bay_l / 3, 2 * bay_l / 3])
                translate([div_x + div_t + dx - 0.6, out_w / 2 - 15, -(in_h - bat[2] - 0.5)])
                    cube([1.2, 30, in_h - bat[2] - 0.5 + 0.01]);
        }
        // bores in the tubes for the pin tips
        for (h = holes) translate([cx(h[0]), cy(h[1]), -top_h - 1]) cylinder(d = tube_bore, h = pin_up + 1.5, $fn = 32);
        // window over D1 for the LED holder
        translate([cx(d1_x) - win / 2, cy(d1_y) - win / 2, -1]) cube([win, win, lid_t + 2]);
        // LED wires back inside
        translate([cx(wire_x), cy(d1_y), -1]) cylinder(d = wire_hole, h = lid_t + 2);
        // window over J2's pins, labels engraved to the left of each pin
        translate([cx(j2_x) - j2_win[0] / 2, cy(j2_y[1]) - j2_win[1] / 2, -1]) cube([j2_win[0], j2_win[1], lid_t + 2]);
        for (i = [0 : 2]) {
            translate([cx(j2_x) - j2_win[0] / 2 - 1.0, cy(j2_y[i]), lid_t - txt_d])
                linear_extrude(txt_d + 1) text(j2_name[i], size = txt_h, font = "Liberation Sans:style=Bold",
                                               halign = "right", valign = "center");
        }
    }
}

// The LED holder, modelled the way it sits in the lid, flange underside at z = 0 (the lid top).
// The tube ends at the LED tip; the LED's rim rests on the step between the two bores.
module led_holder() {
    tip  = board_top + d1_h + led_gap;     // case z of the LED tip
    lidz = out_h + lid_t;                  // case z of the lid top
    down = lidz - tip;                     // tube length below the flange
    step = led_len - down;                 // z of the step, relative to the flange underside (negative)
    difference() {
        union() {
            cylinder(d = flange_d, h = flange_t);
            translate([0, 0, -down]) cylinder(d = holder_d, h = down + 0.01);
        }
        translate([0, 0, -down - 1]) cylinder(d = led_bore, h = led_len + 1.01);
        translate([0, 0, step]) cylinder(d = rim_bore, h = flange_t - step + 1);
    }
}

// ---- layout for printing: everything flat on the bed, no supports ----
base();                                                              // floor down
translate([0, 2 * out_w + 8, lid_t]) rotate([180, 0, 0]) lid();     // outer face down
translate([out_l + 15, out_w / 2, flange_t]) rotate([180, 0, 0]) led_holder();   // flange down

// ---- assembled view: comment out the layout above and use these instead ----
// base();
// translate([0, 0, out_h]) lid();
// translate([cx(d1_x), cy(d1_y), out_h + lid_t]) led_holder();
