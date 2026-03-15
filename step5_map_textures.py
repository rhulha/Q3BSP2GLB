import csv

TEXTURE_MAP = "input/texture_map.txt"
SHADERS_CSV = "output/shaders.csv"

def load_texture_map(path):
    mapping = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            shader, texture = line.split("=", 1)
            mapping[shader.strip()] = texture.strip()
    return mapping

def main():
    mapping = load_texture_map(TEXTURE_MAP)

    with open(SHADERS_CSV, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    replaced = 0
    for row in rows[1:]:
        if row and row[0] in mapping:
            row[0] = mapping[row[0]]
            replaced += 1

    with open(SHADERS_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Replaced {replaced} shader name(s).")

if __name__ == "__main__":
    main()
