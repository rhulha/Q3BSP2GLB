import os

root = os.path.dirname(os.path.abspath(__file__))
output = os.path.join(root, "textures.txt")

with open(output, "w") as f:
    for dirpath, _, filenames in os.walk(root):
        for filename in sorted(filenames):
            if filename == "inventory.py" or filename == "textures.txt":
                continue
            full = os.path.join(dirpath, filename)
            rel = os.path.relpath(full, root)
            f.write(rel.replace("\\", "/") + "\n")

print(f"Textures inventory written to {output}")
