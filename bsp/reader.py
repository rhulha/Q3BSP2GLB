from __future__ import annotations

from pathlib import Path

from .binary_reader import BinaryReader

LUMP_ENTITIES    = 0
LUMP_SHADERS     = 1
LUMP_PLANES      = 2
LUMP_NODES       = 3
LUMP_LEAFS       = 4
LUMP_LEAF_SURF   = 5
LUMP_LEAF_BRUSH  = 6
LUMP_MODELS      = 7
LUMP_BRUSHES     = 8
LUMP_BRUSH_SIDES = 9
LUMP_DRAW_VERTS  = 10
LUMP_DRAW_IDX    = 11
LUMP_FOGS        = 12
LUMP_SURFACES    = 13
LUMP_LIGHTMAPS   = 14
LUMP_LIGHT_GRID  = 15
LUMP_VISIBILITY  = 16
NUM_LUMPS        = 17

Q3_VERSION = 46
Q3_MAGIC   = "IBSP"


def load_bsp(path: Path) -> list[bytes]:
    data = path.read_bytes()
    br = BinaryReader(data)

    magic = br.read_string(4)
    version = br.read_int()
    if magic != Q3_MAGIC:
        raise ValueError(f"not a Q3 BSP (magic={magic!r})")
    if version != Q3_VERSION:
        raise ValueError(f"expected BSP version {Q3_VERSION}, got {version}")

    offsets, lengths = [], []
    for _ in range(NUM_LUMPS):
        offsets.append(br.read_int())
        lengths.append(br.read_int())

    return [data[offsets[i]: offsets[i] + lengths[i]] for i in range(NUM_LUMPS)]
