# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CrossRiver** is a 2D boat navigation game built with Pygame. Players steer a boat across a river avoiding forest walls and obstacles within a time limit. The game has two levels with distinct visual themes (forest walls vs rock obstacles), a menu system, and win/transition screens.

**Tech:** Python 3.x, Pygame. Optional: pytmx (for maps.py only).

## Running the Game

```bash
pip install pygame
python week2.py          # Latest version — always work on this file
```

Other files (`CrossRiver.py`, `update1.py`, `update1.2.py`, `week1.py`, `level1.0.py`) are earlier iterations kept for reference. `maps.py` is an alternative TMX tilemap approach (requires `pip install pytmx`).

No test suite — test by running the game and playing.

## Architecture (week2.py — 2032 lines)

### Game State Machine

`game_state` controls flow: `"menu"` → `"playing"` (Level 1) → `"level1_complete"` → `"level2"` → `"level2_win"` → back to `"menu"`.

Transitions use `FadeTransition` — call `fade.start(callback)` where the callback sets the new `game_state`.

### Code Organization

The file is structured in labeled sections (`# === SECTION ===`):

1. **Audio Setup** (lines 1–90) — Sound loading, `play_sound()`, `play_paddle_sound()`, ambience/music loops
2. **Window & Asset Loading** (lines 92–130) — Screen setup, `load_image()` for sprites from `assets/images/`
3. **Visual Systems** (lines 131–1040) — Classes for rendering:
   - `WaterRenderer` — Animated multi-layer wave background with sparkles and flow particles
   - `OarAnimator` — Rowing animation state machine
   - `WakeSystem` — Boat wake trail particles
   - `ParticleSystem` — General splash/impact particles
   - `CrashAnimation` — Debris + flash on collision (calls a respawn callback when done)
   - `FishSystem` — Ambient fish jumping in Level 2
   - `ScreenShake` — Camera shake effect
   - `FadeTransition` — Black fade in/out for state transitions
   - `WindSystem` — Visual wind streaks + gameplay current (Level 2 only)
   - `RiverCurrent` — Constant downward drift (Level 2 only)
   - `Button` — Menu button with hover animation
4. **Helper functions** — `create_forest_surface()`, `create_rock_surface()`, `precompute_foam()`, `draw_foam()`, `draw_boat()`, `draw_menu()`
5. **Game Setup** (lines 1150–1353) — Level 1 & 2 state initialization, `reset_game()`, `reset_level2()`
6. **Main Loop** (lines 1355–2032) — Handles all states: menu, playing (L1), level1_complete, level2, level2_win

### Rendering Pipeline (per frame, Level 1)

```
WaterRenderer.draw()         → Animated river background
Exit glow indicator          → Pulsing green line at finish gap
draw_foam()                  → Shoreline foam particles
forest_surface blit          → Pre-rendered forest overlay (static, computed once at startup)
WakeSystem.draw()            → Boat wake trail
CrashAnimation.draw()        → Debris if active
draw_boat()                  → Sprite-based boat with animated oars
Timer HUD                    → Countdown with shake when critical
ScreenShake offset           → Apply shake to final blit
FadeTransition.draw()        → Overlay fade if transitioning
```

Level 2 adds: `RiverCurrent` drift, `WindSystem` gusts, `FishSystem`, `ParticleSystem`.

### Physics System

All state is module-level globals. Key constants (tune these for gameplay feel):

```python
MAX_SPEED = 10          ROTATION_SPEED = 450       ROTATION_STEP = 25
BASE_ACCEL = 0.6        ACCEL_PER_PRESS = 0.35     BASE_FRICTION = 0.99
SIDEWAYS_FRICTION = 0.985   SIDEWAYS_DRIFT_MULT = 0.75
```

**Input buffer system:** Each key press increments `input_buffer`, which decays exponentially (0.25s). Higher buffer = more acceleration. This rewards tapping over holding.

**Rotation:** Discrete 25° steps per press, smoothly animated at 450°/s toward `target_angle`. 0° = up, clockwise positive.

**Velocity:** Forward direction from `boat_angle`, friction varies by alignment (more sideways = more friction).

**Collision:** Circle (15px radius) vs AABB. On collision: triggers `CrashAnimation` which calls a respawn callback after playing debris animation. Level 2 also applies `RiverCurrent` (constant downward push) and `WindSystem` (periodic lateral gusts).

### Level Layouts

**Level 1** (`cubes` list): Forest walls (200px each side) + 4 obstacle rectangles. Win by reaching `y < 40` through the gap at top. Timer: 60s.

**Level 2** (`level2_cubes` list): Narrower forest walls (150px) + scattered rock obstacles. Wind gusts and river current add difficulty. Timer: 45s. Win at `y < LEVEL2_FINISH_Y (40)`.

Obstacles are pre-rendered as static surfaces at startup (`create_forest_surface()` / `create_rock_surface()`), so changing obstacle positions requires restarting the game.

### Assets

```
assets/
├── images/
│   ├── boat/          # Boat sprite frames
│   ├── obstacles/     # Forest canopy PNGs, forest tile
│   └── water/         # (water is procedurally rendered, not used)
└── sounds/
    ├── background_music.ogg
    ├── crash.wav, forest_ambience.wav, wind_gust.wav
    ├── paddle_splash.wav, paddle_splash2.wav, paddle_splash3.wav
    └── paddle_bubble.ogg, paddle_bubble2.ogg
```

Audio gracefully degrades — if mixer init or any sound file fails, the game continues without it.

### Key Patterns

- **All game state is global variables** — reset functions (`reset_game()`, `reset_level2()`) manually reset each variable
- **Level 2 duplicates Level 1 state** with `l2_` prefix (e.g., `l2_boat_pos`, `l2_boat_vel`) rather than sharing code
- **Pre-rendered static surfaces** — Forest and rock overlays are computed once at startup, not per frame
- **`draw_boat()`** renders a detailed sprite-based boat with hull, cabin, oars, and visual effects based on speed
- **Delta time (`dt`)** used throughout for frame-rate independent physics; capped at 0.05s to prevent physics explosions
