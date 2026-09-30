"""Generate assets/icon.png (256x256) with stdlib only: dark tile + amber lens."""

import struct
import zlib


def _chunk(typ: bytes, data: bytes) -> bytes:
    c = typ + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)


def main() -> None:
    n = 256
    bg = (24, 24, 27)  # zinc-950-ish
    amber = (251, 191, 36)
    rows = bytearray()
    cx, cy, r = 108, 112, 62
    for y in range(n):
        rows.append(0)  # filter byte
        for x in range(n):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            # handle: line from (150,154) to (205,209), width ~16
            hx = x - 150
            hy = y - 154
            on_handle = 0 <= hx - hy <= 14 and 0 <= hx <= 70 and 0 <= hy <= 70
            if abs(d - r) < 9:
                px = amber
            elif on_handle and abs(hx - hy - 7) < 8:
                px = amber
            elif d < r:
                px = (39, 39, 42)  # lens glass: zinc-800-ish
            else:
                px = bg
            rows.extend(px)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + _chunk(b"IEND", b"")
    )
    with open("mcpb/assets/icon.png", "wb") as f:
        f.write(png)
    print(f"wrote mcpb/assets/icon.png ({len(png)} bytes)")


if __name__ == "__main__":
    main()
