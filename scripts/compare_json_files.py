import json
import sys
from pathlib import Path
from deepdiff import DeepDiff  # pip install deepdiff

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python compare_json.py fichier1.json fichier2.json")
        sys.exit(1)

    file1 = Path(sys.argv[1])
    file2 = Path(sys.argv[2])

    if not file1.exists() or not file2.exists():
        print("❌ Un des fichiers n'existe pas.")
        sys.exit(1)

    j1 = load_json(file1)
    j2 = load_json(file2)

    diff = DeepDiff(j1, j2, ignore_order=True)

    if not diff:
        print("✔️ Les deux fichiers JSON sont identiques.")
    else:
        print("❌ Les fichiers sont différents :")
        print(diff)
