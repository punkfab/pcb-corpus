#!/usr/bin/env python3
"""groups.py — sort the boards into groups by size, technology, features and measured difficulty.

  python3 tools/groups.py        # features.json + baselines/*.json -> groups.json, GROUPS.md

A board can be in many groups. Difficulty is measured, not guessed: it comes from what the baseline
routers in baselines/ actually did with the designer's placement.
"""
import json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = json.loads((ROOT / 'features.json').read_text())
M = {b['id']: b for b in json.loads((ROOT / 'manifest.json').read_text())}
BASE = {p.stem: json.loads(p.read_text())['boards'] for p in sorted((ROOT / 'baselines').glob('*.json'))}

# name: (what it means, test on a board's features f and manifest row m)
GROUPS = {
    'size': {
        'small': ('under 40 connections', lambda f, m: m['connections'] < 40),
        'medium': ('40 to 149 connections', lambda f, m: 40 <= m['connections'] < 150),
        'large': ('150 to 399 connections', lambda f, m: 150 <= m['connections'] < 400),
        'xlarge': ('400 connections and up', lambda f, m: m['connections'] >= 400),
    },
    'stackup': {
        'two-layer': ('2 copper layers', lambda f, m: f['copper_layers'] <= 2),
        'four-layer': ('4 copper layers', lambda f, m: f['copper_layers'] == 4),
        'inner-planes': ('a pour on an inner layer', lambda f, m: bool(f['inner_planes'])),
        'no-pour': ('no copper pour at all', lambda f, m: f['pours'] == 0),
    },
    'technology': {
        'through-hole': ('60% or more of the pads are through-hole', lambda f, m: f['through_hole_share'] >= 0.6),
        'surface-mount': ('under 15% of the pads are through-hole', lambda f, m: f['through_hole_share'] < 0.15),
        'double-sided': ('at least 10% of the parts are on the bottom', lambda f, m: f['double_sided']),
        'fine-pitch': ('a part with 16+ pins at 0.5 mm pitch or finer', lambda f, m: f['parts_16plus_pins'] > 0 and (f['min_pitch_mm'] or 9) <= 0.5),
        'bga': ('a ball-grid part', lambda f, m: f['bga'] > 0),
        'dense': ('11 or more pads per cm2 (the top quarter)', lambda f, m: f['pads_per_cm2'] >= 11),
        'sparse': ('under 2.7 pads per cm2 (the bottom quarter)', lambda f, m: f['pads_per_cm2'] < 2.7),
    },
    'constraints': {
        'diff-pairs': ('named differential pairs', lambda f, m: f['diff_pairs'] > 0),
        'shaped-outline': ('the outline fills under 95% of its bounding box', lambda f, m: f['outline_fill'] < 0.95),
        'cutouts': ('holes cut inside the outline', lambda f, m: f['cutouts'] > 0),
        'keepouts': ('rule areas', lambda f, m: f['keepouts'] > 0),
        'net-classes': ('more than one net class', lambda f, m: (f.get('net_classes') or 1) > 1),
        'custom-rules': ('a .kicad_dru file', lambda f, m: f['custom_rules']),
        'tight-rules': ('default clearance of 0.15 mm or less', lambda f, m: 0 < (f.get('default_clearance_mm') or 9) <= 0.15),
    },
    'wiring': {
        'tangled': ('4.2 or more ratsnest crossings per net (the top quarter)', lambda f, m: f.get('crossings_per_net', 0) >= 4.2),
        'untangled': ('under 1.5 crossings per net (the bottom quarter)', lambda f, m: f.get('crossings_per_net', 9) < 1.5),
        'via-heavy': ("the designer used 2.5 or more vias per net (the top quarter)", lambda f, m: f['vias_per_net'] >= 2.5),
        'single-sided-routing': ('90% or more of the copper on one layer', lambda f, m: f['track_mm'] > 0 and max(f['layer_track_mm'].values(), default=0) / f['track_mm'] >= 0.9),
    },
    'reference': {
        'clean-reference': ("zero DRC errors as designed: a clean pass is a fair bar", lambda f, m: m['ref_drv'] == 0),
    },
}
for t in ('usb', 'usb-c', 'ethernet', 'can-rs485', 'wireless', 'crystal', 'switching-regulator', 'battery', 'display', 'audio', 'motor-power', 'memory',
          'sensor', 'fpga', 'keyboard', 'addressable-leds'):
    GROUPS.setdefault('on the board', {})[t] = ('detected from net, footprint and value names', lambda f, m, t=t: t in f['tags'])
for t in ('esp32', 'rp2040', 'stm32', 'avr', 'nrf', 'teensy-module'):
    GROUPS.setdefault('controller', {})[t] = ('detected from footprint and value names', lambda f, m, t=t: t in f['mcu'])


def difficulty(bid):
    """solved: some baseline routed it clean. connects: some baseline connected at least 98%. open: none did."""
    rs = [b[bid] for b in BASE.values() if bid in b and not b[bid].get('failed')]
    if not rs:
        return None
    if any(r['clean'] for r in rs):
        return 'solved'
    return 'connects' if max(r['routed'] for r in rs) >= 0.98 else 'open'


def main():
    ids = sorted(F)
    groups = {}
    for kind, gs in GROUPS.items():
        for name, (_, test) in gs.items():
            groups[name] = [i for i in ids if test(F[i], M[i])]
    diff = {i: difficulty(i) for i in ids}
    if BASE:
        for d in ('solved', 'connects', 'open'):
            groups[f'difficulty-{d}'] = [i for i in ids if diff[i] == d]
    (ROOT / 'groups.json').write_text(json.dumps(groups, indent=1) + '\n')
    best = {}
    for i in ids:
        rs = [b[i] for b in BASE.values() if i in b and not b[i].get('failed')]
        if rs:
            best[i] = {'clean': any(r['clean'] for r in rs), 'routed': max(r['routed'] for r in rs)}

    def row(name, what, members):
        got = [best[i] for i in members if i in best]
        med = lambda k, src: statistics.median(src[i][k] for i in members) if members else 0
        return (f"| `{name}` | {what} | {len(members)} | {med('connections', M):.0f} | {med('pads_per_cm2', F):.1f} | "
                + (f"{sum(g['clean'] for g in got) / len(got):.2f} | {statistics.mean(g['routed'] for g in got):.2f} |" if got else '– | – |'))

    out = ['# Groups', '', f'{len(ids)} boards. A board can be in many groups; `groups.json` has the members of each.', '']
    if BASE:
        out += ['The last two columns are the best of the baseline routers in `baselines/` (' + ', '.join(f'`{b}`' for b in BASE) + ") on the designer's placement: "
                'the share of the group routed clean (fully connected, zero error-level DRC), and the mean share of connections routed.', '']
        out += ['## Measured difficulty', '', '| group | meaning | boards | median connections | median pads/cm2 | clean | routed |', '|---|---|---|---|---|---|---|']
        out += [row('difficulty-solved', 'a baseline routed it clean', groups['difficulty-solved']),
                row('difficulty-connects', 'not clean, but a baseline connected 98% or more', groups['difficulty-connects']),
                row('difficulty-open', 'no baseline connected 98%', groups['difficulty-open']), '']
    for kind, gs in GROUPS.items():
        out += [f'## {kind.capitalize()}', '', '| group | meaning | boards | median connections | median pads/cm2 | clean | routed |', '|---|---|---|---|---|---|---|']
        out += [row(name, what, groups[name]) for name, (what, _) in gs.items()] + ['']
    (ROOT / 'GROUPS.md').write_text('\n'.join(out))
    print('\n'.join(out[:60]))


if __name__ == '__main__':
    main()
