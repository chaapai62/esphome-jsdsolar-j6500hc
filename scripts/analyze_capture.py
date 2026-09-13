#!/usr/bin/env python3
"""Summarize passive_capture JSONL files and highlight suspicious values."""
from __future__ import annotations

import argparse, json, math
from collections import Counter, defaultdict
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('jsonl')
    args = ap.parse_args()
    p = Path(args.jsonl)
    rows = [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
    bc = Counter(str(r.get('byte_count')) for r in rows)
    seq = Counter(str(r.get('seq')) for r in rows if 'seq' in r)
    blocks = defaultdict(list)
    for r in rows:
        kd = r.get('known_decode') or {}
        b = kd.get('block')
        if b: blocks[b].append(kd)
    print('frames', len(rows))
    print('crc_ok', sum(1 for r in rows if r.get('crc_ok')), 'crc_bad', sum(1 for r in rows if not r.get('crc_ok')))
    print('byte_counts', dict(bc))
    print('seq_counts', dict(seq))
    for name, vals in blocks.items():
        print('\n[' + name + '] samples=' + str(len(vals)))
        keys = sorted({k for v in vals for k in v if k not in ('block','raw','hex')})
        for k in keys:
            nums = [v[k] for v in vals if isinstance(v.get(k), (int, float)) and not (isinstance(v.get(k), float) and math.isnan(v[k]))]
            if nums:
                print(f'  {k}: min={min(nums)} max={max(nums)} last={nums[-1]}')
        if vals and 'hex' in vals[-1]:
            print('  last_hex:', vals[-1]['hex'])
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
