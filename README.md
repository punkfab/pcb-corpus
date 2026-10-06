# pcb-corpus

235 real KiCad boards from 170 open-source hardware repositories, prepared as a benchmark for
PCB placement and routing tools. Each board comes as its designer shipped it and as an unrouted copy, with
its own project rules.

It exists because the public routing benchmarks are built on KiCad 5 files with no project file, so every
board is judged against KiCad's default rules. These are current designs judged against their own.

## What is in a board folder

| file | what it is |
|---|---|
| `board.kicad_pcb` | the designer's board, unmodified |
| `board.kicad_pro` | its project file: net classes, clearances, DRC severities |
| `board.kicad_dru` | its custom rules, when the project has them |
| `unrouted.kicad_pcb` | the same board with tracks, vias and zone fills removed; placement kept |
| `LICENSE` (or as named upstream) | the source repository's licence file at the pinned commit |
| `SOURCE.json` | repository, commit, path, licence, and what was changed |

`manifest.json` lists every board with its statistics. `splits.json` groups them by size:
easy (under 40 connections, 37 boards), medium (40 to 149, 112) and hard (150 and up, 86).

## What qualified

A board is here if:

- its repository carries an open-hardware or permissive licence that GitHub recognises,
- a `.kicad_pro` sits beside the `.kicad_pcb`,
- it opens in KiCad 9, has 1 to 4 copper layers and at least 5 parts on nets,
- and its designer's routing leaves no connection open.

158 of the 235 boards have error-level DRC violations under their own rules as designed. `ref_drv` in
the manifest is that count. For a "clean pass" comparison (fully connected, zero DRC errors), use the
77 boards where it is 0.

Mix: 178 two-layer, 57 four-layer.
Licences: MIT 75, GPL-3.0 67, CERN-OHL-S-2.0 25, CERN-OHL-P-2.0 25, Apache-2.0 19, CC-BY-SA-4.0 10, CERN-OHL-W-2.0 5, CC-BY-4.0 4, BSD-3-Clause 3, CC0-1.0 2.

## Using it

- **Routing:** route `unrouted.kicad_pcb`, refill the zones, and run
  `kicad-cli pcb drc --severity-error` on the result with `board.kicad_pro` copied beside it.
- **Placement:** move the parts of `unrouted.kicad_pcb`, then route and judge the same way. The designer's
  placement is the reference.
- A router that reads the board file directly will treat a stale zone fill as copper in its way. The
  unrouted boards have their fills cleared for that reason; refill after routing, before DRC.

The collector that built this, and harnesses that run it, are in
[punkfab/circuit-skills](https://github.com/punkfab/circuit-skills) under `evals/corpus`.

## Licences

This repository is a collection. **Each board keeps the licence of its source repository**, copied into
its folder; see [ATTRIBUTION.md](ATTRIBUTION.md) for the full list. Several are share-alike (GPL-3.0,
CERN-OHL-S, CC-BY-SA): if you redistribute or modify those boards, their terms apply to you.
`unrouted.kicad_pcb` is a modified copy (routing removed) under the same licence as its board.

The licence recorded for a board is the one GitHub detects for its repository. If you are an author
and a board here is under different terms than recorded, or you want it removed, open an issue and it
will be taken down.

The manifest, splits, README and attribution files are released under CC0-1.0.
