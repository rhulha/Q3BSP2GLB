from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.models import Model
from bsp.reader import LUMP_MODELS


def read_models(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_MODELS])
    result = []
    for _ in range(br.length() // Model.SIZE):
        result.append(asdict(Model(
            br.read_floats(3), br.read_floats(3),
            br.read_int(), br.read_int(), br.read_int(), br.read_int(),
        )))
    return result
