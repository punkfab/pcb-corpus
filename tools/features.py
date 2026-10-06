#!/usr/bin/env python3
"""features.py — describe every board: size, density, packages, rules, how its designer routed it, and what is on it.

  /usr/bin/python3 tools/features.py [--jobs 8]      # -> features.json

Read from board.kicad_pcb and board.kicad_pro with KiCad's pcbnew module. Wiring estimates (ratsnest
length, crossings, congestion) come from circuit-skills' placement_score.py when CIRCUIT_SKILLS points
at a checkout of github.com/punkfab/circuit-skills; without it those fields are left out.
"""
import argparse, concurrent.futures as cf, json, math, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CS = Path(os.getenv('CIRCUIT_SKILLS', Path.home() / 'sandbox/punkfab/circuit-skills')) / 'pcb-layout' / 'scripts'

TAGS = {  # tag: (where to look, pattern)
    'usb': ('nets fps', r'USB|(^|[/_])D[+-]$|D_?[PN]$|VBUS|CC[12]$'),
    'usb-c': ('fps', r'USB[_-]?C|TYPE[_-]?C'),
    'ethernet': ('nets fps vals', r'RJ45|ETH|MDI|RMII|LAN87|W5500|KSZ|MAGJACK'),
    'can-rs485': ('nets vals', r'CAN[HL]|CAN_|RS485|MAX485|SN65HVD|TJA10|MCP2551'),
    'wireless': ('fps vals nets', r'ESP32|ESP-?(12|WROOM|WROVER)|NRF5|NRF24|RFM\d|SX12|CC1101|ANTENNA|\bANT\d*\b|LORA|WIFI|U\.FL'),
    'crystal': ('fps vals', r'CRYSTAL|XTAL|OSCILLATOR|\bHC-?49'),
    'switching-regulator': ('vals fps', r'BUCK|BOOST|TPS5|TPS6|LM25|LM26|MP1584|MP23|AP62|AP63|MT3608|RT8|SY8|TLV62|LTC3|XL\d{4}'),
    'battery': ('nets vals fps', r'VBAT|BATT|TP4056|MCP738|BQ2|18650|LIPO|JST[_-]?PH'),
    'display': ('nets vals fps', r'OLED|LCD|TFT|SSD13|ST77|ILI9|HDMI|DSI|EPAPER|E-?INK'),
    'audio': ('nets vals fps', r'I2S|AUDIO|SPEAKER|\bMIC\b|MICROPHONE|PCM51|MAX98|CODEC|PJ-?3\d'),
    'motor-power': ('nets vals fps', r'MOTOR|DRV8|TB66|A4988|TMC2|L298|HBRIDGE|IRF|MOSFET.*TO-?220|RELAY'),
    'memory': ('vals fps nets', r'W25Q|FLASH|EEPROM|24LC|AT24|SDRAM|DDR|MICROSD|SD_?CARD|QSPI'),
    'sensor': ('vals', r'BME|BMP|MPU|ICM|LSM|LIS|SHT|AHT|INA2|ADS1|MAX31|VL53|HX711'),
    'fpga': ('vals fps', r'ICE40|ECP5|XC[2-7]|SPARTAN|ARTIX|CYCLONE|GW1N|FPGA'),
    'keyboard': ('fps vals', r'MX[_-]|CHERRY|KAILH|CHOC|SW_?MX|HOTSWAP|KEYSWITCH'),
    'addressable-leds': ('vals fps', r'WS281|SK68|APA10'),
}
MCUS = {'esp32': r'ESP32|ESP-?WROOM|ESP8266|ESP-?12', 'rp2040': r'RP2040|RP2350|RASPBERRY.?PI.?PICO|RPI.?PICO', 'stm32': r'STM32', 'nrf': r'NRF5\d', 'avr': r'ATMEGA|ATTINY|ATSAM|AVR',
        'pic': r'PIC1[2-8]|PIC32|DSPIC', 'ch32-wch': r'CH32|CH55\d', 'teensy-module': r'TEENSY|ARDUINO|FEATHER|XIAO|PRO_?MICRO'}

WORKER = r'''
import json, math, re, sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
mm = pcbnew.ToMM
bb = b.GetBoardEdgesBoundingBox()
f = {'width_mm': round(mm(bb.GetWidth()), 1), 'height_mm': round(mm(bb.GetHeight()), 1), 'copper_layers': b.GetCopperLayerCount()}
outline = pcbnew.SHAPE_POLY_SET()
try:
    ok = b.GetBoardPolygonOutlines(outline)
    area = sum(outline.Outline(i).Area() for i in range(outline.OutlineCount())) / 1e12 if ok else 0
    holes = sum(outline.HoleCount(i) for i in range(outline.OutlineCount())) if ok else 0
    harea = sum(outline.Hole(i, j).Area() for i in range(outline.OutlineCount()) for j in range(outline.HoleCount(i))) / 1e12 if ok else 0
except Exception:
    area, holes, harea = 0, 0, 0
bbox_area = mm(bb.GetWidth()) * mm(bb.GetHeight())
f['area_mm2'] = round((area - harea) if area else bbox_area, 1)
f['outline_fill'] = round(f['area_mm2'] / bbox_area, 3) if bbox_area else 1.0
f['cutouts'] = holes
fps = [x for x in b.GetFootprints() if any(p.GetNetCode() > 0 for p in x.Pads())]
f['parts'] = len(fps)
f['parts_bottom'] = sum(1 for x in fps if x.GetLayer() == pcbnew.B_Cu)
pads = [p for x in fps for p in x.Pads() if p.GetNetCode() > 0]
f['pads'] = len(pads)
f['pads_through_hole'] = sum(1 for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)
nets = {}
for p in pads:
    nets.setdefault(p.GetNetname(), 0)
    nets[p.GetNetname()] += 1
f['nets'] = sum(1 for n, c in nets.items() if c >= 2)
f['max_net_pads'] = max(nets.values(), default=0)
body = 0.0
pitch, big, bga, maxpins = [], 0, 0, 0
for x in fps:
    box = x.GetBoundingBox(False)
    body += mm(box.GetWidth()) * mm(box.GetHeight())
    pp = [p for p in x.Pads()]
    maxpins = max(maxpins, len(pp))
    if len(pp) >= 8:
        pts = sorted({(p.GetPosition().x, p.GetPosition().y) for p in pp})
        d = min((math.dist(a, c) for i, a in enumerate(pts) for c in pts[i + 1:i + 40]), default=0)
        if mm(d) >= 0.2:  # closer than that is a stacked or split pad, not a pin pitch
            pitch.append(mm(d))
        names = [p.GetNumber() for p in pp]
        grid = [n for n in names if re.fullmatch(r'[A-Z]{1,2}\d{1,2}', n)]
        rows = {re.match(r'[A-Z]+', n).group(0) for n in grid}
        if 'BGA' in x.GetFPIDAsString().upper() or (len(pp) >= 16 and len(grid) > 0.8 * len(pp) and len(rows) >= 4):  # a USB-C socket has rows A and B only
            bga += 1
    if len(pp) >= 16:
        big += 1
f['body_cover'] = round(body / f['area_mm2'], 3) if f['area_mm2'] else None
f['max_pins'] = maxpins
f['parts_16plus_pins'] = big
f['bga'] = bga
f['min_pitch_mm'] = round(min(pitch), 3) if pitch else None
f['fine_pitch_parts'] = sum(1 for d in pitch if d <= 0.55)
tr = list(b.GetTracks())
seg = [t for t in tr if t.GetClass() != 'PCB_VIA']
vias = [t for t in tr if t.GetClass() == 'PCB_VIA']
f['vias'] = len(vias)
f['track_mm'] = round(sum(mm(t.GetLength()) for t in seg), 1)
ws = sorted({round(mm(t.GetWidth()), 3) for t in seg})
f['min_track_mm'], f['track_widths'] = (ws[0] if ws else None), len(ws)
f['min_via_mm'] = round(min((mm(v.GetWidth(pcbnew.F_Cu)) for v in vias), default=0), 3) or None
f['min_via_drill_mm'] = round(min((mm(v.GetDrillValue()) for v in vias), default=0), 3) or None
f['blind_or_micro_vias'] = sum(1 for v in vias if v.GetViaType() != pcbnew.VIATYPE_THROUGH)
used = {}
for t in seg:
    used[b.GetLayerName(t.GetLayer())] = used.get(b.GetLayerName(t.GetLayer()), 0) + mm(t.GetLength())
f['layer_track_mm'] = {k: round(v, 1) for k, v in sorted(used.items())}
zones = [z for z in b.Zones() if not z.GetIsRuleArea()]
f['pours'] = len(zones)
f['pour_nets'] = sorted({z.GetNetname() for z in zones if z.GetNetname()})
f['inner_planes'] = sorted({z.GetNetname() for z in zones if z.GetNetname() and any(pcbnew.IsInnerCopperLayer(l) for l in z.GetLayerSet().Seq())})
f['keepouts'] = sum(1 for z in b.Zones() if z.GetIsRuleArea())
names = set(nets)
pairs = set()
for n in names:
    m = re.match(r'(.*?)([_.\-]?)(P|\+)$', n)
    if m and any((m.group(1) + m.group(2) + s) in names for s in ('N', '-')):
        pairs.add(m.group(1))
f['diff_pairs'] = len(pairs)
f['_text'] = {'nets': sorted(names), 'fps': sorted({x.GetFPIDAsString() for x in fps}), 'vals': sorted({x.GetValue() for x in fps}),
              'refs': sorted(x.GetReference() for x in fps)}
print(json.dumps(f))
'''


def one(bid):
    d = ROOT / 'boards' / bid
    r = subprocess.run(['/usr/bin/python3', '-c', WORKER, str(d / 'board.kicad_pcb')], capture_output=True, text=True, timeout=900)
    if r.returncode or not r.stdout.strip():
        return bid, {'error': (r.stderr.strip().splitlines() or ['?'])[-1][:200]}
    f = json.loads(r.stdout.strip().splitlines()[-1])
    text = f.pop('_text')
    hay = {k: ' '.join(v).upper() for k, v in text.items()}
    f['tags'] = sorted(t for t, (where, pat) in TAGS.items() if any(re.search(pat, hay[w]) for w in where.split()))
    f['mcu'] = sorted(m for m, pat in MCUS.items() if re.search(pat, hay['fps'] + ' ' + hay['vals']))
    refs = text['refs']
    cnt = lambda prefix: sum(1 for x in refs if re.fullmatch('(?:' + prefix + r')\d+', x))
    f['connectors'], f['inductors'], f['switches'], f['leds'] = cnt('J|P|CN|CON'), cnt('L'), cnt('SW|S|K|MX'), cnt('LED|D')
    if f['switches'] >= 12 and 'keyboard' not in f['tags']:
        f['tags'].append('keyboard')
    try:  # project rules
        pro = json.loads((d / 'board.kicad_pro').read_text())
        rules = pro['board']['design_settings']['rules']
        classes = pro.get('net_settings', {}).get('classes', [])
        f['rule_min_clearance_mm'], f['rule_min_track_mm'] = rules.get('min_clearance'), rules.get('min_track_width')
        f['net_classes'] = len(classes)
        f['default_clearance_mm'] = next((c.get('clearance') for c in classes if c.get('name') == 'Default'), None)
        f['default_track_mm'] = next((c.get('track_width') for c in classes if c.get('name') == 'Default'), None)
    except (OSError, KeyError, ValueError):
        pass
    f['custom_rules'] = (d / 'board.kicad_dru').exists()
    try:  # wiring estimates on the designer's placement
        sys.path.insert(0, str(CS))
        import placement_score
        s = placement_score.score(str(d / 'unrouted.kicad_pcb'))
        f['signal_nets'] = s['signal_nets']
        f['ratsnest_mm'] = s['ratsnest']['mst_mm']
        f['crossings'] = s['ratsnest']['crossings']
        f['congestion_max'], f['congestion_p95'] = s['congestion']['max'], s['congestion']['p95']
        f['over_capacity_pct'] = s['congestion']['over_capacity_pct']
        f['escape_ratio'] = max([e['ratio'] or 0 for e in s['escape']], default=0)
        f['decap_mm'] = s['intent']['decap_mm']
    except (Exception, SystemExit):
        pass
    # derived, per unit of board
    a = f['area_mm2'] or 1
    f['pads_per_cm2'] = round(100 * f['pads'] / a, 2)
    f['through_hole_share'] = round(f['pads_through_hole'] / f['pads'], 2) if f['pads'] else 0
    f['double_sided'] = f['parts_bottom'] >= max(2, 0.1 * f['parts'])
    if f.get('ratsnest_mm'):
        f['detour'] = round(f['track_mm'] / f['ratsnest_mm'], 2)                       # designer's copper over the shortest trees
        f['wiring_density'] = round(f['ratsnest_mm'] / (a * min(2, f['copper_layers'])) * 10, 3)  # mm of wire per cm2 of signal layer
        f['crossings_per_net'] = round(f['crossings'] / max(1, f['signal_nets']), 2)
    f['vias_per_net'] = round(f['vias'] / max(1, f['nets']), 2)
    return bid, f


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--jobs', type=int, default=8)
    p.add_argument('--limit', type=int)
    a = p.parse_args()
    ids = [b['id'] for b in json.loads((ROOT / 'manifest.json').read_text())][:a.limit]
    with cf.ProcessPoolExecutor(a.jobs) as pool:
        res = dict(pool.map(one, ids))
    if not a.limit:
        (ROOT / 'features.json').write_text(json.dumps(res, indent=1, sort_keys=True) + '\n')
    bad = {k: v['error'] for k, v in res.items() if 'error' in v}
    print(f'{len(res)} boards, {len(bad)} errors', list(bad.items())[:3])
    if a.limit:
        print(json.dumps(list(res.values())[0], indent=1)[:2500])


if __name__ == '__main__':
    main()
