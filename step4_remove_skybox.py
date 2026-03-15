"""Remove skybox surfaces from output/surfaces.json.

Strategy:
  1. Look for shaders whose name contains the sky keyword (texture hint).
  2. If none found, fall back to the shader group with the largest
     axis-aligned bounding box volume (the skybox typically wraps
     the entire map).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"

def load_shaders() -> list[dict]:
    with (OUTPUT_DIR / "shaders.json").open() as f:
        return json.load(f)


def load_surfaces() -> list[dict]:
    with (OUTPUT_DIR / "surfaces.json").open() as f:
        return json.load(f)


def load_draw_verts() -> list[tuple[float, float, float]]:
    verts: list[tuple[float, float, float]] = []
    with (OUTPUT_DIR / "draw_verts.csv").open() as f:
        for row in csv.DictReader(f):
            verts.append((float(row["x"]), float(row["y"]), float(row["z"])))
    return verts


def bbox_volume(positions: list[tuple[float, float, float]]) -> float:
    if not positions:
        return 0.0
    xs, ys, zs = zip(*positions)
    return (max(xs) - min(xs)) * (max(ys) - min(ys)) * (max(zs) - min(zs))


def find_sky_by_texture(shaders: list[dict], keyword: str) -> list[int]:
    return [i for i, s in enumerate(shaders) if keyword in s["shader"].lower()]


def find_sky_by_bbox(
    surfaces: list[dict],
    draw_verts: list[tuple[float, float, float]],
    shaders: list[dict],
) -> list[int]:
    volumes: dict[int, list[tuple[float, float, float]]] = {}
    for surf in surfaces:
        sn = surf["shader_num"]
        fv, nv = surf["first_vert"], surf["num_verts"]
        if nv == 0:
            continue
        volumes.setdefault(sn, []).extend(draw_verts[fv : fv + nv])

    best_sn = max(volumes, key=lambda sn: bbox_volume(volumes[sn]))
    print(f"  largest bbox belongs to shader {best_sn}: {shaders[best_sn]['shader']}")
    return [best_sn]

# shader[38] = textures/skies/blacksky
SKY_KEYWORD = "sky" # blacksky

def main() -> None:
    shaders = load_shaders()
    surfaces = load_surfaces()

    sky_shader_indices = find_sky_by_texture(shaders, SKY_KEYWORD)

    if sky_shader_indices:
        print("Found sky shader(s) by texture name:")
        for i in sky_shader_indices:
            print(f"  shader[{i}] = {shaders[i]['shader']}")
    else:
        print(f"No '{SKY_KEYWORD}' texture found; falling back to largest bounding box.")
        draw_verts = load_draw_verts()
        sky_shader_indices = find_sky_by_bbox(surfaces, draw_verts, shaders)

    sky_shader_set = set(sky_shader_indices)
    filtered = [s for s in surfaces if s["shader_num"] not in sky_shader_set]
    removed = len(surfaces) - len(filtered)

    surfaces_path = OUTPUT_DIR / "surfaces.json"
    with surfaces_path.open("w") as f:
        json.dump(filtered, f, indent=2)

    print(f"\nRemoved {removed} skybox surface(s). {len(filtered)} surfaces remaining.")
    print(f"Updated {surfaces_path}")


if __name__ == "__main__":
    main()
