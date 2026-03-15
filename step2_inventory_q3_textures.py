import os
import configparser
from pathlib import Path

_conf = configparser.ConfigParser()
_conf.read(Path(__file__).parent / "conf.ini")
texture_dir = Path(_conf["paths"]["texture_dir"])

output = Path(__file__).parent / "input" / "textures.txt"

with output.open("w") as f:
    for dirpath, _, filenames in os.walk(texture_dir):
        for filename in sorted(filenames):
            if filename.lower().endswith(".tga"):
                continue
            full = Path(dirpath) / filename
            rel = full.relative_to(texture_dir)
            f.write(rel.as_posix() + "\n")

print(f"Textures inventory written to {output}")
