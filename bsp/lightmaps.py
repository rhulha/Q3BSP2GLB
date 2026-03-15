
import struct
from pathlib import Path

from .reader import LUMP_LIGHTMAPS

def _make_bmp(rgb_data: bytes, width: int, height: int) -> bytes:
    row_size = (width * 3 + 3) & ~3
    pixel_data = bytearray(row_size * height)
    for y in range(height):
        src_row = (height - 1 - y) * width * 3
        dst_row = y * row_size
        for x in range(width):
            r = rgb_data[src_row + x * 3]
            g = rgb_data[src_row + x * 3 + 1]
            b = rgb_data[src_row + x * 3 + 2]
            pixel_data[dst_row + x * 3]     = b
            pixel_data[dst_row + x * 3 + 1] = g
            pixel_data[dst_row + x * 3 + 2] = r
    file_size   = 14 + 40 + len(pixel_data)
    file_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
    dib_header  = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(pixel_data), 2835, 2835, 0, 0)
    return file_header + dib_header + bytes(pixel_data)


def write_lightmaps_bmp(out_dir: Path, lumps: list[bytes]) -> None:
    data   = lumps[LUMP_LIGHTMAPS]
    block  = 128 * 128 * 3
    lm_dir = out_dir / "lightmaps"
    lm_dir.mkdir(exist_ok=True)
    count  = 0
    for i, offset in enumerate(range(0, len(data), block)):
        bmp = _make_bmp(data[offset: offset + block], 128, 128)
        (lm_dir / f"lightmap_{i:03d}.bmp").write_bytes(bmp)
        count += 1
    print(f"  wrote {count} BMP files in lightmaps/")