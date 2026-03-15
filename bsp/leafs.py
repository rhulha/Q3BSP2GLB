from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.reader import LUMP_LEAF_BRUSH, LUMP_LEAF_SURF, LUMP_LEAFS
from dataclasses import dataclass

@dataclass
class Leaf:
    cluster: int
    area: int
    mins: list[int]
    maxs: list[int]
    first_leaf_surface: int
    num_leaf_surfaces: int
    first_leaf_brush: int
    num_leaf_brushes: int
    SIZE = 48


def read_leafs(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_LEAFS])
    result = []
    for _ in range(br.length() // Leaf.SIZE):
        result.append(asdict(Leaf(
            br.read_int(), br.read_int(),
            br.read_ints(3), br.read_ints(3),
            br.read_int(), br.read_int(), br.read_int(), br.read_int(),
        )))
    return result


def read_leaf_surfaces(lumps: list[bytes]) -> list[int]:
    br = BinaryReader(lumps[LUMP_LEAF_SURF])
    return br.read_ints(br.length() // 4)


def read_leaf_brushes(lumps: list[bytes]) -> list[int]:
    br = BinaryReader(lumps[LUMP_LEAF_BRUSH])
    return br.read_ints(br.length() // 4)
