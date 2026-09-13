#!/usr/bin/env python3
"""Passive TCP capture for a RS232/IP gateway carrying raw Modbus RTU bytes.
Default target: 192.168.x.x:6666. This script only reads TCP bytes; it sends no
Modbus request frames. Use it first to debug spontaneous inverter traffic.
"""
from __future__ import annotations

import argparse, json, socket, time
from pathlib import Path
from jsd_rtu import decode_response, extract_responses, known_decode

EXPECTED_BC = [20, 4, 4, 2, 8, 8, 12, 4, 4, 8, 6, 2, 6, 4, 32, 16, 16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='192.168.x.x')
    ap.add_argument('--port', type=int, default=6666)
    ap.add_argument('--seconds', type=float, default=120)
    ap.add_argument('--out', default='../captures/passive.jsonl')
    ap.add_argument('--timeout', type=float, default=5)
    args = ap.parse_args()

    out = Path(args.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    summary_path = out.with_suffix('.summary.json')
    buf = bytearray(); seq = -1
    counts = {'frames': 0, 'crc_ok': 0, 'crc_bad': 0, 'sequence_errors': 0, 'cycles': 0, 'byte_counts': {}, 'start': time.time(), 'end': None}

    with socket.create_connection((args.host, args.port), timeout=args.timeout) as s, out.open('w', encoding='utf-8') as f:
        s.settimeout(0.5)
        deadline = time.time() + args.seconds
        while time.time() < deadline:
            try:
                chunk = s.recv(4096)
            except socket.timeout:
                continue
            if not chunk:
                break
            buf.extend(chunk)
            for raw in extract_responses(buf):
                fr = decode_response(raw)
                d = fr.asdict()
                counts['frames'] += 1
                counts['crc_ok' if fr.crc_ok else 'crc_bad'] += 1
                if fr.byte_count is not None:
                    counts['byte_counts'][str(fr.byte_count)] = counts['byte_counts'].get(str(fr.byte_count), 0) + 1
                # Sequence anchored on 20-byte serial response starting with digits.
                if fr.byte_count == 20 and fr.ascii[:7].isdigit():
                    seq = 0
                if seq >= 0:
                    d['seq'] = seq
                    if seq >= len(EXPECTED_BC) or fr.byte_count != EXPECTED_BC[seq]:
                        counts['sequence_errors'] += 1
                        d['sequence_error'] = True
                        seq = -1
                    else:
                        kd = known_decode(seq, fr.regs)
                        if kd: d['known_decode'] = kd
                        seq += 1
                        if seq == len(EXPECTED_BC):
                            counts['cycles'] += 1
                            seq = -1
                f.write(json.dumps(d, ensure_ascii=False) + '\n')
                f.flush()
    counts['end'] = time.time(); counts['elapsed_s'] = round(counts['end'] - counts['start'], 3); counts['out'] = str(out)
    summary_path.write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
