"""
Editor-created maps - Loaded from saved_maps JSON files.
These are the actual map designs created in the map editor.
"""

import json
from pathlib import Path

SAVED_MAPS_DIR = Path(__file__).parent / "saved_maps"


def load_editor_map_from_json(theme, level):
    """Load actual editor-created map from saved JSON file."""
    # Try different possible filenames
    possible_names = [
        f"{theme}_{level}.json",
        f"{theme}_level{level}.json",
        f"{theme.upper()}_{level}.json",
        f"{theme.upper()}_LEVEL{level}.json",
    ]

    for filename in possible_names:
        filepath = SAVED_MAPS_DIR / filename
        if filepath.exists():
            try:
                with open(filepath) as f:
                    json_data = json.load(f)

                # Convert obstacles explicitly to ensure correct order (x, y, w, h)
                obstacles = []
                for obs in json_data.get("generated_obstacles", []):
                    if isinstance(obs, dict):
                        obstacles.append((obs["x"], obs["y"], obs["w"], obs["h"]))
                    else:
                        obstacles.append(obs)

                # Convert editor JSON format to game format
                map_data = {
                    "name": json_data.get("name", f"{theme.title()} Level {level}"),
                    "theme": json_data.get("season", theme),
                    "level": level,
                    "time_limit": json_data.get("time_limit", 60),
                    "description": f"Editor-designed {theme.title()} Level {level}",
                    "obstacles": obstacles,
                    "assets": json_data.get("assets", []),
                    "start": json_data.get("start", {}),
                    "spawn_point": json_data.get("spawn_point", None),
                    "river_paths": json_data.get("river_paths", []),
                    "poly_obstacles": json_data.get("poly_obstacles", []),
                    "slow_zones": json_data.get("slow_zones", []),
                    "finish": json_data.get("finish", {}),
                    "finish_y": json_data.get("finish", {}).get("pos", 40),
                    "finish_x1": json_data.get("finish", {}).get("x1", 0),
                    "finish_x2": json_data.get("finish", {}).get("x2", 1250),
                    "l2_wall_width": 100,
                }
                print(f"✅ Loaded editor map: {theme}/{level} - {len(obstacles)} obstacles")
                return map_data
            except Exception as e:
                print(f"  ⚠️ Could not load {filepath}: {e}")

    return None


def get_editor_map(theme, level):
    """Get editor-created map for specified theme and level.
    Loads from actual saved JSON files."""
    return load_editor_map_from_json(theme, level)
