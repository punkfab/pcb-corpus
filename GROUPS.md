# Groups

235 boards. A board can be in many groups; `groups.json` has the members of each.

The last two columns are the best of the baseline routers in `baselines/` (`tracemaker-30s`) on the designer's placement: the share of the group routed clean (fully connected, zero error-level DRC), and the mean share of connections routed.

## Measured difficulty

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `difficulty-solved` | a baseline routed it clean | 48 | 58 | 4.0 | 1.00 | 1.00 |
| `difficulty-connects` | not clean, but a baseline connected 98% or more | 101 | 88 | 5.6 | 0.00 | 1.00 |
| `difficulty-open` | no baseline connected 98% | 86 | 207 | 6.1 | 0.00 | 0.85 |

## Size

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `small` | under 40 connections | 37 | 28 | 5.5 | 0.43 | 0.98 |
| `medium` | 40 to 149 connections | 112 | 89 | 5.4 | 0.24 | 0.97 |
| `large` | 150 to 399 connections | 66 | 232 | 5.1 | 0.08 | 0.94 |
| `xlarge` | 400 connections and up | 20 | 499 | 6.0 | 0.00 | 0.72 |

## Stackup

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `two-layer` | 2 copper layers | 178 | 95 | 4.4 | 0.24 | 0.96 |
| `four-layer` | 4 copper layers | 57 | 184 | 10.2 | 0.11 | 0.91 |
| `inner-planes` | a pour on an inner layer | 57 | 184 | 10.2 | 0.11 | 0.91 |
| `no-pour` | no copper pour at all | 13 | 53 | 2.5 | 0.38 | 0.95 |

## Technology

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `through-hole` | 60% or more of the pads are through-hole | 43 | 85 | 2.6 | 0.35 | 0.95 |
| `surface-mount` | under 15% of the pads are through-hole | 72 | 134 | 10.8 | 0.15 | 0.94 |
| `double-sided` | at least 10% of the parts are on the bottom | 99 | 136 | 7.3 | 0.09 | 0.95 |
| `fine-pitch` | a part with 16+ pins at 0.5 mm pitch or finer | 113 | 156 | 9.5 | 0.10 | 0.92 |
| `bga` | a ball-grid part | 7 | 169 | 12.8 | 0.00 | 0.91 |
| `dense` | 11 or more pads per cm2 (the top quarter) | 60 | 102 | 18.3 | 0.18 | 0.95 |
| `sparse` | under 2.7 pads per cm2 (the bottom quarter) | 59 | 94 | 1.8 | 0.29 | 0.95 |

## Constraints

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `diff-pairs` | named differential pairs | 80 | 140 | 10.0 | 0.14 | 0.94 |
| `shaped-outline` | the outline fills under 95% of its bounding box | 85 | 120 | 5.8 | 0.19 | 0.94 |
| `cutouts` | holes cut inside the outline | 55 | 135 | 4.5 | 0.18 | 0.96 |
| `keepouts` | rule areas | 63 | 160 | 9.5 | 0.11 | 0.93 |
| `net-classes` | more than one net class | 114 | 136 | 6.8 | 0.18 | 0.92 |
| `custom-rules` | a .kicad_dru file | 22 | 161 | 7.3 | 0.14 | 0.94 |
| `tight-rules` | default clearance of 0.15 mm or less | 56 | 138 | 10.5 | 0.12 | 0.93 |

## Wiring

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `tangled` | 4.2 or more ratsnest crossings per net (the top quarter) | 59 | 238 | 4.7 | 0.03 | 0.86 |
| `untangled` | under 1.5 crossings per net (the bottom quarter) | 55 | 54 | 5.5 | 0.45 | 0.99 |
| `via-heavy` | the designer used 2.5 or more vias per net (the top quarter) | 63 | 137 | 7.6 | 0.13 | 0.93 |
| `single-sided-routing` | 90% or more of the copper on one layer | 23 | 44 | 3.6 | 0.43 | 0.94 |

## Reference

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `clean-reference` | zero DRC errors as designed: a clean pass is a fair bar | 77 | 86 | 6.7 | 0.49 | 0.96 |

## On the board

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `usb` | detected from net, footprint and value names | 107 | 134 | 7.3 | 0.11 | 0.95 |
| `usb-c` | detected from net, footprint and value names | 63 | 155 | 9.5 | 0.11 | 0.95 |
| `ethernet` | detected from net, footprint and value names | 6 | 146 | 5.5 | 0.17 | 0.91 |
| `can-rs485` | detected from net, footprint and value names | 11 | 229 | 11.9 | 0.09 | 0.95 |
| `wireless` | detected from net, footprint and value names | 46 | 134 | 9.6 | 0.11 | 0.95 |
| `crystal` | detected from net, footprint and value names | 83 | 187 | 8.2 | 0.06 | 0.89 |
| `switching-regulator` | detected from net, footprint and value names | 25 | 175 | 10.5 | 0.16 | 0.95 |
| `battery` | detected from net, footprint and value names | 56 | 134 | 6.6 | 0.16 | 0.96 |
| `display` | detected from net, footprint and value names | 19 | 175 | 6.0 | 0.16 | 0.94 |
| `audio` | detected from net, footprint and value names | 50 | 124 | 4.1 | 0.16 | 0.92 |
| `motor-power` | detected from net, footprint and value names | 16 | 158 | 7.6 | 0.19 | 0.95 |
| `memory` | detected from net, footprint and value names | 43 | 187 | 7.6 | 0.07 | 0.91 |
| `sensor` | detected from net, footprint and value names | 13 | 187 | 9.5 | 0.08 | 0.94 |
| `fpga` | detected from net, footprint and value names | 15 | 183 | 12.8 | 0.00 | 0.91 |
| `keyboard` | detected from net, footprint and value names | 44 | 160 | 2.2 | 0.09 | 0.97 |
| `addressable-leds` | detected from net, footprint and value names | 20 | 150 | 3.9 | 0.15 | 0.96 |

## Controller

| group | meaning | boards | median connections | median pads/cm2 | clean | routed |
|---|---|---|---|---|---|---|
| `esp32` | detected from footprint and value names | 33 | 99 | 10.4 | 0.15 | 0.95 |
| `rp2040` | detected from footprint and value names | 29 | 126 | 4.8 | 0.14 | 0.96 |
| `stm32` | detected from footprint and value names | 19 | 168 | 9.5 | 0.11 | 0.98 |
| `avr` | detected from footprint and value names | 13 | 82 | 2.8 | 0.31 | 0.96 |
| `nrf` | detected from footprint and value names | 7 | 139 | 2.2 | 0.00 | 0.94 |
| `teensy-module` | detected from footprint and value names | 21 | 137 | 2.5 | 0.19 | 0.99 |
