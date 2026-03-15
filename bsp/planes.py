from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.reader import LUMP_PLANES
from dataclasses import dataclass

@dataclass
class Plane:
    normal: list[float]
    distance: float
    SIZE = 16

def read_planes(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_PLANES])
    result = []
    for _ in range(br.length() // Plane.SIZE):
        result.append(asdict(Plane(br.read_floats(3), br.read_float())))
    return result
