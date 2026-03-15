from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.models import Brush, BrushSide
from bsp.reader import LUMP_BRUSH_SIDES, LUMP_BRUSHES


def read_brushes(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_BRUSHES])
    result = []
    for _ in range(br.length() // Brush.SIZE):
        result.append(asdict(Brush(br.read_int(), br.read_int(), br.read_int())))
    return result


def read_brush_sides(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_BRUSH_SIDES])
    result = []
    for _ in range(br.length() // BrushSide.SIZE):
        result.append(asdict(BrushSide(br.read_int(), br.read_int())))
    return result
