from __future__ import annotations

import configparser
import csv
import json
from pathlib import Path

from bsp.brushes import read_brush_sides, read_brushes
from bsp.draw_verts import read_draw_indexes, read_draw_verts
from bsp.entities import read_entities
from bsp.fogs import read_fogs
from bsp.leafs import read_leaf_brushes, read_leaf_surfaces, read_leafs
from bsp.models import read_models
from bsp.nodes import read_nodes
from bsp.planes import read_planes
from bsp.reader import load_bsp
from bsp.shaders import read_shaders
from bsp.surfaces import read_surfaces
from bsp.visibility import write_visibility_csv
from bsp.lightmaps import write_lightmaps_bmp
from bsp.lightgrid import write_light_grid_csv

_conf = configparser.ConfigParser()
_conf.read(Path(__file__).parent / "conf.ini")
BASE_DIR = Path(_conf["paths"]["base_dir"])




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

def _load_texture_extensions(textures_file: Path) -> dict[str, str]:
    ext_map: dict[str, str] = {}
    with textures_file.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            p = Path(line)
            key = p.with_suffix("").as_posix()
            ext_map[key] = p.suffix
    return ext_map


# The if key in ext_map guard means only shaders that have a matching entry in textures.txt get an extension appended — anything else (noshader, flareShader, models/..., etc.) is left unchanged.

# For models/... shaders: removeprefix("textures/") doesn't strip anything, so the key becomes models/mapobjects/foo. If textures.txt has that path, it will match; if not, it's left alone 

def _apply_shader_extensions(shaders: list[dict], ext_map: dict[str, str]) -> list[dict]:
    for s in shaders:
        name: str = s["shader"]
        key = name.removeprefix("textures/")
        if key in ext_map:
            s["shader"] = name + ext_map[key]
    return shaders


def convert_bsp(bsp_path: Path, out_dir: Path, ext_map: dict[str, str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"parsing {bsp_path} ...")
    lumps = load_bsp(bsp_path)

    shaders = _apply_shader_extensions(read_shaders(lumps), ext_map)
    write_csv(out_dir, "shaders.csv", shaders)

    jobs = [
        ("entities.json",      read_entities),
        ("leaf_surfaces.json", read_leaf_surfaces),
        ("leaf_brushes.json",  read_leaf_brushes),
        ("draw_indexes.json",  read_draw_indexes),
        ("fogs.json",          read_fogs),
        ("surfaces.json",      read_surfaces),
    ]

    for filename, reader in jobs:
        write_json(out_dir, filename, reader(lumps))

    node_rows = [
        {
            "plane_num": n["plane_num"],
            "child0": n["children"][0], "child1": n["children"][1],
            "min_x": n["mins"][0], "min_y": n["mins"][1], "min_z": n["mins"][2],
            "max_x": n["maxs"][0], "max_y": n["maxs"][1], "max_z": n["maxs"][2],
        }
        for n in read_nodes(lumps)
    ]
    write_csv(out_dir, "nodes.csv", node_rows)

    write_visibility_csv(out_dir, lumps)
    model_rows = [
        {
            "min_x": m["mins"][0], "min_y": m["mins"][1], "min_z": m["mins"][2],
            "max_x": m["maxs"][0], "max_y": m["maxs"][1], "max_z": m["maxs"][2],
            "first_surface": m["first_surface"], "num_surfaces": m["num_surfaces"],
            "first_brush": m["first_brush"], "num_brushes": m["num_brushes"],
        }
        for m in read_models(lumps)
    ]
    write_csv(out_dir, "models.csv", model_rows)
    leaf_rows = [
        {
            "cluster": l["cluster"], "area": l["area"],
            "min_x": l["mins"][0], "min_y": l["mins"][1], "min_z": l["mins"][2],
            "max_x": l["maxs"][0], "max_y": l["maxs"][1], "max_z": l["maxs"][2],
            "first_leaf_surface": l["first_leaf_surface"], "num_leaf_surfaces": l["num_leaf_surfaces"],
            "first_leaf_brush": l["first_leaf_brush"], "num_leaf_brushes": l["num_leaf_brushes"],
        }
        for l in read_leafs(lumps)
    ]
    write_csv(out_dir, "leafs.csv", leaf_rows)
    plane_rows = [
        {"nx": p["normal"][0], "ny": p["normal"][1], "nz": p["normal"][2], "distance": p["distance"]}
        for p in read_planes(lumps)
    ]
    write_csv(out_dir, "planes.csv", plane_rows)
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
    print(f"  done -> {out_dir}")


def main() -> None:
    maps_dir = BASE_DIR / "maps"
    bsp_files = sorted(maps_dir.glob("*.bsp"))
    if not bsp_files:
        print(f"no .bsp files found in {maps_dir}")
        return

    print(f"found {len(bsp_files)} BSP file(s) in {maps_dir}:")
    for p in bsp_files:
        print(f"  {p.name}")
    print()

    out_root = Path(__file__).parent / "output"
    textures_file = Path(__file__).parent / "input" / "textures.txt"
    ext_map = _load_texture_extensions(textures_file)

    for bsp_path in bsp_files:
        out_dir = out_root / bsp_path.stem
        convert_bsp(bsp_path, out_dir, ext_map)

    print("all done.")


if __name__ == "__main__":
    main()
