from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.models import Vertex
from bsp.reader import LUMP_DRAW_IDX, LUMP_DRAW_VERTS


def read_draw_verts(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_DRAW_VERTS])
    result = []
    for _ in range(br.length() // Vertex.SIZE):
        xyz    = br.read_floats(3)
        st     = br.read_floats(2)
        lm     = br.read_floats(2)
        normal = br.read_floats(3)
        rgba   = br.read_bytes(4)
        color  = [rgba[0] / 255.0, rgba[1] / 255.0, rgba[2] / 255.0, rgba[3] / 255.0]
        result.append(asdict(Vertex(xyz, st, lm, normal, color)))
    return result


def read_draw_indexes(lumps: list[bytes]) -> list[int]:
    br = BinaryReader(lumps[LUMP_DRAW_IDX])
    return br.read_ints(br.length() // 4)
