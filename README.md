# BSPParserPythonQ3

A pipeline to convert Quake 3 BSP maps into GLB files for use in [instagib.me](https://instagib.me).

## Setup

Edit `conf.ini` to point at your unpacked Q3 assets and target directory:

```ini
[paths]
texture_dir = C:/Action/id/q3unpacked/textures
base_dir    = C:/Action/id/q3unpacked
target_dir  = C:/path/to/instagib3
```

## Pipeline

Run the steps in order for each map:

| Step | Script | What it does |
|------|--------|--------------|
| 1 | `step1_convert_tga.py` | Convert TGA textures to PNG |
| 2 | `step2_inventory_q3_textures.py` | Build texture inventory into `input/textures.txt` |
| 3 | `step3_bsp_to_output.py` | Parse BSP file and extract geometry/shaders into `output/` |
| 4 | `step4_remove_skiplist.py` | Remove skybox surfaces from `output/surfaces.json` |
| 5 | `step5_map_textures.py` | Remap shader names to textures via `input/texture_map.txt` |
| 6 | `step6_output_to_glb.py` | Pack geometry and textures into a GLB file |
| 7 | `step7_copy_triggers.py` | Copy map output to `target_dir` |

## Requirements

- Quake 3
- Python 3

