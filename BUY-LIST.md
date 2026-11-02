# Project 1 buy list, with prices

**Superseded 2026-10-09 by `BUY-LIST.txt`**, which adds the breadboard parts, groups the items by where to buy them and has today's prices. This file is kept for the alternates table and the board maker prices.

Updated 2026-10-06 for building straight onto the circuit board (no breadboard build).
`BUY-LIST.txt` is the plain shopping list; this file adds prices, stock and alternates.
Prices read on digikey.fr on 2026-10-04 and 2026-10-06, each, excluding VAT.
`buy-list-cart.csv` holds the same lines for a distributor's bulk-add tool (not tested on any site).

## A. Main parts

| # | Item | Part number | Qty | Board uses | Each | Line |
|---|------|-------------|-----|------------|------|------|
| 1 | Photodiode | Vishay BPW34 | 2 | 1 | 1.17 | 2.34 |
| 2 | Op amp, SOIC-8 | MCP6022-I/SN | 4 | 3 | 1.52 | 6.08 |
| 3 | Analog switch, SOIC-16 | Nexperia 74HC4053D,653 | 2 | 1 | 0.34 | 0.68 |
| 4 | Divider, SOIC-16 | Nexperia 74HC4060D,653 | 2 | 1 | 0.34 | 0.68 |
| 5 | Crystal 32.768 kHz, 12.5 pF | Abracon AB26T-32.768KHZ | 2 | 1 | 0.25 | 0.50 |
| 6 | MOSFET, TO-92 | Diotec 2N7000 | 3 | 1 | 0.25 | 0.75 |
| 7 | Red LED 5 mm | Kingbright WP7113SURDK | 5 | 1 | 0.24 | 1.20 |
| 8 | 5 V regulator, TO-92 | LP2950ACZ-5.0/NOPB | 2 | 1 | 1.12 | 2.24 |
| 9 | Diode, DO-35 | onsemi 1N4148TR | 3 | 1 | 0.09 | 0.27 |
| 10 | 9 V battery clip | MPD BS6I-MC | 1 | 1 | 1.56 | 1.56 |
| 11 | 10 uF 50 V electrolytic, radial | Panasonic ECA-1HM100 | 3 | 2 | 0.21 | 0.63 |
| 12 | 1 uF 63 V film, 5 mm pitch | KEMET R82DC4100AA60J | 3 | 2 | 0.57 | 1.71 |
| | Subtotal A | | | | | 18.64 |

Not bought: the 40-way pin header strip (Wurth 61304011121, 1.25); the user already has one.
Line 12: the page showed both 0.11 and 0.57; the higher is used.

## B. Surface-mount parts (0805, ten of each)

| # | Value | Part number | Board uses | Each at 10 | Line |
|---|-------|-------------|------------|-----------|------|
| 13 | 100 ohm 1 % | Yageo RC0805FR-07100RL | 3 | 0.029 | 0.29 |
| 14 | 680 ohm 1 % | Yageo RC0805FR-07680RL | 1 | 0.029 | 0.29 |
| 15 | 1 k 1 % | Yageo RC0805FR-071KL | 1 | 0.029 | 0.29 |
| 16 | 10 k 1 % | Yageo RC0805FR-0710KL | 5 | 0.029 | 0.29 |
| 17 | 100 k 1 % | Yageo RC0805FR-07100KL | 5 | 0.031 | 0.31 |
| 18 | 330 k 1 % | Yageo RC0805FR-07330KL | 1 | 0.029 | 0.29 |
| 19 | 10 M 1 % | Yageo RC0805FR-0710ML | 1 | 0.031 | 0.31 |
| 20 | 22 pF C0G | Yageo CC0805JRNPO9BN220 | 2 | 0.075 | 0.75 |
| 21 | 100 pF C0G | KEMET C0805C101J5GACTU | 1 | 0.091 | 0.91 |
| 22 | 10 nF C0G | Murata GRM2195C1H103JA01D | 1 | 0.10 | 1.00 |
| 23 | 100 nF X7R | Yageo CC0805KRX7R9BB104 | 5 | 0.084 | 0.84 |
| 24 | 1 uF X7R 25 V | Yageo CC0805KKX7R8BB105 | 1 | 0.138 | 1.38 |
| | Subtotal B | | | | 6.95 |

## Total for the electronic parts

| | Excl. VAT | With 20 % VAT |
|---|-----------|---------------|
| A + B | 25.59 | about 31 |

Delivery is extra and depends on the shop: DigiKey charged 25 euros below 75 euros on 2026-10-04.

## C. Circuit board

`kicad/lockin-gerbers.zip`, 2 layers, 90 x 60 mm. Prices found by web search on 2026-10-06, not from a quote for this board:

| Maker | Price found | Note |
|-------|-------------|------|
| Aisler (Germany) | 12.00 job fee + 0.067 per cm2 per board, 3 boards: about 23 euros | Shipping within Europe reported as included |
| JLCPCB (China) | About 2 US dollars for 5 boards up to 100 x 100 mm | Shipping to France and import VAT are extra and were not found |

## D. Battery, supplies and tools

A 9 V battery, solder, flux, tweezers, solder wick and side cutters: see `BUY-LIST.txt`. Not priced here; cheaper in an ordinary shop than at a distributor.

## Alternates if a line is out of stock

| Line | Alternate |
|------|-----------|
| 2 | MCP6292-E/SN |
| 3, 4 | Any 74HC4053 / 74HC4060 in SOIC-16 (3.9 mm wide) |
| 6 | BS170 (pin order differs: check before fitting) |
| 8 | L78L05 (check its pin order and output capacitor needs in its datasheet first; not checked here) |
| 9 | Any 1N4148 or 1N914 in the DO-35 glass package |
| 12 | Any 1 uF polyester film, 63 V, 5 mm pitch, body up to 7.2 x 5 mm |
| 21 | Yageo CC0805JRNPO9BN101 (out of stock on 2026-10-04) |
