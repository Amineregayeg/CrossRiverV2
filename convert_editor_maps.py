"""
Convert map editor JSON saves to maps.py format and integrate into the game.
"""

import json
import os
from pathlib import Path

SAVED_MAPS_DIR = Path("/opt/crossriver/saved_maps") if os.path.exists("/opt/crossriver") else Path("saved_maps")


def json_to_map_dict(json_file):
    """Convert editor JSON map to maps.py format."""
    with open(json_file) as f:
        data = json.load(f)

    season = data.get("season", "forest")
    level = data.get("level", 1)
    name = data.get("name", f"{season.upper()} Level {level}")
    time_limit = data.get("time_limit", 60)

    # Extract obstacles from generated_obstacles
    obstacles = []
    for obs in data.get("generated_obstacles", []):
        obstacles.append((obs["x"], obs["y"], obs["w"], obs["h"]))

    # Extract finish line
    finish = data.get("finish", {})
    finish_y = finish.get("pos", 40)
    finish_x1 = finish.get("x1", 0)
    finish_x2 = finish.get("x2", 1250)

    # Extract assets - convert editor format to maps.py semantic types
    assets = []
    for asset in data.get("assets", []):
        src = asset.get("src", "")
        name_key = asset.get("name", "")

        # Map editor asset names to semantic types
        asset_type_map = {
            "grass": "forest_decor",
            "tree": "forest_tree_tall",
            "palm": "tropics_palm",
            "cactus": "desert_cactus_tall",
            "snow": "snow_tree",
        }

        asset_type = asset_type_map.get(name_key, f"{season}_asset")

        assets.append({
            "type": asset_type,
            "x": int(asset.get("x", 0)),
            "y": int(asset.get("y", 0)),
        })

    return {
        "name": name,
        "theme": season,
        "level": level,
        "time_limit": time_limit,
        "description": f"Custom {season.title()} Level {level} from map editor",
        "obstacles": obstacles,
        "assets": assets,
        "finish_y": finish_y,
        "finish_x1": finish_x1,
        "finish_x2": finish_x2,
        "l2_wall_width": 100,
    }


def generate_python_code(map_dict, var_name):
    """Generate Python code for a map."""
    code = f"{var_name} = {{\n"
    code += f'    "name": "{map_dict["name"]}",\n'
    code += f'    "theme": "{map_dict["theme"]}",\n'
    code += f'    "level": {map_dict["level"]},\n'
    code += f'    "time_limit": {map_dict["time_limit"]},\n'
    code += f'    "description": "{map_dict["description"]}",\n'

    code += '    "obstacles": [\n'
    for obs in map_dict["obstacles"]:
        code += f"        {obs},\n"
    code += "    ],\n"

    code += '    "assets": [\n'
    for asset in map_dict["assets"]:
        code += f'        {{"type": "{asset["type"]}", "x": {asset["x"]}, "y": {asset["y"]}}},\n'
    code += "    ],\n"

    code += f'    "finish_y": {map_dict["finish_y"]},\n'
    code += f'    "finish_x1": {map_dict["finish_x1"]},\n'
    code += f'    "finish_x2": {map_dict["finish_x2"]},\n'
    code += f'    "l2_wall_width": {map_dict["l2_wall_width"]},\n'
    code += "}\n\n"

    return code


def main():
    """Convert saved maps and show Python code."""
    print("\n📍 Converting editor maps to Python format...\n")

    if SAVED_MAPS_DIR.exists():
        json_files = sorted(SAVED_MAPS_DIR.glob("*.json"))
    else:
        json_files = sorted(Path(".").glob("saved_maps/*.json"))

    if not json_files:
        print("❌ No saved maps found")
        return

    all_code = ""
    conversions = []

    for json_file in json_files:
        print(f"Converting: {json_file.name}")
        try:
            map_dict = json_to_map_dict(json_file)
            season = map_dict["theme"].upper()
            level = map_dict["level"]
            var_name = f"{season}_LEVEL{level}_EDITOR"

            code = generate_python_code(map_dict, var_name)
            all_code += code

            conversions.append({
                "file": json_file.name,
                "season": season,
                "level": level,
                "var_name": var_name,
                "obstacles": len(map_dict["obstacles"]),
                "assets": len(map_dict["assets"]),
            })
            print(f"  ✅ {var_name} ({len(map_dict['obstacles'])} obstacles, {len(map_dict['assets'])} assets)")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Print summary
    print(f"\n{'='*60}")
    print("CONVERTED MAPS (Add to maps.py):\n")
    print(all_code)

    print(f"{'='*60}")
    print("\nSUMMARY:")
    for conv in conversions:
        print(f"  • {conv['var_name']:30s} ({conv['season']} L{conv['level']}) - {conv['obstacles']} obs, {conv['assets']} assets")

    print(f"\n📝 Total maps converted: {len(conversions)}")
    print("✅ Copy the Python code above and add to maps.py")


if __name__ == "__main__":
    main()
