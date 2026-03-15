from __future__ import annotations

from pathlib import Path

from bsp.brushes import read_brush_sides, read_brushes
from bsp.draw_verts import read_draw_indexes, read_draw_verts
from bsp.entities import read_entities
from bsp.fogs import read_fogs
from bsp.leafs import read_leaf_brushes, read_leaf_surfaces, read_leafs
from bsp.nodes import read_nodes
from bsp.planes import read_planes
from bsp.reader import load_bsp
from bsp.shaders import read_shaders
from bsp.surfaces import read_surfaces
from bsp.visibility import write_visibility_csv
from bsp.lightmaps import write_lightmaps_bmp
from bsp.lightgrid import write_light_grid_csv
import csv
import json

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

def write_json(out_dir: Path, filename: str, obj) -> None:
    target = out_dir / filename
    with target.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)
    print(f"  wrote {target.name}")

def write_csv(out_dir: Path, filename: str, rows: list[dict]) -> None:
    target = out_dir / filename
    with target.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {target.name}")

def main() -> None:
    bsp_path = Path(__file__).parent / "q3dm17.bsp"
    out_dir  = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    print(f"parsing {bsp_path} ...")
    lumps = load_bsp(bsp_path)

    jobs = [
        ("entities.json",      read_entities),
        ("shaders.json",       read_shaders),
        ("planes.json",        read_planes),
        ("nodes.json",         read_nodes),
        ("leafs.json",         read_leafs),
        ("leaf_surfaces.json", read_leaf_surfaces),
        ("leaf_brushes.json",  read_leaf_brushes),
        ("models.json",        read_models),
        ("draw_indexes.json",  read_draw_indexes),
        ("fogs.json",          read_fogs),
        ("surfaces.json",      read_surfaces),
    ]

    for filename, reader in jobs:
        write_json(out_dir, filename, reader(lumps))

    write_visibility_csv(out_dir, lumps)
    write_csv(out_dir, "brushes.csv", read_brushes(lumps))
    write_csv(out_dir, "brush_sides.csv", read_brush_sides(lumps))

    dv_rows = [
        {
            "x": v["xyz"][0], "y": v["xyz"][1], "z": v["xyz"][2],
            "s": v["st"][0],  "t": v["st"][1],
            "lm_s": v["lightmap"][0], "lm_t": v["lightmap"][1],
            "nx": v["normal"][0], "ny": v["normal"][1], "nz": v["normal"][2],
            "r": v["color"][0], "g": v["color"][1], "b": v["color"][2], "a": v["color"][3],
        }
        for v in read_draw_verts(lumps)
    ]
    write_csv(out_dir, "draw_verts.csv", dv_rows)
    write_lightmaps_bmp(out_dir, lumps)
    write_light_grid_csv(out_dir, lumps)

    print("done.")


if __name__ == "__main__":
    main()
