# -*- coding: utf-8 -*-
import math
import struct

SIZE = 64


def pixel(x, y):
    cx = x - SIZE / 2 + 0.5
    cy = y - SIZE / 2 + 0.5
    d = math.sqrt(cx * cx + cy * cy)
    r = SIZE / 2 - 2
    if d < r - 2:
        t = max(0.0, 1.0 - d / (r - 2))
        return (int(20 + 40 * t), int(150 + 90 * t), int(30 + 30 * t), 255)
    if d < r:
        return (15, 23, 42, 255)
    return (0, 0, 0, 0)


xor_rows = []
and_rows = []
for y in range(SIZE - 1, -1, -1):
    row = bytearray()
    mask = 0
    bits = 0
    mask_row = bytearray()
    for x in range(SIZE):
        b, g, rr, a = pixel(x, y)
        row += bytes((b, g, rr, a))
        mask = (mask << 1) | (0 if a else 1)
        bits += 1
        if bits == 8:
            mask_row.append(mask)
            mask = 0
            bits = 0
    if bits:
        mask_row.append(mask << (8 - bits))
    xor_rows.append(bytes(row))
    and_rows.append(bytes(mask_row))

xor = b"".join(xor_rows)
and_mask = b"".join(and_rows)
bmi = struct.pack("<IiiHHIIiiII", 40, SIZE, SIZE * 2, 1, 32, 0, len(xor) + len(and_mask), 0, 0, 0, 0)
data = bmi + xor + and_mask
header = struct.pack("<HHH", 0, 1, 1)
entry = struct.pack("<BBBBHHII", SIZE, SIZE, 0, 0, 1, 32, len(data), 6 + 16)
with open(r"C:\Users\lengu\kr-vpn\kr.ico", "wb") as f:
    f.write(header + entry + data)
print("icon written")
