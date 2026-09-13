#!/usr/bin/env python3
"""Helpers for JSD Solar J6500HC RTU-over-TCP/passive RS232 captures."""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Optional


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


@dataclass
class Frame:
    ts: float
    raw_hex: str
    unit: int
    function: int
    byte_count: Optional[int]
    data_hex: str
    crc_ok: bool
    crc_calc: str
    crc_seen: str
    regs: list[int]
    ascii: str

    def asdict(self):
        return asdict(self)


def decode_response(frame: bytes, ts: Optional[float] = None) -> Frame:
    if ts is None:
        ts = time.time()
    unit = frame[0]
    fn = frame[1]
    bc = frame[2] if len(frame) >= 5 and fn in (3, 4) else None
    data = frame[3:-2] if bc is not None else b''
    seen = frame[-2] | (frame[-1] << 8)
    calc = crc16_modbus(frame[:-2])
    regs = []
    if bc is not None:
        for i in range(0, min(len(data), bc), 2):
            if i + 1 < len(data):
                regs.append((data[i] << 8) | data[i+1])
    asc = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
    return Frame(ts, frame.hex(' '), unit, fn, bc, data.hex(' '), calc == seen,
                 f'0x{calc:04X}', f'0x{seen:04X}', regs, asc)


def extract_responses(buf: bytearray, max_byte_count: int = 64) -> list[bytes]:
    """Extract CRC-valid or complete-looking FC03/FC04 response frames from a stream buffer."""
    out: list[bytes] = []
    while len(buf) >= 5:
        start = None
        for i in range(len(buf) - 1):
            if buf[i] == 0x01 and buf[i+1] in (0x03, 0x04):
                start = i
                break
        if start is None:
            del buf[:-1]
            break
        if start:
            del buf[:start]
        if len(buf) < 5:
            break
        bc = buf[2]
        if bc == 0 or bc > max_byte_count or bc & 1:
            del buf[0]
            continue
        flen = bc + 5
        if len(buf) < flen:
            break
        frame = bytes(buf[:flen])
        out.append(frame)
        del buf[:flen]
    return out


def u16s_to_signed(regs: list[int]) -> list[int]:
    return [r - 0x10000 if r & 0x8000 else r for r in regs]


def known_decode(seq: int, regs: list[int]) -> dict:
    s = u16s_to_signed(regs)
    if seq == 5 and len(s) >= 4:
        return {'block': 'grid_a_0x0050', 'grid_voltage_v': s[0]*0.1, 'grid_current_a': s[1]*0.01, 'grid_frequency_hz': s[2]*0.01, 'grid_power_w': s[3]}
    if seq == 6 and len(s) >= 6:
        return {'block': 'output_a_0x0058', 'output_voltage_v': s[0]*0.1, 'output_current_a': s[1]*0.01, 'output_frequency_hz': s[2]*0.01, 'output_power_w': s[3], 'output_apparent_va': s[4], 'load_pct': s[5]*0.1}
    if seq == 7 and len(s) >= 2:
        return {'block': 'battery_0x0080', 'battery_voltage_v': s[0]*0.1, 'battery_current_a': s[1]*0.1}
    if seq == 8 and len(s) >= 2:
        return {'block': 'battery_soc_power_0x0084', 'battery_soc_pct': s[0], 'battery_power_w': s[1]}
    if seq == 9 and len(regs) >= 4:
        return {'block': 'terminal_status_raw', 'raw': regs[:4], 'hex': [f'0x{x:04X}' for x in regs[:4]]}
    if seq == 10 and len(s) >= 3:
        return {'block': 'pv1_0x0096', 'pv1_voltage_v': s[0]*0.1, 'pv1_current_a': s[1]*0.01, 'pv1_power_w': s[2]}
    if seq == 11 and regs:
        return {'block': 'fan_0x0320', 'fan_raw': regs[0]}
    if seq == 12 and len(s) >= 3:
        return {'block': 'temperature_0x0330', 'pv1_temp_c': s[0]*0.1, 'inverter_temp_c': s[1]*0.1, 'charger_temp_c': s[2]*0.1, 'raw': regs[:3], 'hex': [f'0x{x:04X}' for x in regs[:3]]}
    if seq == 13 and len(regs) >= 2:
        return {'block': 'temperature_raw_extra', 'raw4': regs[0], 'raw5': regs[1], 'hex': [f'0x{x:04X}' for x in regs[:2]]}
    return {}
