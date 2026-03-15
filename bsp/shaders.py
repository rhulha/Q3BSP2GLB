from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.models import Shader
from bsp.reader import LUMP_SHADERS


def read_shaders(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_SHADERS])
    result = []
    for _ in range(br.length() // Shader.SIZE):
        name = br.read_string(64).split("\x00", 1)[0]
        result.append(asdict(Shader(name, br.read_int(), br.read_int())))
    return result
