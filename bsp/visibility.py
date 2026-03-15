import csv
from pathlib import Path

from bsp.binary_reader import BinaryReader
from bsp.reader import LUMP_VISIBILITY


def write_visibility_csv(out_dir: Path, lumps: list[bytes]) -> None:
    br = BinaryReader(lumps[LUMP_VISIBILITY])
    if br.length() < 8:
        return
    n_vecs  = br.read_int()
    sz_vecs = br.read_int()
    vecs    = br.read_bytes(n_vecs * sz_vecs)

    target = out_dir / "visibility.csv"
    with target.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(range(n_vecs))
        for i in range(n_vecs):
            row_bytes = vecs[i * sz_vecs : (i + 1) * sz_vecs]
            bits = [
                (row_bytes[j // 8] >> (j % 8)) & 1
                for j in range(n_vecs)
            ]
            writer.writerow(bits)
    print(f"  wrote {target.name}")
