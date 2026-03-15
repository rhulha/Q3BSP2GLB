"""Remove skybox surfaces from output/surfaces.json using output/shaders.csv."""

from __future__ import annotations

import csv
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"

def find_sky_by_texture(shaders: list[dict], keywords: list[str]) -> list[int]:
    return [i for i, s in enumerate(shaders) if any(keyword in s["shader"].lower() for keyword in keywords)]


SKIPLIST_PATH = Path(__file__).parent / "skiplist.txt"

def main() -> None:
    with (OUTPUT_DIR / "shaders.csv").open(encoding="utf-8", newline="") as fh:
        shaders = list(csv.DictReader(fh))
    surfaces = json.loads((OUTPUT_DIR / "surfaces.json").read_text())
    skip_list = [line for line in SKIPLIST_PATH.read_text().splitlines() if line.strip()]

    sky_shader_indices = find_sky_by_texture(shaders, skip_list)

    if sky_shader_indices:
        print("Found shader(s) by texture name:")
        for i in sky_shader_indices:
            print(f"  shader[{i}] = {shaders[i]['shader']}")
    else:
        print(f"No skipped textures found; no surfaces removed.")

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
