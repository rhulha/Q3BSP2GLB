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
from bsp.submodels import read_models
from bsp.surfaces import read_surfaces
from bsp.visibility import read_visibility
from bsp.lightmaps import write_lightmaps_bmp
from bsp.lightgrid import write_light_grid_csv
import json

def write_json(out_dir: Path, filename: str, obj) -> None:
    target = out_dir / filename
    with target.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)
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
        ("brushes.json",       read_brushes),
        ("brush_sides.json",   read_brush_sides),
        ("draw_verts.json",    read_draw_verts),
        ("draw_indexes.json",  read_draw_indexes),
        ("fogs.json",          read_fogs),
        ("surfaces.json",      read_surfaces),
        ("visibility.json",    read_visibility),
    ]

    for filename, reader in jobs:
        write_json(out_dir, filename, reader(lumps))

    write_lightmaps_bmp(out_dir, lumps)
    write_light_grid_csv(out_dir, lumps)

    print("done.")


if __name__ == "__main__":
    main()
