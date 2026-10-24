import json
from pathlib import Path

def load_game_data():
    base_dir = Path(__file__).resolve().parent.parent.parent

    config_path = base_dir / "godot_game" / "config" / "balance.json"
    map_path = base_dir / "godot_game" / "config" / "map_data.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    with open(map_path, 'r', encoding='utf-8') as f:
        map_data = json.load(f)

    return config_data, map_data
