import base64

from bsp.binary_reader import BinaryReader
from bsp.reader import LUMP_VISIBILITY


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
