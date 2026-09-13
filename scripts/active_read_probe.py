#!/usr/bin/env python3
"""Read-only Modbus RTU-over-TCP probe for the temporary RS232/IP gateway.
WARNING: unlike passive_capture.py this sends Modbus read requests on TX. It does
not write registers, but only run it when you accept active polling on the bus.
"""
from __future__ import annotations

import argparse, json, socket, time
from pathlib import Path
from jsd_rtu import crc16_modbus, decode_response, extract_responses


def req(unit: int, fn: int, addr: int, count: int) -> bytes:
    p = bytes([unit, fn, (addr >> 8) & 255, addr & 255, (count >> 8) & 255, count & 255])
    c = crc16_modbus(p)
    return p + bytes([c & 255, (c >> 8) & 255])


def drain(sock: socket.socket, quiet_s: float = 0.15, max_s: float = 2.0) -> int:
    """Drain unsolicited bytes before an active request; returns discarded byte count."""
    end = time.time() + max_s
    discarded = 0
    last = time.time()
    sock.settimeout(0.05)
    while time.time() < end and time.time() - last < quiet_s:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            continue
        if not chunk:
            break
        discarded += len(chunk)
        last = time.time()
    return discarded


def extract_matching(buf: bytearray, unit: int, fn: int, expected_bc: int):
    """Return a response matching unit/fn/byte-count; discard unrelated spontaneous frames."""
    while len(buf) >= 5:
        start = None
        for i in range(len(buf) - 1):
            if buf[i] == unit and buf[i + 1] in (fn, fn | 0x80):
                start = i
                break
        if start is None:
            del buf[:-1]
            return None
        if start:
            del buf[:start]
        if len(buf) < 5:
            return None
        if buf[1] == (fn | 0x80):
            flen = 5
        else:
            bc = buf[2]
            if bc != expected_bc:
                # Complete unrelated response from the autonomous stream: drop it.
                if bc > 0 and bc <= 252 and not (bc & 1) and len(buf) >= bc + 5:
                    del buf[:bc + 5]
                    continue
                del buf[0]
                continue
            flen = bc + 5
        if len(buf) < flen:
            return None
        frame = bytes(buf[:flen]); del buf[:flen]
        return frame
    return None


def read_once(sock: socket.socket, unit: int, fn: int, addr: int, count: int, timeout: float):
    discarded = drain(sock)
    expected_bc = count * 2
    request_ts = time.time()
    sock.sendall(req(unit, fn, addr, count))
    deadline = time.time() + timeout
    buf = bytearray()
    while time.time() < deadline:
        sock.settimeout(max(0.05, deadline - time.time()))
        try: chunk = sock.recv(4096)
        except socket.timeout: break
        if not chunk: break
        buf.extend(chunk)
        frame = extract_matching(buf, unit, fn, expected_bc)
        if frame:
            d = decode_response(frame).asdict()
            d.update({'latency_ms': round((time.time() - request_ts) * 1000, 1), 'discarded_before_request_bytes': discarded})
            return d
    return {'unit': unit, 'function': fn, 'address': addr, 'count': count, 'error': 'timeout', 'discarded_before_request_bytes': discarded, 'raw_buffer_hex': bytes(buf).hex(' ')}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='192.168.x.x')
    ap.add_argument('--port', type=int, default=6666)
    ap.add_argument('--unit', type=int, default=1)
    ap.add_argument('--function', type=int, choices=[3,4], default=3)
    ap.add_argument('--ranges', default='0x0000:32,0x0050:16,0x0080:16,0x0090:16,0x0320:32')
    ap.add_argument('--count', type=int, default=8)
    ap.add_argument('--timeout', type=float, default=1.5)
    ap.add_argument('--delay', type=float, default=0.2)
    ap.add_argument('--out', default='../captures/active_probe.jsonl')
    args = ap.parse_args()
    out = Path(args.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    starts=[]
    for item in args.ranges.split(','):
        a,n=item.split(':')
        starts.append((int(a,0), int(n,0)))
    with socket.create_connection((args.host, args.port), timeout=5) as s, out.open('w', encoding='utf-8') as f:
        for start, total in starts:
            for addr in range(start, start + total, args.count):
                n = min(args.count, start + total - addr)
                r = read_once(s, args.unit, args.function, addr, n, args.timeout)
                r.update({'request_address': addr, 'request_count': n, 'request_address_hex': f'0x{addr:04X}'})
                f.write(json.dumps(r, ensure_ascii=False) + '\n'); f.flush()
                print(json.dumps(r, ensure_ascii=False))
                time.sleep(args.delay)
    print('saved', out)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
