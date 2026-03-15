import configparser
from pathlib import Path
from PIL import Image

_conf = configparser.ConfigParser()
_conf.read(Path(__file__).parent / "conf.ini")
TEXTURE_DIR = Path(_conf["paths"]["texture_dir"])


def main() -> None:
    tga_files = list(TEXTURE_DIR.rglob("*.tga"))
    print(f"Found {len(tga_files)} TGA files")
    for tga in tga_files:
        png = tga.with_suffix(".png")
        Image.open(tga).convert("RGBA").save(png, format="PNG")
        print(f"  {tga.relative_to(TEXTURE_DIR)} -> {png.name}")
    print("done.")


if __name__ == "__main__":
    main()
