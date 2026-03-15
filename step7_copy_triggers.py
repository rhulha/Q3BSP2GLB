import configparser
import shutil
from pathlib import Path

config = configparser.ConfigParser()
config.read('conf.ini')

target_dir = Path(config['paths']['target_dir'])
output_dir = Path('output')

for map_dir in output_dir.iterdir():
    if not map_dir.is_dir():
        continue
    dest = target_dir / map_dir.name
    dest.mkdir(parents=True, exist_ok=True)
    for filename in ('entities.json', 'models.csv'):
        src = map_dir / filename
        if src.exists():
            shutil.copy2(src, dest / filename)
            print(f'copied {src} -> {dest / filename}')
        else:
            print(f'missing {src}')
