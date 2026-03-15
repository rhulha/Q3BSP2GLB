from dataclasses import asdict

from bsp.binary_reader import BinaryReader
from bsp.models import Node
from bsp.reader import LUMP_NODES


def read_nodes(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_NODES])
    result = []
    for _ in range(br.length() // Node.SIZE):
        result.append(asdict(Node(br.read_int(), br.read_ints(2), br.read_ints(3), br.read_ints(3))))
    return result
