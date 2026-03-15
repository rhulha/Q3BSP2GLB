from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Shader:
    shader: str
    surface_flags: int
    content_flags: int
    SIZE = 72


@dataclass
class Plane:
    normal: list[float]
    distance: float
    SIZE = 16


@dataclass
class Node:
    plane_num: int
    children: list[int]
    mins: list[int]
    maxs: list[int]
    SIZE = 36


@dataclass
class Leaf:
    cluster: int
    area: int
    mins: list[int]
    maxs: list[int]
    first_leaf_surface: int
    num_leaf_surfaces: int
    first_leaf_brush: int
    num_leaf_brushes: int
    SIZE = 48


@dataclass
class Model:
    mins: list[float]
    maxs: list[float]
    first_surface: int
    num_surfaces: int
    first_brush: int
    num_brushes: int
    SIZE = 40


@dataclass
class Brush:
    first_side: int
    num_sides: int
    shader_num: int
    SIZE = 12


@dataclass
class BrushSide:
    plane_num: int
    shader_num: int
    SIZE = 8


@dataclass
class Vertex:
    xyz: list[float]
    st: list[float]
    lightmap: list[float]
    normal: list[float]
    color: list[float]
    SIZE = 44


@dataclass
class Fog:
    shader: str
    brush_num: int
    visible_side: int
    SIZE = 72


@dataclass
class Surface:
    shader_num: int
    fog_num: int
    surface_type: int
    first_vert: int
    num_verts: int
    first_index: int
    num_indexes: int
    lightmap_num: int
    lm_start: list[int]
    lm_size: list[int]
    lightmap_origin: list[float]
    lightmap_vecs: list[float]
    patch_size: list[int]
    SIZE = 104


@dataclass
class LightGrid:
    ambient: list[int]
    directional: list[int]
    direction: list[int]
    SIZE = 8
