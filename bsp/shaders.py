from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.reader import LUMP_SHADERS
from dataclasses import dataclass

@dataclass
class Shader:
    shader: str
    surface_flags: int
    content_flags: int
    SIZE = 72

def read_shaders(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_SHADERS])
    result = []
    for _ in range(br.length() // Shader.SIZE):
        name = br.read_string(64).split("\x00", 1)[0]
        result.append(asdict(Shader(name, br.read_int(), br.read_int())))
    return result
