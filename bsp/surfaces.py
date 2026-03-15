from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.reader import LUMP_SURFACES
from dataclasses import dataclass

@dataclass
class Surface:
    shader_num: int
    fog_num: int
    surface_type: int
    first_vert: int
    num_verts: int
    first_index: int
    num_indexes: int
    lightmap_num: int
    lm_start: list[int]
    lm_size: list[int]
    lightmap_origin: list[float]
    lightmap_vecs: list[float]
    patch_size: list[int]
    SIZE = 104

def read_surfaces(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_SURFACES])
    result = []
    for _ in range(br.length() // Surface.SIZE):
        result.append(asdict(Surface(
            br.read_int(), br.read_int(), br.read_int(),
            br.read_int(), br.read_int(), br.read_int(), br.read_int(),
            br.read_int(),
            br.read_ints(2), br.read_ints(2),
            br.read_floats(3), br.read_floats(9),
            br.read_ints(2),
        )))
    return result
