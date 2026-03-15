# Quake 3 BSP File Format — Rendering Overview

## File Structure

A Q3 BSP file begins with a **header** containing the magic number `IBSP` and version `0x2E` (46), followed by a **directory of 17 lumps**, each described by an offset and length.

---

## Key Lumps for Rendering

### 1. Shaders (Lump 1)
Each shader entry is 72 bytes: a 64-byte texture path string + surface flags + content flags. Maps geometry to materials. The path points to a `.shader` script or a direct texture file.

### 2. Planes (Lump 2)
`float[3] normal, float distance` — used by the BSP tree for frustum culling and PVS traversal, not directly rendered.

### 3. Nodes (Lump 3) & Leaves (Lump 4)
The BSP tree. Each **node** splits space with a plane; each **leaf** holds references into the face and brush lists. Used to determine which leaf the camera is in.

### 4. Leaf Faces (Lump 5)
Index array mapping leaf entries to actual faces. The renderer collects all faces visible from the current leaf via this list + the PVS.

### 5. Leaf Brushes (Lump 6)
Same idea for collision brushes — not needed for pure rendering.

### 6. Faces / Surfaces (Lump 13) — most important
Each face is 104 bytes and has a **type**:

| Type | Value | Description |
|------|-------|-------------|
| Polygon | 1 | Flat mesh, indexed triangles |
| Patch | 2 | Biquadratic Bezier control-point mesh |
| Mesh | 3 | Pre-triangulated mesh |
| Billboard | 4 | Camera-facing sprite (flares etc.) |

Key fields per face:
- `shader` index → which texture/shader to apply
- `lightmap_index` + UV offsets → lightmap atlas coordinates
- `vertex` + `num_verts` → slice into the Vertexes lump
- `meshvert` + `num_meshverts` → index buffer slice (Polygons/Meshes)
- `patch_width` / `patch_height` → control grid size (Patches only)

### 7. Vertexes (Lump 10)
Each vertex (44 bytes) contains:
- `position` — `float[3]`
- `texcoord[2]` — surface UV + lightmap UV (separate pairs)
- `normal` — `float[3]`
- `color` — `byte[4]` RGBA vertex color

### 8. Mesh Verts (Lump 11)
A flat array of `int32` index offsets, relative to a face's base vertex. Used to build the triangle index buffer for polygon and mesh faces.

### 9. Lightmaps (Lump 14)
128×128 RGB textures (49152 bytes each), baked lighting. Each face's lightmap UVs index into one of these. Essential for correct visual output — Q3 levels look wrong without them.

### 10. Visibility / PVS (Lump 16)
Bit-vector table: for each BSP leaf, which other leaves are potentially visible. Allows the renderer to skip drawing geometry in occluded areas. Structure: `num_clusters`, `bytes_per_cluster`, then the raw bitfield.

---

## Rendering Pipeline Summary

```
Camera position
  → find current BSP leaf (walk nodes using planes)
  → look up cluster from leaf
  → fetch PVS row for that cluster
  → collect all leaves whose cluster bit is set
  → gather their Leaf Faces
  → for each face: bind shader + lightmap, submit vertex/index data
  → Patch faces require tessellation of the Bezier control grid first
```

---

## Patch Tessellation (Type 2)

Control points are arranged in a `patch_width × patch_height` grid (always odd dimensions). Each 3×3 sub-grid defines one biquadratic Bezier patch. Tessellate by evaluating `B(s,t)` at desired resolution and stitching into triangles. This is the most complex rendering path.

---

## What You Can Skip for a Basic Renderer

| Lump | Skip? |
|------|-------|
| Brushes / Brush Sides | Yes (collision only) |
| Effects / Fogs | Yes (optional) |
| Light Grid | Yes (dynamic entity lighting) |
| Models (Lump 7) | Partial — only needed for brush entity sub-models |
| Advertisements | Yes |
