import json
from pathlib import Path


def load_hole(file_path: Path) -> dict:
    with open(file_path) as f:
        return json.load(f)
