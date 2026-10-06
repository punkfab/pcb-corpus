#!/usr/bin/env python3
"""baseline.py — route every board's unrouted copy with one router and record the outcome.

  python3 tools/baseline.py --name tracemaker-30s --cmd 'tracemaker route {in} -o {out} --time 30 --threads 4 --no-kb' [--jobs 6]

{in} is a copy of unrouted.kicad_pcb with the board's project rules beside it; the command must write
{out}. The result is refilled, then judged by `kicad-cli pcb drc --severity-error`. A board is clean
when nothing is left open and there are no error-level violations. Writes baselines/<name>.json and
resumes. Needs kicad-cli and KiCad's pcbnew Python module (/usr/bin/python3 on Debian/Ubuntu).
"""
import argparse, concurrent.futures as cf, json, shlex, shutil, subprocess, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILL = "import sys; sys.path.insert(0, '/usr/lib/python3/dist-packages'); import pcbnew; b = pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1], b)"


def drc(board):
    out = board.with_suffix('.drc.json')
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-error', '--units', 'mm', '-o', str(out), str(board)], capture_output=True, timeout=900)
    d = json.loads(out.read_text())
    return len(d.get('violations', [])), len(d.get('unconnected_items', []))


def one(bid, cmd, timeout):
    src = ROOT / 'boards' / bid
    with tempfile.TemporaryDirectory(prefix='pcb-corpus-') as tmp:
        tmp = Path(tmp)
        for name in ('in', 'out'):
            for ext in ('.kicad_pro', '.kicad_dru'):
                if (src / f'board{ext}').exists():
                    shutil.copy(src / f'board{ext}', tmp / f'{name}{ext}')
        shutil.copy(src / 'unrouted.kicad_pcb', tmp / 'in.kicad_pcb')
        row = {'id': bid}
        try:
            _, row['connections'] = drc(tmp / 'in.kicad_pcb')
            t0 = time.time()
            subprocess.run([a.replace('{in}', str(tmp / 'in.kicad_pcb')).replace('{out}', str(tmp / 'out.kicad_pcb')) for a in shlex.split(cmd)],
                           capture_output=True, timeout=timeout, cwd=tmp)
            row['seconds'] = round(time.time() - t0, 1)
            if not (tmp / 'out.kicad_pcb').exists():
                return {**row, 'failed': 'no output'}
            subprocess.run(['/usr/bin/python3', '-c', FILL, str(tmp / 'out.kicad_pcb')], capture_output=True, timeout=900)
            row['drv'], row['open'] = drc(tmp / 'out.kicad_pcb')
            row['routed'] = round(max(0.0, 1 - row['open'] / row['connections']), 4) if row['connections'] else 1.0
            row['clean'] = row['drv'] == 0 and row['open'] == 0
        except Exception as e:
            row['failed'] = f'{type(e).__name__}'
        return row


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--name', required=True)
    p.add_argument('--cmd', required=True)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--timeout', type=int, default=600)
    a = p.parse_args()
    out = ROOT / 'baselines' / f'{a.name}.json'
    res = json.loads(out.read_text()) if out.exists() else {'name': a.name, 'cmd': a.cmd, 'boards': {}}
    todo = [b['id'] for b in json.loads((ROOT / 'manifest.json').read_text()) if b['id'] not in res['boards']]
    with cf.ThreadPoolExecutor(a.jobs) as pool:
        for i, f in enumerate(cf.as_completed([pool.submit(one, b, a.cmd, a.timeout) for b in todo]), 1):
            r = f.result()
            res['boards'][r.pop('id')] = r
            out.write_text(json.dumps(res, indent=1, sort_keys=True) + '\n')
            print(f"[{i}/{len(todo)}] {r}", flush=True)
    rows = list(res['boards'].values())
    ok = [r for r in rows if not r.get('failed')]
    print(f"{a.name}: {len(rows)} boards, clean {sum(r['clean'] for r in ok)}, mean routed {sum(r['routed'] for r in ok) / max(1, len(ok)):.3f}, failed {len(rows) - len(ok)}")


if __name__ == '__main__':
    main()
