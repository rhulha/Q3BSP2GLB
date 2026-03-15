from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.models import Plane
from bsp.reader import LUMP_PLANES


def read_planes(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_PLANES])
    result = []
    for _ in range(br.length() // Plane.SIZE):
        result.append(asdict(Plane(br.read_floats(3), br.read_float())))
    return result
