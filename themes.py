"""
Theme definitions for CrossRiver game.
Defines obstacle layouts, colors, and assets for each theme/level combination.
Game resolution: 1250×650
"""

# ============================================================================
# FOREST THEME - Levels 1 & 2
# ============================================================================
FOREST_LEVEL1 = {
    "name": "Forest - Level 1",
    "theme": "forest",
    "level": 1,
    "time_limit": 60,
    "description": "Navigate the winding forest river. Watch out for the closing door!",
    "background_color": (34, 139, 34),  # Forest green
    "water_color": (100, 150, 200),      # River blue

    # Obstacle positions: (x, y, width, height) - using coordinate system from sketch
    # Sketch shows a winding path with forest walls on sides
    # Left wall (x=0 to ~150px), right sections vary
    "obstacles": [
        # Left wall - continuous
        (0, 0, 120, 650),
        # Right wall sections
        (1130, 0, 120, 250),
        (1100, 250, 150, 150),
        (900, 350, 350, 50),
        # Middle obstacles
        (300, 200, 100, 80),
        (550, 400, 120, 100),
    ],
    "finish_y": 40,
    "assets": [
        {"type": "forest_asset", "x": 200, "y": 100},
        {"type": "forest_asset", "x": 700, "y": 500},
    ]
}

FOREST_LEVEL2 = {
    "name": "Forest - Level 2",
    "theme": "forest",
    "level": 2,
    "time_limit": 45,
    "description": "Navigate the muddy forest. Obstacles slow you down!",
    "background_color": (34, 139, 34),
    "water_color": (100, 150, 200),

    # More obstacles, closer together
    "obstacles": [
        # Side walls - narrower
        (0, 0, 100, 650),
        (1150, 0, 100, 650),
        # Mud obstacles in water - slow the player
        (400, 150, 120, 100),
        (700, 250, 140, 110),
        (300, 400, 130, 90),
        (850, 500, 150, 80),
    ],
    "finish_y": 40,
    "assets": [
        {"type": "forest_asset", "x": 250, "y": 300},
        {"type": "forest_asset", "x": 800, "y": 200},
        {"type": "forest_asset", "x": 500, "y": 550},
    ]
}

# ============================================================================
# SNOW THEME - Levels 1 & 2
# ============================================================================
SNOW_LEVEL1 = {
    "name": "Snow - Level 1",
    "theme": "snow",
    "level": 1,
    "time_limit": 50,
    "description": "Navigate the icy river. Ice blocks to avoid!",
    "background_color": (200, 230, 255),  # Light blue ice
    "water_color": (150, 200, 255),        # Frozen water

    "obstacles": [
        # Frozen walls - straight sides
        (0, 0, 80, 650),
        (1170, 0, 80, 650),
        # Ice block obstacles
        (350, 150, 100, 100),
        (600, 300, 110, 95),
        (450, 450, 95, 90),
        (800, 550, 120, 80),
    ],
    "finish_y": 40,
    "assets": [
        {"type": "snow_asset", "x": 200, "y": 400},
        {"type": "snow_asset", "x": 950, "y": 250},
    ]
}

SNOW_LEVEL2 = {
    "name": "Snow - Level 2",
    "theme": "snow",
    "level": 2,
    "time_limit": 40,
    "description": "Blizzard conditions! Navigate dangerous ice formations!",
    "background_color": (200, 230, 255),
    "water_color": (150, 200, 255),

    "obstacles": [
        (0, 0, 90, 650),
        (1160, 0, 90, 650),
        # More densely packed ice blocks
        (300, 100, 95, 95),
        (550, 200, 100, 100),
        (750, 280, 110, 90),
        (400, 400, 105, 95),
        (700, 500, 115, 85),
        (950, 350, 100, 100),
    ],
    "finish_y": 40,
    "assets": [
        {"type": "snow_asset", "x": 175, "y": 300},
        {"type": "snow_asset", "x": 1000, "y": 150},
        {"type": "snow_asset", "x": 400, "y": 550},
    ]
}

# ============================================================================
# DESERT THEME - Levels 1 & 2
# ============================================================================
DESERT_LEVEL1 = {
    "name": "Desert - Level 1",
    "theme": "desert",
    "level": 1,
    "time_limit": 55,
    "description": "Cross the desert oasis river. Watch for sand dunes!",
    "background_color": (238, 203, 127),  # Sandy tan
    "water_color": (100, 180, 200),        # Oasis water

    "obstacles": [
        # Sand dunes - side walls
        (0, 0, 110, 650),
        (1140, 0, 110, 650),
        # Cactus/rock obstacles in water
        (400, 120, 110, 100),
        (700, 280, 105, 110),
        (350, 420, 115, 95),
        (850, 500, 100, 90),
    ],
    "finish_y": 40,
    "assets": [
        {"type": "desert_asset", "x": 220, "y": 250},
        {"type": "desert_asset", "x": 900, "y": 400},
    ]
}

DESERT_LEVEL2 = {
    "name": "Desert - Level 2",
    "theme": "desert",
    "level": 2,
    "time_limit": 45,
    "description": "Mirage and mirages! More obstacles and quicksand!",
    "background_color": (238, 203, 127),
    "water_color": (100, 180, 200),

    "obstacles": [
        (0, 0, 100, 650),
        (1150, 0, 100, 650),
        # Quicksand and rocky obstacles
        (380, 80, 105, 100),
        (600, 200, 115, 105),
        (750, 320, 100, 110),
        (420, 440, 110, 95),
        (800, 480, 120, 100),
        (550, 580, 100, 50),
    ],
    "finish_y": 40,
    "assets": [
        {"type": "desert_asset", "x": 200, "y": 350},
        {"type": "desert_asset", "x": 950, "y": 200},
        {"type": "desert_asset", "x": 400, "y": 600},
    ]
}

# ============================================================================
# TROPICS THEME - Levels 1 & 2
# ============================================================================
TROPICS_LEVEL1 = {
    "name": "Tropics - Level 1",
    "theme": "tropics",
    "level": 1,
    "time_limit": 60,
    "description": "Navigate the tropical river jungle. Vines and rocks!",
    "background_color": (50, 120, 50),     # Jungle green
    "water_color": (80, 160, 200),         # River blue

    "obstacles": [
        # Jungle walls - vegetation heavy
        (0, 0, 100, 650),
        (1150, 0, 100, 650),
        # Tropical obstacles
        (380, 150, 105, 100),
        (680, 280, 110, 105),
        (450, 420, 100, 100),
        (850, 520, 110, 95),
    ],
    "finish_y": 40,
    "assets": [
        {"type": "tropics_asset", "x": 250, "y": 300},
        {"type": "tropics_asset", "x": 900, "y": 150},
    ]
}

TROPICS_LEVEL2 = {
    "name": "Tropics - Level 2",
    "theme": "tropics",
    "level": 2,
    "time_limit": 40,
    "description": "Wild jungle! Dense obstacles and strong currents!",
    "background_color": (50, 120, 50),
    "water_color": (80, 160, 200),

    "obstacles": [
        (0, 0, 110, 650),
        (1140, 0, 110, 650),
        # Dense jungle obstacles
        (350, 80, 100, 95),
        (600, 200, 110, 105),
        (750, 300, 105, 110),
        (420, 420, 115, 100),
        (800, 480, 100, 95),
        (550, 580, 110, 50),
    ],
    "finish_y": 40,
    "assets": [
        {"type": "tropics_asset", "x": 200, "y": 350},
        {"type": "tropics_asset", "x": 950, "y": 200},
        {"type": "tropics_asset", "x": 450, "y": 600},
    ]
}

# Theme collection for easy access
THEMES = {
    "forest": {
        1: FOREST_LEVEL1,
        2: FOREST_LEVEL2,
    },
    "snow": {
        1: SNOW_LEVEL1,
        2: SNOW_LEVEL2,
    },
    "desert": {
        1: DESERT_LEVEL1,
        2: DESERT_LEVEL2,
    },
    "tropics": {
        1: TROPICS_LEVEL1,
        2: TROPICS_LEVEL2,
    }
}

def get_theme(theme_name, level):
    """Get theme configuration for specified theme and level."""
    if theme_name in THEMES and level in THEMES[theme_name]:
        return THEMES[theme_name][level]
    return None

def get_all_themes():
    """Get list of all available themes."""
    return list(THEMES.keys())
