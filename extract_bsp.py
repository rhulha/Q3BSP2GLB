from __future__ import annotations

import base64
import csv
import io
import json
import re
import struct
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path


# ── Binary reader ────────────────────────────────────────────────────────────

class BinaryReader:
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)
        self._data_len = len(data)

    def read_bytes(self, count: int) -> bytes:
        data = self._buf.read(count)
        if len(data) != count:
            raise EOFError(f"expected {count} bytes, got {len(data)}")
        return data

    def read_int(self) -> int:
        return struct.unpack("<i", self.read_bytes(4))[0]

    def read_ints(self, count: int) -> list[int]:
        if count == 0:
            return []
        return list(struct.unpack(f"<{count}i", self.read_bytes(4 * count)))

    def read_float(self) -> float:
        return struct.unpack("<f", self.read_bytes(4))[0]

    def read_floats(self, count: int) -> list[float]:
        if count == 0:
            return []
        return list(struct.unpack(f"<{count}f", self.read_bytes(4 * count)))

    def read_string(self, length: int) -> str:
        return self.read_bytes(length).decode("latin-1", errors="ignore")

    def length(self) -> int:
        return self._data_len


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class Shader:
    shader: str
    surface_flags: int
    content_flags: int
    SIZE = 72


@dataclass
class Plane:
    normal: list[float]
    distance: float
    SIZE = 16


@dataclass
class Node:
    plane_num: int
    children: list[int]
    mins: list[int]
    maxs: list[int]
    SIZE = 36


@dataclass
class Leaf:
    cluster: int
    area: int
    mins: list[int]
    maxs: list[int]
    first_leaf_surface: int
    num_leaf_surfaces: int
    first_leaf_brush: int
    num_leaf_brushes: int
    SIZE = 48


@dataclass
class Model:
    mins: list[float]
    maxs: list[float]
    first_surface: int
    num_surfaces: int
    first_brush: int
    num_brushes: int
    SIZE = 40


@dataclass
class Brush:
    first_side: int
    num_sides: int
    shader_num: int
    SIZE = 12


@dataclass
class BrushSide:
    plane_num: int
    shader_num: int
    SIZE = 8


@dataclass
class Vertex:
    xyz: list[float]
    st: list[float]
    lightmap: list[float]
    normal: list[float]
    color: list[float]
    SIZE = 44


@dataclass
class Fog:
    shader: str
    brush_num: int
    visible_side: int
    SIZE = 72


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


@dataclass
class LightGrid:
    ambient: list[int]
    directional: list[int]
    direction: list[int]
    SIZE = 8


# ── Entity parser ────────────────────────────────────────────────────────────

_QUOTED_PAIR_RE = re.compile(r'\s*"([^"]*)"\s+"([^"]*)"\s*')


def parse_entities(text: str) -> dict[str, list[dict[str, str]]]:
    entities: dict[str, list[dict[str, str]]] = defaultdict(list)
    current: dict[str, str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "{":
            current = {}
            continue
        if line == "}":
            if current is None:
                raise ValueError("unexpected closing entity brace")
            classname = current.get("classname", "")
            entities[classname].append(current)
            current = None
            continue
        if current is None:
            continue
        match = _QUOTED_PAIR_RE.fullmatch(line)
        if not match:
            continue
        current[match.group(1)] = match.group(2)
    return dict(entities)


# ── BSP reader ───────────────────────────────────────────────────────────────

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


# ── Lump extractors ──────────────────────────────────────────────────────────

def read_entities(lumps: list[bytes]) -> dict:
    text = lumps[LUMP_ENTITIES].decode("latin-1", errors="ignore")
    return parse_entities(text)


def read_shaders(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_SHADERS])
    result = []
    for _ in range(br.length() // Shader.SIZE):
        name = br.read_string(64).split("\x00", 1)[0]
        result.append(asdict(Shader(name, br.read_int(), br.read_int())))
    return result


def read_planes(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_PLANES])
    result = []
    for _ in range(br.length() // Plane.SIZE):
        normal = br.read_floats(3)
        dist = br.read_float()
        result.append(asdict(Plane(normal, dist)))
    return result


def read_nodes(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_NODES])
    result = []
    for _ in range(br.length() // Node.SIZE):
        result.append(asdict(Node(br.read_int(), br.read_ints(2), br.read_ints(3), br.read_ints(3))))
    return result


def read_leafs(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_LEAFS])
    result = []
    for _ in range(br.length() // Leaf.SIZE):
        result.append(asdict(Leaf(
            br.read_int(), br.read_int(),
            br.read_ints(3), br.read_ints(3),
            br.read_int(), br.read_int(), br.read_int(), br.read_int(),
        )))
    return result


def read_leaf_surfaces(lumps: list[bytes]) -> list[int]:
    br = BinaryReader(lumps[LUMP_LEAF_SURF])
    return br.read_ints(br.length() // 4)


def read_leaf_brushes(lumps: list[bytes]) -> list[int]:
    br = BinaryReader(lumps[LUMP_LEAF_BRUSH])
    return br.read_ints(br.length() // 4)


def read_models(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_MODELS])
    result = []
    for _ in range(br.length() // Model.SIZE):
        result.append(asdict(Model(
            br.read_floats(3), br.read_floats(3),
            br.read_int(), br.read_int(), br.read_int(), br.read_int(),
        )))
    return result


def read_brushes(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_BRUSHES])
    result = []
    for _ in range(br.length() // Brush.SIZE):
        result.append(asdict(Brush(br.read_int(), br.read_int(), br.read_int())))
    return result


def read_brush_sides(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_BRUSH_SIDES])
    result = []
    for _ in range(br.length() // BrushSide.SIZE):
        result.append(asdict(BrushSide(br.read_int(), br.read_int())))
    return result


def read_draw_verts(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_DRAW_VERTS])
    result = []
    for _ in range(br.length() // Vertex.SIZE):
        xyz     = br.read_floats(3)
        st      = br.read_floats(2)
        lm      = br.read_floats(2)
        normal  = br.read_floats(3)
        rgba    = br.read_bytes(4)
        color   = [rgba[0] / 255.0, rgba[1] / 255.0, rgba[2] / 255.0, rgba[3] / 255.0]
        result.append(asdict(Vertex(xyz, st, lm, normal, color)))
    return result


def read_draw_indexes(lumps: list[bytes]) -> list[int]:
    br = BinaryReader(lumps[LUMP_DRAW_IDX])
    return br.read_ints(br.length() // 4)


def read_fogs(lumps: list[bytes]) -> list[dict]:
    br = BinaryReader(lumps[LUMP_FOGS])
    result = []
    for _ in range(br.length() // Fog.SIZE):
        name = br.read_string(64).split("\x00", 1)[0]
        result.append(asdict(Fog(name, br.read_int(), br.read_int())))
    return result


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


def _make_bmp(rgb_data: bytes, width: int, height: int) -> bytes:
    # BMP rows are bottom-to-top and in BGR order; row stride must be 4-byte aligned
    row_size = (width * 3 + 3) & ~3
    pixel_data = bytearray(row_size * height)
    for y in range(height):
        src_row = (height - 1 - y) * width * 3
        dst_row = y * row_size
        for x in range(width):
            r, g, b = rgb_data[src_row + x*3], rgb_data[src_row + x*3+1], rgb_data[src_row + x*3+2]
            pixel_data[dst_row + x*3]   = b
            pixel_data[dst_row + x*3+1] = g
            pixel_data[dst_row + x*3+2] = r

    file_size = 14 + 40 + len(pixel_data)
    file_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
    dib_header  = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(pixel_data), 2835, 2835, 0, 0)
    return file_header + dib_header + bytes(pixel_data)


def write_lightmaps_bmp(out_dir: Path, lumps: list[bytes]) -> None:
    data  = lumps[LUMP_LIGHTMAPS]
    block = 128 * 128 * 3
    lm_dir = out_dir / "lightmaps"
    lm_dir.mkdir(exist_ok=True)
    count = 0
    for i, offset in enumerate(range(0, len(data), block)):
        bmp = _make_bmp(data[offset: offset + block], 128, 128)
        (lm_dir / f"lightmap_{i:03d}.bmp").write_bytes(bmp)
        count += 1
    print(f"  wrote {count} BMP files in lightmaps/")



def read_visibility(lumps: list[bytes]) -> dict:
    br = BinaryReader(lumps[LUMP_VISIBILITY])
    if br.length() < 8:
        return {"n_vecs": 0, "sz_vecs": 0, "vecs": ""}
    n_vecs  = br.read_int()
    sz_vecs = br.read_int()
    vecs    = br.read_bytes(n_vecs * sz_vecs)
    return {
        "n_vecs":  n_vecs,
        "sz_vecs": sz_vecs,
        "vecs":    base64.b64encode(vecs).decode("ascii"),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def write_json(out_dir: Path, filename: str, obj) -> None:
    target = out_dir / filename
    with target.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)
    print(f"  wrote {target.name}")


def write_light_grid_csv(out_dir: Path, lumps: list[bytes]) -> None:
    br = BinaryReader(lumps[LUMP_LIGHT_GRID])
    target = out_dir / "light_grid.csv"
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "ambient_r", "ambient_g", "ambient_b",
            "directional_r", "directional_g", "directional_b",
            "direction_phi", "direction_theta",
        ])
        for _ in range(br.length() // LightGrid.SIZE):
            ambient     = list(br.read_bytes(3))
            directional = list(br.read_bytes(3))
            direction   = list(br.read_bytes(2))
            writer.writerow(ambient + directional + direction)
    print(f"  wrote {target.name}")


def main() -> None:
    bsp_path = Path(__file__).parent / "q3dm17.bsp"
    out_dir  = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    print(f"parsing {bsp_path} …")
    lumps = load_bsp(bsp_path)

    jobs = [
        ("entities.json",    read_entities),
        ("shaders.json",     read_shaders),
        ("planes.json",      read_planes),
        ("nodes.json",       read_nodes),
        ("leafs.json",       read_leafs),
        ("leaf_surfaces.json", read_leaf_surfaces),
        ("leaf_brushes.json",  read_leaf_brushes),
        ("models.json",      read_models),
        ("brushes.json",     read_brushes),
        ("brush_sides.json", read_brush_sides),
        ("draw_verts.json",  read_draw_verts),
        ("draw_indexes.json",read_draw_indexes),
        ("fogs.json",        read_fogs),
        ("surfaces.json",    read_surfaces),
        ("visibility.json",  read_visibility),
    ]

    for filename, reader in jobs:
        data = reader(lumps)
        write_json(out_dir, filename, data)

    write_lightmaps_bmp(out_dir, lumps)
    write_light_grid_csv(out_dir, lumps)

    print("done.")


if __name__ == "__main__":
    main()
