"""
Seasonal maps for CrossRiver - precisely traced from sketch images.
Game resolution: 1250×650
Each map defines obstacle rectangles that create the river path.
Assets are placed as decoration within the river and on obstacle areas.

20 maps across 4 seasons (5 levels per season):
- FOREST: Closing Door, Muddy Zigzag, Rock Horseshoe, Cloud Cover, Dense Forest
- SNOW: The Freeze, Ice Block Alley, Ice Field, Frozen S-Curve, Wind Corridor
- DESERT: Sandy S-Curve, Cactus Zigzag, Rock Hairpin, Sandstorm Run, Scorpion Slalom
- TROPICS: Foggy River, Vine Corridor, Mud Bend, Jungle S, Dark Swamp
"""

# ============================================================================
# FOREST THEME - Ancient trees and muddy waters
# ============================================================================

FOREST_CLOSING_DOOR = {
    "name": "Forest - Closing Door",
    "theme": "forest",
    "level": 1,
    "season": "forest",
    "time_limit": 60,
    "description": "Navigate an L-shaped river. Watch the closing door mechanic at the exit!",

    # Traced from sketch: L-shaped river flowing up then right, large mass on right/bottom
    "obstacles": [
        # Left wall (continuous narrow strip)
        (0, 0, 100, 500),
        # Bottom-right wall (wide area, leaving spawn gap at bottom-center)
        (700, 520, 550, 130),
        # Right wall at top (the closing door area)
        (1100, 0, 150, 300),
        # Interior obstacles creating current effect
        (150, 100, 120, 100),
        (200, 250, 100, 90),
        (350, 350, 110, 120),
        (600, 200, 130, 110),
        (800, 380, 150, 100),
        (0, 520, 200, 130),
    ],
    "assets": [
        {"file": "props/Pixel_art_forest_202603281320.png", "x": 50, "y": 150, "scale": 0.15, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_3.png", "x": 50, "y": 350, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_10.png", "x": 50, "y": 500, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_2.png", "x": 1100, "y": 50, "scale": 0.15, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_3.png", "x": 1100, "y": 150, "scale": 0.12, "z_order": 1},
        {"file": "decor/Pixel_art_fallen_202603281320.png", "x": 150, "y": 550, "scale": 0.2, "z_order": 2},
        {"file": "decor/Pixel_art_fallen_202603281320.png", "x": 500, "y": 550, "scale": 0.2, "z_order": 2},
        {"file": "decor/Pixel_art_fallen_202603281320.png", "x": 900, "y": 550, "scale": 0.2, "z_order": 2},
        {"file": "decor/Pixel_art_moss_202603281320.png", "x": 200, "y": 400, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_mushroom_202603281320.png", "x": 600, "y": 450, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_grass_202603281320.png", "x": 800, "y": 350, "scale": 0.08, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 100,
    "finish_x2": 1100,
    "mechanics": {"closing_door": True, "difficulty": 1},
}

FOREST_MUDDY_ZIGZAG = {
    "name": "Forest - Muddy Zigzag",
    "theme": "forest",
    "level": 2,
    "season": "forest",
    "time_limit": 55,
    "description": "Zigzag through muddy patches. Mud slows your boat significantly!",

    # Traced: Zigzag pattern with mud obstacles in the water
    "obstacles": [
        # Top left wall
        (0, 0, 150, 200),
        # Top right wall
        (900, 0, 350, 150),
        # First zigzag - left jut
        (0, 150, 250, 200),
        # First zigzag - right jut
        (700, 150, 550, 150),
        # Second zigzag - left jut
        (150, 350, 280, 150),
        # Second zigzag - right jut
        (600, 350, 650, 150),
        # Bottom section walls
        (0, 500, 200, 150),
        (1000, 500, 250, 150),
        # Mud patches in water (circular obstacles as rectangles)
        (350, 100, 110, 90),
        (600, 250, 100, 100),
        (300, 400, 120, 100),
        (800, 400, 110, 90),
        (450, 550, 130, 80),
    ],
    "assets": [
        {"file": "props/Pixel_art_forest_202603281320_3.png", "x": 50, "y": 80, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_9.png", "x": 50, "y": 200, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320.png", "x": 950, "y": 50, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_10.png", "x": 1050, "y": 80, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 350, "y": 120, "scale": 0.18, "z_order": 2},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 600, "y": 280, "scale": 0.18, "z_order": 2},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 300, "y": 430, "scale": 0.18, "z_order": 2},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 800, "y": 430, "scale": 0.18, "z_order": 2},
        {"file": "decor/Pixel_art_dirt_202603281320.png", "x": 700, "y": 200, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_grass_202603281320.png", "x": 900, "y": 350, "scale": 0.09, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 150,
    "finish_x2": 900,
    "mechanics": {"mud_patches": True, "difficulty": 2},
}

FOREST_ROCK_HORSESHOE = {
    "name": "Forest - Rock Horseshoe",
    "theme": "forest",
    "level": 3,
    "season": "forest",
    "time_limit": 50,
    "description": "Navigate a wide horseshoe/U-turn. Gray rocks scatter the waterway!",

    # Traced: U-turn river flowing right then back left
    "obstacles": [
        # Top left wall
        (0, 0, 180, 250),
        # Top right wall (enters from right side)
        (950, 0, 300, 200),
        # Inner curve right wall
        (900, 200, 350, 200),
        # Inner curve left wall
        (150, 250, 250, 200),
        # Bottom left wall
        (0, 450, 200, 200),
        # Bottom right opening
        (1050, 450, 200, 200),
        # Rock obstacles scattered throughout
        (300, 50, 120, 110),
        (700, 100, 130, 120),
        (200, 200, 110, 100),
        (800, 300, 120, 110),
        (400, 400, 130, 100),
        (550, 520, 120, 80),
        (300, 530, 100, 70),
    ],
    "assets": [
        {"file": "obstacles/Pixel_art_rock_202603281320.png", "x": 50, "y": 100, "scale": 0.14, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_2.png", "x": 950, "y": 80, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 900, "y": 280, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_3.png", "x": 150, "y": 350, "scale": 0.14, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_3.png", "x": 50, "y": 480, "scale": 0.11, "z_order": 1},
        {"file": "decor/Pixel_art_moss_202603281320.png", "x": 400, "y": 80, "scale": 0.11, "z_order": 1},
        {"file": "decor/Pixel_art_moss_202603281320.png", "x": 750, "y": 150, "scale": 0.11, "z_order": 1},
        {"file": "decor/Pixel_art_moss_202603281320.png", "x": 250, "y": 250, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_moss_202603281320.png", "x": 850, "y": 350, "scale": 0.1, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 180,
    "finish_x2": 950,
    "mechanics": {"rocky_obstacles": True, "difficulty": 3},
}

FOREST_CLOUD_COVER = {
    "name": "Forest - Cloud Cover",
    "theme": "forest",
    "level": 4,
    "season": "forest",
    "time_limit": 45,
    "description": "Heavy clouds reduce visibility. Navigate by memory and compass!",

    # Traced: U-shaped/spiral with center path
    "obstacles": [
        # Left wall
        (0, 0, 220, 650),
        # Right wall
        (1000, 0, 250, 650),
        # Center divider (island in middle)
        (400, 150, 450, 200),
        # Scattered obstacles
        (250, 50, 130, 110),
        (700, 80, 140, 100),
        (300, 300, 120, 100),
        (750, 280, 130, 110),
        (350, 450, 140, 120),
        (750, 500, 130, 100),
        (450, 580, 120, 60),
    ],
    "assets": [
        {"file": "props/Pixel_art_forest_202603281320.png", "x": 80, "y": 150, "scale": 0.14, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_10.png", "x": 80, "y": 400, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_3.png", "x": 1050, "y": 200, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_9.png", "x": 1050, "y": 450, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_2.png", "x": 400, "y": 230, "scale": 0.13, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_3.png", "x": 550, "y": 210, "scale": 0.11, "z_order": 1},
        {"file": "decor/Pixel_art_hanging_202603281320.png", "x": 300, "y": 50, "scale": 0.15, "z_order": 3},
        {"file": "decor/Pixel_art_hanging_202603281320.png", "x": 750, "y": 80, "scale": 0.15, "z_order": 3},
        {"file": "decor/Pixel_art_hanging_202603281320.png", "x": 400, "y": 300, "scale": 0.15, "z_order": 3},
    ],
    "finish_y": 50,
    "finish_x1": 220,
    "finish_x2": 1000,
    "mechanics": {"fog": True, "reduced_visibility": True, "difficulty": 4},
}

FOREST_DENSE_FOREST = {
    "name": "Forest - Dense Forest",
    "theme": "forest",
    "level": 5,
    "season": "forest",
    "time_limit": 40,
    "description": "The densest forest. Narrow winding passages through thick obstacles!",

    # Traced: Very narrow winding with tight turns (min 130px gaps)
    "obstacles": [
        # Left wall
        (0, 0, 180, 650),
        # Right wall
        (1000, 0, 250, 650),
        # First tight turn - left jut
        (180, 80, 200, 150),
        # First turn - right jut
        (750, 60, 250, 120),
        # Second turn - left jut
        (220, 260, 200, 120),
        # Second turn - right jut
        (720, 250, 280, 120),
        # Third turn - left jut
        (180, 420, 220, 130),
        # Third turn - right jut
        (800, 410, 200, 140),
        # Dense interior obstacles (placed in wider sections)
        (480, 80, 100, 80),
        (380, 180, 100, 70),
        (550, 300, 100, 80),
        (400, 400, 100, 70),
        (650, 480, 100, 80),
        (480, 570, 100, 60),
    ],
    "assets": [
        {"file": "props/Pixel_art_forest_202603281320.png", "x": 50, "y": 100, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_10.png", "x": 50, "y": 300, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_3.png", "x": 50, "y": 500, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320.png", "x": 1000, "y": 150, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_9.png", "x": 1000, "y": 380, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_forest_202603281320_10.png", "x": 1000, "y": 550, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_2.png", "x": 280, "y": 120, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_3.png", "x": 850, "y": 100, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 350, "y": 320, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 850, "y": 320, "scale": 0.1, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 200,
    "finish_x2": 950,
    "mechanics": {"narrow_passages": True, "difficulty": 5},
}

# ============================================================================
# SNOW THEME - Frozen rivers with slippery ice
# ============================================================================

SNOW_THE_FREEZE = {
    "name": "Snow - The Freeze",
    "theme": "snow",
    "level": 1,
    "season": "snow",
    "time_limit": 55,
    "description": "S-curve frozen river. Icy water means zero friction - slide carefully!",

    # Traced: S-curve from bottom-left to top
    "obstacles": [
        # Bottom left wall
        (0, 450, 280, 200),
        # First curve - right wall
        (800, 350, 450, 200),
        # Second curve - left wall
        (150, 100, 350, 250),
        # Top right wall
        (950, 0, 300, 150),
        # Center obstacles
        (300, 200, 130, 110),
        (650, 350, 140, 120),
        (450, 500, 130, 100),
    ],
    "assets": [
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 50, "y": 480, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_2.png", "x": 50, "y": 520, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 950, "y": 50, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/snow_asset_1.png", "x": 850, "y": 400, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 200, "y": 120, "scale": 0.11, "z_order": 1},
        {"file": "decor/Pixel_art_icicle_202603281320.png", "x": 50, "y": 100, "scale": 0.08, "z_order": 2},
        {"file": "decor/Pixel_art_frost_202603281320.png", "x": 950, "y": 200, "scale": 0.08, "z_order": 2},
        {"file": "decor/Pixel_art_snowflake_202603281320.png", "x": 400, "y": 250, "scale": 0.08, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 150,
    "finish_x2": 950,
    "mechanics": {"ice_friction": True, "zero_friction": True, "difficulty": 1},
}

SNOW_ICE_BLOCK_ALLEY = {
    "name": "Snow - Ice Block Alley",
    "theme": "snow",
    "level": 2,
    "season": "snow",
    "time_limit": 50,
    "description": "S-curve with ice block obstacles. Navigate between frozen formations!",

    # Traced: S-curve with scattered ice blocks (pentagons as rectangles)
    "obstacles": [
        # Side walls narrower
        (0, 0, 110, 650),
        (1140, 0, 110, 650),
        # First curve jut left
        (110, 100, 200, 150),
        # First curve jut right
        (800, 100, 340, 150),
        # Second curve jut left
        (200, 350, 220, 150),
        # Second curve jut right
        (850, 300, 290, 150),
        # Ice blocks scattered
        (250, 50, 110, 100),
        (600, 80, 120, 110),
        (400, 200, 115, 100),
        (750, 240, 130, 110),
        (300, 380, 120, 100),
        (700, 420, 125, 120),
        (450, 530, 120, 70),
    ],
    "assets": [
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 50, "y": 150, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_3.png", "x": 50, "y": 350, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_2.png", "x": 50, "y": 550, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 1180, "y": 200, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_3.png", "x": 1180, "y": 450, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 280, "y": 80, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 650, "y": 120, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 380, "y": 250, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 750, "y": 290, "scale": 0.1, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 110,
    "finish_x2": 1140,
    "mechanics": {"ice_friction": True, "difficulty": 2},
}

SNOW_ICE_FIELD = {
    "name": "Snow - Ice Field",
    "theme": "snow",
    "level": 3,
    "season": "snow",
    "time_limit": 48,
    "description": "Wide open frozen area. Large ice blocks scattered everywhere!",

    # Traced: Open frozen water with scattered hexagon/pentagon obstacles
    "obstacles": [
        # Minimal side walls
        (0, 0, 80, 650),
        (1170, 0, 80, 650),
        # Large ice blocks scattered throughout
        (200, 50, 150, 140),
        (600, 80, 160, 150),
        (900, 100, 140, 130),
        (300, 250, 170, 160),
        (750, 220, 180, 170),
        (450, 350, 160, 150),
        (850, 380, 150, 140),
        (200, 450, 140, 150),
        (650, 500, 170, 160),
        (350, 550, 150, 90),
        (1000, 550, 140, 90),
    ],
    "assets": [
        {"file": "props/Pixel_art_snow_202603281320_3.png", "x": 50, "y": 100, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 50, "y": 350, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_2.png", "x": 50, "y": 550, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_3.png", "x": 1190, "y": 250, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 230, "y": 90, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 650, "y": 120, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 950, "y": 140, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 350, "y": 290, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 800, "y": 270, "scale": 0.12, "z_order": 1},
        {"file": "decor/Pixel_art_frosted_202603281320.png", "x": 450, "y": 380, "scale": 0.09, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 80,
    "finish_x2": 1170,
    "mechanics": {"ice_friction": True, "open_field": True, "difficulty": 3},
}

SNOW_FROZEN_S_CURVE = {
    "name": "Snow - Frozen S-Curve",
    "theme": "snow",
    "level": 4,
    "season": "snow",
    "time_limit": 45,
    "description": "Tight S-curve with wind gusts and frozen water. Hardest ice challenge!",

    # Traced: Tighter S-curve with central island and wind effects
    "obstacles": [
        # Side walls
        (0, 0, 130, 650),
        (1120, 0, 130, 650),
        # Top jut right
        (800, 0, 320, 180),
        # Middle island (central channel divider)
        (350, 250, 500, 180),
        # Bottom jut left
        (130, 470, 280, 180),
        # Scattered obstacles
        (200, 80, 120, 100),
        (650, 150, 130, 110),
        (400, 300, 140, 100),
        (750, 380, 150, 120),
        (300, 500, 130, 100),
        (950, 500, 120, 100),
    ],
    "assets": [
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 80, "y": 100, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_2.png", "x": 80, "y": 350, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_3.png", "x": 80, "y": 550, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 1160, "y": 150, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_3.png", "x": 1160, "y": 450, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/snow_asset_1.png", "x": 400, "y": 300, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/snow_asset_2.png", "x": 550, "y": 320, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_icicle_202603281320.png", "x": 800, "y": 80, "scale": 0.09, "z_order": 2},
        {"file": "decor/Pixel_art_icicle_202603281320.png", "x": 200, "y": 450, "scale": 0.08, "z_order": 2},
    ],
    "finish_y": 50,
    "finish_x1": 130,
    "finish_x2": 1120,
    "mechanics": {"ice_friction": True, "wind": True, "difficulty": 4},
}

SNOW_WIND_CORRIDOR = {
    "name": "Snow - Wind Corridor",
    "theme": "snow",
    "level": 5,
    "season": "snow",
    "time_limit": 40,
    "description": "Extreme conditions! Narrow zigzag with random wind gusts!",

    # Traced: Very narrow zigzag with strong lateral wind effects
    "obstacles": [
        # Left wall narrow
        (0, 0, 180, 650),
        # Right wall narrow
        (1070, 0, 180, 650),
        # First zigzag left
        (180, 100, 280, 160),
        # First zigzag right
        (850, 100, 220, 160),
        # Second zigzag left
        (250, 300, 250, 150),
        # Second zigzag right
        (900, 280, 170, 170),
        # Third zigzag left
        (200, 480, 270, 150),
        # Third zigzag right
        (950, 480, 120, 170),
        # Scattered obstacles
        (500, 150, 120, 100),
        (550, 350, 130, 110),
        (450, 550, 140, 90),
    ],
    "assets": [
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 80, "y": 150, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_3.png", "x": 80, "y": 400, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_2.png", "x": 80, "y": 550, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320.png", "x": 1110, "y": 250, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_snow_202603281320_3.png", "x": 1110, "y": 550, "scale": 0.12, "z_order": 1},
        {"file": "decor/Pixel_art_icicle_202603281320.png", "x": 300, "y": 120, "scale": 0.08, "z_order": 2},
        {"file": "decor/Pixel_art_icicle_202603281320.png", "x": 900, "y": 320, "scale": 0.08, "z_order": 2},
        {"file": "decor/Pixel_art_icicle_202603281320.png", "x": 350, "y": 500, "scale": 0.08, "z_order": 2},
    ],
    "finish_y": 50,
    "finish_x1": 180,
    "finish_x2": 1070,
    "mechanics": {"ice_friction": True, "wind": True, "narrow_passages": True, "difficulty": 5},
}

# ============================================================================
# DESERT THEME - Sandy dunes with quicksand
# ============================================================================

DESERT_SANDY_S_CURVE = {
    "name": "Desert - Sandy S-Curve",
    "theme": "desert",
    "level": 1,
    "season": "desert",
    "time_limit": 60,
    "description": "Navigate sand dunes forming an S-curve. Quicksand slows you down!",

    # Traced: S-curve between sand dunes with quicksand patches
    "obstacles": [
        # Top left dune
        (0, 0, 300, 200),
        # Top right dune
        (850, 0, 400, 220),
        # Middle left dune
        (50, 250, 350, 200),
        # Middle right dune
        (700, 200, 550, 200),
        # Bottom left dune
        (0, 450, 250, 200),
        # Bottom right dune
        (950, 400, 300, 250),
        # Quicksand obstacles
        (350, 80, 130, 120),
        (600, 250, 140, 130),
        (250, 350, 120, 110),
        (800, 500, 130, 100),
    ],
    "assets": [
        {"file": "props/Pixel_art_desert_202603281320_2.png", "x": 100, "y": 50, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_5.png", "x": 900, "y": 50, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_6.png", "x": 150, "y": 320, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_2.png", "x": 800, "y": 280, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_5.png", "x": 50, "y": 480, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_6.png", "x": 1000, "y": 450, "scale": 0.11, "z_order": 1},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 400, "y": 120, "scale": 0.18, "z_order": 2},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 650, "y": 280, "scale": 0.18, "z_order": 2},
        {"file": "decor/Pixel_art_dirt_202603281320.png", "x": 250, "y": 370, "scale": 0.1, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 300,
    "finish_x2": 850,
    "mechanics": {"quicksand": True, "difficulty": 1},
}

DESERT_CACTUS_ZIGZAG = {
    "name": "Desert - Cactus Zigzag",
    "theme": "desert",
    "level": 2,
    "season": "desert",
    "time_limit": 55,
    "description": "Right-angle zigzag path. Cactus obstacles at each turn!",

    # Traced: Right-angle zigzag with cactus obstacles
    "obstacles": [
        # Side walls minimal
        (0, 0, 100, 650),
        (1150, 0, 100, 650),
        # First zigzag left
        (100, 100, 300, 180),
        # First zigzag right
        (750, 100, 400, 180),
        # Second zigzag left
        (200, 320, 280, 160),
        # Second zigzag right
        (800, 300, 350, 170),
        # Third zigzag left
        (150, 510, 300, 140),
        # Cactus obstacles at turns
        (250, 120, 110, 130),
        (900, 140, 120, 140),
        (350, 350, 130, 120),
        (850, 360, 120, 130),
        (300, 530, 120, 110),
        (1000, 520, 130, 130),
    ],
    "assets": [
        {"file": "props/Pixel_art_desert_202603281320_2.png", "x": 50, "y": 120, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_5.png", "x": 50, "y": 300, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_2.png", "x": 50, "y": 530, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_6.png", "x": 1180, "y": 150, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_5.png", "x": 1180, "y": 380, "scale": 0.11, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_2.png", "x": 1180, "y": 560, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 280, "y": 150, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 900, "y": 180, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 380, "y": 370, "scale": 0.1, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 100,
    "finish_x2": 1150,
    "mechanics": {"quicksand": True, "difficulty": 2},
}

DESERT_ROCK_HAIRPIN = {
    "name": "Desert - Rock Hairpin",
    "theme": "desert",
    "level": 3,
    "season": "desert",
    "time_limit": 50,
    "description": "Tight hairpin turn through canyon. Boulders block narrow passages!",

    # Traced: Hairpin turn canyon with boulder obstacles
    "obstacles": [
        # Left canyon wall
        (0, 0, 300, 250),
        # Right canyon wall (top)
        (800, 0, 450, 200),
        # Hairpin curve left wall
        (0, 300, 400, 150),
        # Hairpin curve right wall
        (600, 280, 650, 150),
        # Bottom walls (leave center open for spawn)
        (0, 520, 250, 130),
        (900, 520, 350, 130),
        # Boulder obstacles throughout
        (200, 80, 120, 100),
        (850, 60, 120, 100),
        (250, 310, 120, 100),
        (500, 460, 100, 80),
    ],
    "assets": [
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 100, "y": 100, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_2.png", "x": 850, "y": 80, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_3.png", "x": 0, "y": 340, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/Pixel_art_rock_202603281320_3.png", "x": 600, "y": 320, "scale": 0.1, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_2.png", "x": 100, "y": 330, "scale": 0.1, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_6.png", "x": 900, "y": 350, "scale": 0.09, "z_order": 1},
        {"file": "decor/Pixel_art_dirt_202603281320.png", "x": 450, "y": 500, "scale": 0.1, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 320,
    "finish_x2": 800,
    "mechanics": {"difficulty": 3},
}

DESERT_SANDSTORM_RUN = {
    "name": "Desert - Sandstorm Run",
    "theme": "desert",
    "level": 4,
    "season": "desert",
    "time_limit": 45,
    "description": "Raging sandstorm reduces visibility. Navigate the L-shaped river!",

    # Traced: L-shaped river with large dune walls and fog
    "obstacles": [
        # Top wall (wide dune)
        (0, 0, 420, 200),
        # Right wall (wide dune)
        (780, 200, 470, 450),
        # Left wall (bottom)
        (0, 400, 280, 250),
        # Interior obstacles
        (300, 50, 130, 120),
        (620, 100, 130, 110),
        (350, 250, 140, 120),
        (400, 420, 120, 100),
        (600, 500, 120, 90),
    ],
    "assets": [
        {"file": "props/Pixel_art_desert_202603281320_3.png", "x": 150, "y": 50, "scale": 0.25, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_3.png", "x": 800, "y": 300, "scale": 0.25, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_5.png", "x": 100, "y": 420, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_6.png", "x": 200, "y": 500, "scale": 0.11, "z_order": 1},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 400, "y": 80, "scale": 0.2, "z_order": 2},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 700, "y": 140, "scale": 0.2, "z_order": 2},
    ],
    "finish_y": 50,
    "finish_x1": 450,
    "finish_x2": 750,
    "mechanics": {"fog": True, "reduced_visibility": True, "difficulty": 4},
}

DESERT_SCORPION_SLALOM = {
    "name": "Desert - Scorpion Slalom",
    "theme": "desert",
    "level": 5,
    "season": "desert",
    "time_limit": 40,
    "description": "Extreme slalom course. Tight alternating turns through scorpion-infested canyon!",

    # Traced: Tight zigzag slalom with minimal river width
    "obstacles": [
        # Left wall
        (0, 0, 180, 650),
        # Right wall
        (1070, 0, 180, 650),
        # Zigzag pattern - tight alternating turns
        (180, 80, 250, 140),
        (800, 80, 270, 140),
        (220, 240, 280, 130),
        (850, 240, 220, 140),
        (200, 390, 270, 140),
        (900, 380, 170, 150),
        (240, 540, 260, 110),
        (950, 520, 120, 130),
        # Hazard obstacles (scorpion-themed)
        (450, 120, 100, 90),
        (500, 280, 110, 100),
        (480, 430, 100, 100),
        (700, 570, 90, 60),
    ],
    "assets": [
        {"file": "props/Pixel_art_desert_202603281320_2.png", "x": 80, "y": 150, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_5.png", "x": 80, "y": 400, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_2.png", "x": 80, "y": 560, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_6.png", "x": 1100, "y": 250, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_desert_202603281320_5.png", "x": 1100, "y": 520, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 320, "y": 100, "scale": 0.09, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 900, "y": 110, "scale": 0.09, "z_order": 1},
        {"file": "obstacles/Pixel_art_boulder_202603281320_2.png", "x": 350, "y": 270, "scale": 0.09, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 180,
    "finish_x2": 1070,
    "mechanics": {"narrow_passages": True, "difficulty": 5},
}

# ============================================================================
# TROPICS THEME - Dense jungle with narrow corridors
# ============================================================================

TROPICS_FOGGY_RIVER = {
    "name": "Tropics - Foggy River",
    "theme": "tropics",
    "level": 1,
    "season": "tropics",
    "time_limit": 65,
    "description": "Wide winding river. Heavy fog makes navigation challenging!",

    # Traced: Wide horizontal winding path with fog
    "obstacles": [
        # Left wall
        (0, 0, 200, 650),
        # Right wall
        (1050, 0, 200, 650),
        # Gentle curves
        (250, 100, 280, 180),
        (850, 200, 300, 180),
        (200, 350, 300, 150),
        (900, 400, 250, 150),
        (300, 550, 280, 100),
        # Interior obstacles
        (450, 120, 130, 110),
        (700, 300, 140, 120),
        (500, 450, 150, 100),
    ],
    "assets": [
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 80, "y": 150, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 80, "y": 400, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_palm_202603281320.png", "x": 1070, "y": 200, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_palm_202603281320.png", "x": 1070, "y": 500, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/tropics_asset_1.png", "x": 350, "y": 150, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/tropics_asset_2.png", "x": 850, "y": 250, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_tropical_202603281320.png", "x": 200, "y": 80, "scale": 0.1, "z_order": 2},
        {"file": "decor/Pixel_art_flowering_202603281320.png", "x": 1000, "y": 450, "scale": 0.1, "z_order": 2},
    ],
    "finish_y": 50,
    "finish_x1": 200,
    "finish_x2": 1050,
    "mechanics": {"fog": True, "reduced_visibility": True, "difficulty": 1},
}

TROPICS_VINE_CORRIDOR = {
    "name": "Tropics - Vine Corridor",
    "theme": "tropics",
    "level": 2,
    "season": "tropics",
    "time_limit": 60,
    "description": "Narrow vertical river. Hanging vines and branch obstacles!",

    # Traced: Narrow vertical path with slight curves and vine obstacles
    "obstacles": [
        # Side walls narrow
        (0, 0, 220, 650),
        (1030, 0, 220, 650),
        # Slight curves
        (220, 100, 200, 150),
        (800, 100, 230, 150),
        (270, 300, 220, 160),
        (850, 280, 180, 170),
        (200, 480, 250, 170),
        (900, 460, 130, 170),
        # Interior obstacles
        (450, 150, 140, 120),
        (500, 320, 130, 110),
        (450, 520, 150, 100),
    ],
    "assets": [
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 100, "y": 150, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 100, "y": 400, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_palm_202603281320.png", "x": 1050, "y": 250, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/tropics_asset_2.png", "x": 350, "y": 150, "scale": 0.11, "z_order": 1},
        {"file": "obstacles/tropics_asset_2.png", "x": 850, "y": 350, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_hanging_202603281320.png", "x": 250, "y": 120, "scale": 0.15, "z_order": 3},
        {"file": "decor/Pixel_art_hanging_202603281320.png", "x": 900, "y": 330, "scale": 0.15, "z_order": 3},
        {"file": "decor/Pixel_art_tropical_202603281320.png", "x": 500, "y": 200, "scale": 0.09, "z_order": 1},
    ],
    "finish_y": 50,
    "finish_x1": 220,
    "finish_x2": 1030,
    "mechanics": {"narrow_passages": True, "difficulty": 2},
}

TROPICS_MUD_BEND = {
    "name": "Tropics - Mud Bend",
    "theme": "tropics",
    "level": 3,
    "season": "tropics",
    "time_limit": 55,
    "description": "Large U-curve river. Heavy fog and muddy patches slow progress!",

    # Traced: U-curve bend with mud patches and low visibility
    "obstacles": [
        # Left wall
        (0, 0, 250, 650),
        # Right wall
        (950, 0, 300, 650),
        # Curve left
        (250, 100, 280, 200),
        # Curve right
        (750, 100, 200, 250),
        # Bottom curves
        (150, 450, 320, 200),
        (900, 400, 50, 250),
        # Mud patches
        (350, 150, 140, 120),
        (700, 200, 130, 110),
        (300, 350, 150, 130),
        (800, 350, 140, 120),
        (400, 500, 130, 100),
    ],
    "assets": [
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 100, "y": 200, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 100, "y": 480, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_palm_202603281320.png", "x": 1000, "y": 250, "scale": 0.13, "z_order": 1},
        {"file": "obstacles/tropics_asset_1.png", "x": 350, "y": 200, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/tropics_asset_2.png", "x": 700, "y": 250, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 400, "y": 180, "scale": 0.18, "z_order": 2},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 350, "y": 380, "scale": 0.18, "z_order": 2},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 700, "y": 450, "scale": 0.18, "z_order": 2},
    ],
    "finish_y": 50,
    "finish_x1": 250,
    "finish_x2": 950,
    "mechanics": {"mud_patches": True, "fog": True, "difficulty": 3},
}

TROPICS_JUNGLE_S = {
    "name": "Tropics - Jungle S",
    "theme": "tropics",
    "level": 4,
    "season": "tropics",
    "time_limit": 50,
    "description": "S-curve through dense jungle. Light fog with mud and branches!",

    # Traced: S-curve with jungle obstacles
    "obstacles": [
        # Side walls
        (0, 0, 140, 650),
        (1110, 0, 140, 650),
        # Top curve jut right
        (750, 0, 360, 200),
        # Middle curve jut left
        (140, 250, 350, 150),
        # Bottom curve jut right
        (900, 450, 210, 200),
        # Interior obstacles
        (200, 100, 140, 130),
        (850, 120, 140, 120),
        (300, 280, 150, 140),
        (700, 320, 160, 120),
        (450, 480, 140, 130),
        (850, 520, 130, 100),
    ],
    "assets": [
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 70, "y": 150, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 70, "y": 420, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_palm_202603281320.png", "x": 1140, "y": 300, "scale": 0.12, "z_order": 1},
        {"file": "obstacles/tropics_asset_2.png", "x": 250, "y": 140, "scale": 0.1, "z_order": 1},
        {"file": "obstacles/tropics_asset_2.png", "x": 750, "y": 360, "scale": 0.1, "z_order": 1},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 300, "y": 130, "scale": 0.16, "z_order": 2},
        {"file": "decor/Pixel_art_mud_202603281320.png", "x": 700, "y": 360, "scale": 0.16, "z_order": 2},
    ],
    "finish_y": 50,
    "finish_x1": 140,
    "finish_x2": 1110,
    "mechanics": {"mud_patches": True, "difficulty": 4},
}

TROPICS_DARK_SWAMP = {
    "name": "Tropics - Dark Swamp",
    "theme": "tropics",
    "level": 5,
    "season": "tropics",
    "time_limit": 40,
    "description": "Nearly zero visibility! Fireflies light the way through pitch-black swamp!",

    # Traced: Very narrow winding through dark swamp - hardest level
    "obstacles": [
        # Narrow walls
        (0, 0, 200, 650),
        (1050, 0, 200, 650),
        # Tight winding turns
        (200, 80, 300, 180),
        (900, 80, 150, 180),
        (250, 280, 280, 170),
        (850, 260, 200, 190),
        (200, 470, 320, 180),
        (950, 450, 100, 200),
        # Dense interior obstacles
        (500, 120, 130, 110),
        (450, 310, 140, 130),
        (550, 480, 120, 120),
        (450, 600, 140, 50),
    ],
    "assets": [
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 80, "y": 150, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 80, "y": 400, "scale": 0.13, "z_order": 1},
        {"file": "props/Pixel_art_jungle_202603281320.png", "x": 80, "y": 550, "scale": 0.12, "z_order": 1},
        {"file": "props/Pixel_art_palm_202603281320.png", "x": 1080, "y": 250, "scale": 0.13, "z_order": 1},
        {"file": "obstacles/tropics_asset_1.png", "x": 300, "y": 150, "scale": 0.09, "z_order": 1},
        {"file": "obstacles/tropics_asset_2.png", "x": 900, "y": 320, "scale": 0.09, "z_order": 1},
        {"file": "obstacles/tropics_asset_1.png", "x": 350, "y": 480, "scale": 0.08, "z_order": 1},
        {"file": "lighting/Pixel_art_glow_202603281320.png", "x": 500, "y": 150, "scale": 0.08, "z_order": 4},
        {"file": "lighting/Pixel_art_glow_202603281320.png", "x": 550, "y": 340, "scale": 0.08, "z_order": 4},
        {"file": "lighting/Pixel_art_glow_202603281320.png", "x": 480, "y": 550, "scale": 0.08, "z_order": 4},
    ],
    "finish_y": 50,
    "finish_x1": 200,
    "finish_x2": 1050,
    "mechanics": {"fog": True, "near_zero_visibility": True, "narrow_passages": True, "difficulty": 5},
}

# ============================================================================
# Collections and helper functions
# ============================================================================

ALL_MAPS = [
    # Forest
    FOREST_CLOSING_DOOR,
    FOREST_MUDDY_ZIGZAG,
    FOREST_ROCK_HORSESHOE,
    FOREST_CLOUD_COVER,
    FOREST_DENSE_FOREST,
    # Snow
    SNOW_THE_FREEZE,
    SNOW_ICE_BLOCK_ALLEY,
    SNOW_ICE_FIELD,
    SNOW_FROZEN_S_CURVE,
    SNOW_WIND_CORRIDOR,
    # Desert
    DESERT_SANDY_S_CURVE,
    DESERT_CACTUS_ZIGZAG,
    DESERT_ROCK_HAIRPIN,
    DESERT_SANDSTORM_RUN,
    DESERT_SCORPION_SLALOM,
    # Tropics
    TROPICS_FOGGY_RIVER,
    TROPICS_VINE_CORRIDOR,
    TROPICS_MUD_BEND,
    TROPICS_JUNGLE_S,
    TROPICS_DARK_SWAMP,
]

MAPS_BY_SEASON = {
    "forest": [FOREST_CLOSING_DOOR, FOREST_MUDDY_ZIGZAG, FOREST_ROCK_HORSESHOE, FOREST_CLOUD_COVER, FOREST_DENSE_FOREST],
    "snow": [SNOW_THE_FREEZE, SNOW_ICE_BLOCK_ALLEY, SNOW_ICE_FIELD, SNOW_FROZEN_S_CURVE, SNOW_WIND_CORRIDOR],
    "desert": [DESERT_SANDY_S_CURVE, DESERT_CACTUS_ZIGZAG, DESERT_ROCK_HAIRPIN, DESERT_SANDSTORM_RUN, DESERT_SCORPION_SLALOM],
    "tropics": [TROPICS_FOGGY_RIVER, TROPICS_VINE_CORRIDOR, TROPICS_MUD_BEND, TROPICS_JUNGLE_S, TROPICS_DARK_SWAMP],
}

# Backward compatibility: MAPS dict for week2.py (by theme -> level -> map)
MAPS = {
    "forest": {
        1: FOREST_CLOSING_DOOR,
        2: FOREST_MUDDY_ZIGZAG,
        3: FOREST_ROCK_HORSESHOE,
    },
    "snow": {
        1: SNOW_THE_FREEZE,
        2: SNOW_ICE_BLOCK_ALLEY,
        3: SNOW_ICE_FIELD,
    },
    "desert": {
        1: DESERT_SANDY_S_CURVE,
        2: DESERT_CACTUS_ZIGZAG,
        3: DESERT_ROCK_HAIRPIN,
    },
    "tropics": {
        1: TROPICS_FOGGY_RIVER,
        2: TROPICS_VINE_CORRIDOR,
        3: TROPICS_MUD_BEND,
    },
}

def get_map_by_index(index):
    """Get map by 0-based index (0-19)."""
    if 0 <= index < len(ALL_MAPS):
        return ALL_MAPS[index]
    return None

def get_maps_by_season(season):
    """Get all maps for a season."""
    return MAPS_BY_SEASON.get(season, [])

def get_all_maps():
    """Get all 20 maps."""
    return ALL_MAPS

def get_map_count():
    """Get total map count."""
    return len(ALL_MAPS)

def get_map(theme, level):
    """Get map by theme and level (1-based level index).
    For compatibility with week2.py and editor_maps."""
    maps_for_theme = get_maps_by_season(theme)
    if maps_for_theme and level > 0 and level <= len(maps_for_theme):
        return maps_for_theme[level - 1]
    return None
