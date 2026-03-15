from __future__ import annotations

import csv

from pathlib import Path

from .binary_reader import BinaryReader
from .models import LightGrid
from .reader import LUMP_LIGHT_GRID

def write_light_grid_csv(out_dir: Path, lumps: list[bytes]) -> None:
    br     = BinaryReader(lumps[LUMP_LIGHT_GRID])
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