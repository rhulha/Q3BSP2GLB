from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.models import Surface
from bsp.reader import LUMP_SURFACES


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
