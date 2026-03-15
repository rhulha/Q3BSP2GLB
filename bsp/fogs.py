from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.reader import LUMP_FOGS
from dataclasses import dataclass

@dataclass
class Fog:
    shader: str
    brush_num: int
    visible_side: int
    SIZE = 72

def read_fogs(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_FOGS])
    result = []
    for _ in range(br.length() // Fog.SIZE):
        name = br.read_string(64).split("\x00", 1)[0]
        result.append(asdict(Fog(name, br.read_int(), br.read_int())))
    return result
