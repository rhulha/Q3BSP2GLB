import json
import csv
import struct
import configparser
from pathlib import Path

OUTPUT_DIR = "output"
OUTPUT_GLB = "C:\\Action\\id\\q3unpacked\\map.glb"

_conf = configparser.ConfigParser()
_conf.read(Path(__file__).parent / "conf.ini")
TEXTURE_DIR = Path(_conf["paths"]["texture_dir"])
TESSELLATION_LEVEL = 5

SURFACE_PLANAR = 1
SURFACE_PATCH = 2
SURFACE_MESH = 3

GLTF_FLOAT = 5126
GLTF_UNSIGNED_INT = 5125
GLTF_ARRAY_BUFFER = 34962
GLTF_ELEMENT_ARRAY_BUFFER = 34963


def load_texture(shader_name: str):
    rel = shader_name.removeprefix("textures/")
    path = TEXTURE_DIR / rel
    if not path.exists():
        return None
    suffix = path.suffix.lower()
    if suffix in ('.jpg', '.jpeg'):
        return ('image/jpeg', path.read_bytes())
    if suffix == '.png':
        return ('image/png', path.read_bytes())
    return None


def read_surfaces():
    with open(f"{OUTPUT_DIR}/surfaces.json") as f:
        return json.load(f)


def read_draw_verts():
    verts = []
    with open(f"{OUTPUT_DIR}/draw_verts.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            x, y, z = float(row['x']), float(row['y']), float(row['z'])
            nx, ny, nz = float(row['nx']), float(row['ny']), float(row['nz'])
            verts.append({
                'pos': [x, z, -y],
                'normal': [nx, nz, -ny],
                'uv': [float(row['s']), float(row['t'])],
                'lm_uv': [float(row['lm_s']), float(row['lm_t'])],
            })
    return verts


def read_draw_indexes():
    with open(f"{OUTPUT_DIR}/draw_indexes.json") as f:
        return json.load(f)


def read_shaders():
    with open(f"{OUTPUT_DIR}/shaders.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bezier3_vert(p0, p1, p2, t):
    mt = 1 - t
    def b(a, b, c, n):
        return [mt*mt*a[i] + 2*mt*t*b[i] + t*t*c[i] for i in range(n)]
    return {
        'pos':    b(p0['pos'],    p1['pos'],    p2['pos'],    3),
        'normal': b(p0['normal'], p1['normal'], p2['normal'], 3),
        'uv':     b(p0['uv'],     p1['uv'],     p2['uv'],     2),
        'lm_uv':  b(p0['lm_uv'], p1['lm_uv'], p2['lm_uv'],  2),
    }


def tessellate_bezier_patch(cp3x3, level):
    stride = level + 1
    grid = []
    for row in range(stride):
        t = row / level
        for col in range(stride):
            s = col / level
            r0 = bezier3_vert(cp3x3[0][0], cp3x3[0][1], cp3x3[0][2], s)
            r1 = bezier3_vert(cp3x3[1][0], cp3x3[1][1], cp3x3[1][2], s)
            r2 = bezier3_vert(cp3x3[2][0], cp3x3[2][1], cp3x3[2][2], s)
            grid.append(bezier3_vert(r0, r1, r2, t))

    indices = []
    for row in range(level):
        for col in range(level):
            i = row * stride + col
            indices.extend([i, i + stride, i + 1])
            indices.extend([i + 1, i + stride, i + stride + 1])

    return grid, indices


def get_patch_geometry(surface, all_verts, level):
    pw, ph = surface['patch_size']
    first_vert = surface['first_vert']
    sub_rows = (ph - 1) // 2
    sub_cols = (pw - 1) // 2

    out_verts = []
    out_indices = []

    for sr in range(sub_rows):
        for sc in range(sub_cols):
            cp = []
            for r in range(3):
                row_cp = []
                for c in range(3):
                    idx = first_vert + (sr * 2 + r) * pw + (sc * 2 + c)
                    row_cp.append(all_verts[idx])
                cp.append(row_cp)

            base = len(out_verts)
            vs, idxs = tessellate_bezier_patch(cp, level)
            out_verts.extend(vs)
            out_indices.extend(i + base for i in idxs)

    return out_verts, out_indices


def build_groups(surfaces, draw_verts, draw_indexes, level):
    groups = {}

    for surf in surfaces:
        stype = surf['surface_type']
        shader_num = surf['shader_num']

        if stype == SURFACE_PATCH:
            verts, indices = get_patch_geometry(surf, draw_verts, level)

        elif stype in (SURFACE_PLANAR, SURFACE_MESH):
            fv = surf['first_vert']
            nv = surf['num_verts']
            fi = surf['first_index']
            ni = surf['num_indexes']
            if ni == 0:
                continue
            verts = draw_verts[fv:fv + nv]
            indices = draw_indexes[fi:fi + ni]

        else:
            continue

        if not verts or not indices:
            continue

        if shader_num not in groups:
            groups[shader_num] = {'verts': [], 'indices': []}

        base = len(groups[shader_num]['verts'])
        groups[shader_num]['verts'].extend(verts)
        groups[shader_num]['indices'].extend(i + base for i in indices)

    return groups


def pack_primitives(groups):
    binary = bytearray()
    buffer_views = []
    accessors = []
    primitives = []

    def add_data(data_bytes, target):
        offset = len(binary)
        binary.extend(data_bytes)
        pad = (4 - len(data_bytes) % 4) % 4
        binary.extend(b'\x00' * pad)
        bv_idx = len(buffer_views)
        buffer_views.append({
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": len(data_bytes),
            "target": target,
        })
        return bv_idx

    for shader_num, group in groups.items():
        verts = group['verts']
        indices = group['indices']

        positions = [c for v in verts for c in v['pos']]
        normals   = [c for v in verts for c in v['normal']]
        uvs       = [c for v in verts for c in v['uv']]

        # GLTF uses counter-clockwise winding, but Quake 3 uses clockwise, so we need to reverse the order of every triangle
        indices = [indices[i + j] for i in range(0, len(indices), 3) for j in (2, 1, 0)]

        pos_bytes  = struct.pack(f'<{len(positions)}f', *positions)
        norm_bytes = struct.pack(f'<{len(normals)}f', *normals)
        uv_bytes   = struct.pack(f'<{len(uvs)}f', *uvs)
        idx_bytes  = struct.pack(f'<{len(indices)}I', *indices)

        pos_bv  = add_data(pos_bytes,  GLTF_ARRAY_BUFFER)
        norm_bv = add_data(norm_bytes, GLTF_ARRAY_BUFFER)
        uv_bv   = add_data(uv_bytes,   GLTF_ARRAY_BUFFER)
        idx_bv  = add_data(idx_bytes,  GLTF_ELEMENT_ARRAY_BUFFER)

        n_verts = len(verts)
        all_pos = [v['pos'] for v in verts]
        min_pos = [min(v[i] for v in all_pos) for i in range(3)]
        max_pos = [max(v[i] for v in all_pos) for i in range(3)]

        pos_acc = len(accessors)
        accessors.append({"bufferView": pos_bv,  "componentType": GLTF_FLOAT, "count": n_verts, "type": "VEC3", "min": min_pos, "max": max_pos})
        norm_acc = len(accessors)
        accessors.append({"bufferView": norm_bv, "componentType": GLTF_FLOAT, "count": n_verts, "type": "VEC3"})
        uv_acc = len(accessors)
        accessors.append({"bufferView": uv_bv,   "componentType": GLTF_FLOAT, "count": len(uvs) // 2, "type": "VEC2"})
        idx_acc = len(accessors)
        accessors.append({"bufferView": idx_bv,  "componentType": GLTF_UNSIGNED_INT, "count": len(indices), "type": "SCALAR"})

        primitives.append({
            "shader_num": shader_num,
            "attributes": {
                "POSITION":   pos_acc,
                "NORMAL":     norm_acc,
                "TEXCOORD_0": uv_acc,
            },
            "indices": idx_acc,
        })

    return bytes(binary), buffer_views, accessors, primitives


def write_glb(json_data, binary_data, output_path):
    json_bytes = json.dumps(json_data).encode('utf-8')
    json_pad = (4 - len(json_bytes) % 4) % 4
    json_bytes += b' ' * json_pad

    bin_bytes = binary_data if binary_data else b''
    bin_pad = (4 - len(bin_bytes) % 4) % 4
    bin_bytes += b'\x00' * bin_pad

    total = 12 + 8 + len(json_bytes) + (8 + len(bin_bytes) if bin_bytes else 0)

    with open(output_path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<I4s', len(json_bytes), b'JSON'))
        f.write(json_bytes)
        if bin_bytes:
            f.write(struct.pack('<I4s', len(bin_bytes), b'BIN\0'))
            f.write(bin_bytes)


def main():
    print("Reading output data...")
    surfaces = read_surfaces()
    draw_verts = read_draw_verts()
    draw_indexes = read_draw_indexes()
    shaders = read_shaders()

    print(f"  {len(surfaces)} surfaces, {len(draw_verts)} verts, {len(draw_indexes)} indexes, {len(shaders)} shaders")

    print("Building geometry groups by shader...")
    groups = build_groups(surfaces, draw_verts, draw_indexes, TESSELLATION_LEVEL)
    print(f"  {len(groups)} shader groups")

    print("Packing binary data...")
    binary, buffer_views, accessors, prim_data = pack_primitives(groups)

    images = []
    textures = []
    samplers = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]

    shader_to_tex: dict[int, int] = {}
    for i, shader in enumerate(shaders):
        result = load_texture(shader['shader'])
        if result is not None:
            mime, img_bytes = result
            bv_idx = len(buffer_views)
            offset = len(binary)
            binary = binary + img_bytes
            pad = (4 - len(img_bytes) % 4) % 4
            binary = binary + b'\x00' * pad
            buffer_views.append({
                "buffer": 0,
                "byteOffset": offset,
                "byteLength": len(img_bytes),
            })
            img_idx = len(images)
            images.append({"bufferView": bv_idx, "mimeType": mime})
            tex_idx = len(textures)
            textures.append({"sampler": 0, "source": img_idx})
            shader_to_tex[i] = tex_idx

    materials = []
    shader_to_material = {}
    for i, shader in enumerate(shaders):
        mat: dict = {"name": shader['shader'], "doubleSided": True, "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": 1.0}}
        if i in shader_to_tex:
            mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": shader_to_tex[i]}
        materials.append(mat)
        shader_to_material[i] = i

    meshes = []
    nodes = []
    for pd in prim_data:
        shader_num = pd["shader_num"]
        shader_name = shaders[shader_num]['shader'] if shader_num < len(shaders) else f"shader_{shader_num}"
        mesh_idx = len(meshes)
        meshes.append({
            "name": shader_name,
            "primitives": [{
                "attributes": pd["attributes"],
                "indices": pd["indices"],
                "material": shader_to_material.get(shader_num, 0),
            }]
        })
        nodes.append({"name": shader_name, "mesh": mesh_idx})

    SCALE = 0.038
    root_node_idx = len(nodes)
    nodes.append({"name": "map", "scale": [SCALE, SCALE, SCALE], "children": list(range(len(nodes)))})

    gltf = {
        "asset": {"version": "2.0", "generator": "BSPParserPythonQ3"},
        "scene": 0,
        "scenes": [{"name": "Scene", "nodes": [root_node_idx]}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(binary)}],
    }
    if images:
        gltf["samplers"] = samplers
        gltf["textures"] = textures
        gltf["images"] = images

    print(f"Writing {OUTPUT_GLB}...")
    write_glb(gltf, binary, OUTPUT_GLB)
    print(f"Done. {len(binary) // 1024} KB binary data, {len(meshes)} meshes.")


if __name__ == "__main__":
    main()
