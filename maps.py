import random
import pygame
import sys
import math
import os
from typing import Optional, Tuple

# --- TMX loader (pip install pytmx) ---
from pytmx.util_pygame import load_pygame
import pytmx

pygame.init()

# ==================================================
# 1) Create a tiny temporary display BEFORE load_tmx
#    (needed because pytmx uses convert_alpha() on tiles)
# ==================================================
# _temp_screen = pygame.display.set_mode((1, 1))
screen = pygame.display.set_mode((1440, 810), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Cross River (loading...)")

# =======================
# Paths (match your setup)
# =======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_DIR = os.path.join(BASE_DIR, "maps")
MAP_FILE = "crossRiver_Map_Level1.tmx"   # <-- matches your screenshot/file
MAP_PATH = os.path.join(MAP_DIR, MAP_FILE)

print("[DEBUG] CWD        :", os.getcwd())
print("[DEBUG] MAP_DIR    :", MAP_DIR)
print("[DEBUG] MAP_PATH   :", MAP_PATH)
print("[DEBUG] Map exists :", os.path.exists(MAP_PATH))

if not os.path.exists(MAP_PATH):
    try:
        print("[DEBUG] maps/ contents:", os.listdir(MAP_DIR))
    except Exception as e:
        print("[DEBUG] Unable to list maps/:", e)
    raise FileNotFoundError(
        "TMX not found.\n"
        f"Expected here: {MAP_PATH}\n"
        "• Put your .tmx and its tileset PNGs inside the 'maps' folder (as in your screenshots),\n"
        "• or change MAP_FILE above to the correct filename."
    )

# ==================
# Load TMX and tiles
# ==================
try:
    tmx = load_pygame(MAP_PATH)  # resolves tileset images relative to the TMX file
except Exception as e:
    print(f"[TMX] Failed to load {MAP_PATH}: {e}")
    pygame.quit()
    sys.exit(1)

# Map dimensions
tile_w, tile_h = tmx.tilewidth, tmx.tileheight
map_px_width = tmx.width * tile_w
map_px_height = tmx.height * tile_h

# ==============================================
# 2) Now that we know the map size, set real mode
# ==============================================
# screen = pygame.display.set_mode((map_px_width, map_px_height))
# screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN | pygame.SCALED)
# pygame.display.set_caption("Cross River")
clock = pygame.time.Clock()

# ==========================
# Pre-render visible layers
# ==========================
map_surface = pygame.Surface((map_px_width, map_px_height), pygame.SRCALPHA)

# Handles Tile layers even inside Group layers (e.g., your "Level1" group)
for layer in tmx.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        for x, y, gid in layer:
            if gid == 0:
                continue
            img = tmx.get_tile_image_by_gid(gid)
            if img:
                map_surface.blit(img, (x * tile_w, y * tile_h))

# ==========================
# Build collision rectangles
# ==========================
# Treat these tile layers as blocking (present in your TMX):
BLOCKING_LAYER_NAMES = {"Trees", "Puie"}
collision_rects = []

# (A) Any non-empty tile on blocking layers -> solid
for layer in tmx.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer) and layer.name in BLOCKING_LAYER_NAMES:
        for x, y, gid in layer:
            if gid != 0:
                collision_rects.append(pygame.Rect(x * tile_w, y * tile_h, tile_w, tile_h))

# (B) Any tile with tile property collide=true -> solid (optional / future-proof)
for layer in tmx.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        for x, y, gid in layer:
            if gid == 0:
                continue
            props = tmx.get_tile_properties_by_gid(gid)
            if props and props.get("collide") is True:
                collision_rects.append(pygame.Rect(x * tile_w, y * tile_h, tile_w, tile_h))

# =========
# Spawn logic
# =========
def find_bottom_water_spawn(tmx_map) -> Optional[Tuple[float, float]]:
    """
    Find the bottom-most water tile center in the 'River' layer and return (px_x, px_y).
    Uses WATERS_GIDS if those appear in the layer; otherwise falls back to any non-zero GID.
    """
    # If your River layer uses different GIDs for water, update this set:
    WATER_GIDS = {41, 42}

    river_layer: Optional[pytmx.TiledTileLayer] = None
    for lyr in tmx_map.visible_layers:
        if isinstance(lyr, pytmx.TiledTileLayer) and lyr.name == "River":
            river_layer = lyr
            break

    if river_layer is None:
        return None

    # Check whether these GIDs actually appear; if not, we'll treat any non-zero gid as water
    has_listed_water = False
    for _, _, gid in river_layer:
        if gid in WATER_GIDS:
            has_listed_water = True
            break

    bottom_y = -1
    candidates = []

    for x, y, gid in river_layer:
        if gid == 0:
            continue
        is_water = (gid in WATER_GIDS) if has_listed_water else True
        if not is_water:
            continue

        if y > bottom_y:
            bottom_y = y
            candidates = [(x, y)]
        elif y == bottom_y:
            candidates.append((x, y))

    if bottom_y == -1 or not candidates:
        return None

    # Choose the middle water tile in the bottom-most row for a nice centered start
    candidates.sort(key=lambda t: t[0])
    spawn_tx, spawn_ty = candidates[len(candidates) // 2]

    # Convert tile coords to pixel center
    px_x = spawn_tx * tile_w + tile_w / 2
    px_y = spawn_ty * tile_h + tile_h / 2

    # Slightly nudge up so we don’t immediately hit the bottom bank
    px_y -= 2
    return (px_x, px_y)

spawn = find_bottom_water_spawn(tmx)
if spawn is not None:
    spawn_x, spawn_y = spawn
    spawn_x -=210
else:
    # Fallback if 'River' layer not found or has no water
    spawn_x, spawn_y = map_px_width // 2, min(map_px_height - 50, 600)




# =========
# Boat setup (uses the spawn found above)
# =========
WIDTH, HEIGHT = map_px_width, map_px_height  # keep these aliases for later parts of your code

INITIAL_BOAT_POS = pygame.Vector2(spawn_x, spawn_y)
boat_pos = INITIAL_BOAT_POS.copy()
boat_velocity = pygame.Vector2(0, 0)
boat_angle = 0  # face up (forward vector is (0, -1))

# Input tracking for momentum
left_pressed = False
right_pressed = False
input_buffer = 0
input_decay_time = 0.25  # seconds

# Movement/physics tuning (from your original code)
MAX_SPEED = 10
ROTATION_SPEED = 450
ROTATION_STEP = 25
BASE_ACCEL = 0.6
ACCEL_PER_PRESS = 0.35
BASE_FRICTION = 0.99
SIDEWAYS_FRICTION = 0.985

SIDEWAYS_DRIFT_MULT = 0.75
SINGLE_KEY_ACCEL_MULT = 0.8
SINGLE_KEY_SIDEWAYS_MULT = 0.55

boat_image = pygame.image.load("boat.png").convert_alpha() 
boat_image = pygame.transform.scale(boat_image, (30, 54))  # adjust size as needed

def draw_boat(surface, position, angle):
    """Draw the original brown rectangle boat (swap to a canoe sprite later if you want)."""
    boat_shape = [
        pygame.Vector2(5, -9),   # front right
        pygame.Vector2(5, 9),    # back right
        pygame.Vector2(-5, 9),   # back left
        pygame.Vector2(-5, -9)   # front left
    ]
    rotated_shape = [position + p.rotate(angle) for p in boat_shape]
    pygame.draw.polygon(surface, (139, 69, 19), rotated_shape)
    surface.blit(pygame.transform.rotate(boat_image, -angle), boat_image.get_rect(center = position))


# Rotation state for discrete click-based rotations
running = True
last_input_time = pygame.time.get_ticks() / 1000.0
input_this_frame = False
rotating = False
rotation_start_angle = boat_angle
rotation_direction = 0
target_angle = boat_angle
down_pressed = False

boat_collision_radius = 15  # adjust if you later switch to a bigger canoe sprite

def circle_rect_collision(cx, cy, r, rect: pygame.Rect) -> bool:
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top,  min(cy, rect.bottom))
    dx = cx - closest_x
    dy = cy - closest_y
    return (dx * dx + dy * dy) <= (r * r)

timer_seconds = 60.0
font = pygame.font.SysFont(None, 72)

# =========
# Game loop
# =========
while running:
    dt = clock.tick(60) / 1000.0
    current_time = pygame.time.get_ticks() / 1000.0
    input_this_frame = False

    # --- INPUT ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                if not left_pressed:
                    left_pressed = True
                    if not rotating:
                        rotation_start_angle = boat_angle
                        rotation_direction = 1
                        target_angle = (rotation_start_angle + ROTATION_STEP) % 360
                        rotating = True
                    elif rotation_direction == -1:
                        target_angle = rotation_start_angle % 360
                        rotation_direction = 0
                input_buffer += 1
                last_input_time = current_time
                input_this_frame = True

            if event.key == pygame.K_RIGHT:
                if not right_pressed:
                    right_pressed = True
                    if not rotating:
                        rotation_start_angle = boat_angle
                        rotation_direction = -1
                        target_angle = (rotation_start_angle - ROTATION_STEP) % 360
                        rotating = True
                    elif rotation_direction == 1:
                        target_angle = rotation_start_angle % 360
                        rotation_direction = 0
                input_buffer += 1
                last_input_time = current_time
                input_this_frame = True

            if event.key == pygame.K_DOWN:
                if not down_pressed:
                    down_pressed = True
                    if not rotating:
                        rotation_start_angle = boat_angle
                        rotation_direction = 1
                        target_angle = (rotation_start_angle + ROTATION_STEP) % 360
                        rotating = True
                    elif rotation_direction == -1:
                        target_angle = rotation_start_angle % 360
                        rotation_direction = 0
                last_input_time = current_time
                input_this_frame = True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                left_pressed = False
            if event.key == pygame.K_RIGHT:
                right_pressed = False
            if event.key == pygame.K_DOWN:
                down_pressed = False

    # Decay input buffer
    if not input_this_frame:
        if current_time - last_input_time > input_decay_time:
            input_buffer = 0
        else:
            input_buffer *= math.exp(-dt / input_decay_time)

    # Smooth rotations
    if rotating:
        diff = (target_angle - boat_angle + 180) % 360 - 180
        max_step = ROTATION_SPEED * dt
        step = math.copysign(min(abs(diff), max_step), diff)
        boat_angle += step
        remaining = (target_angle - boat_angle + 180) % 360 - 180
        if abs(remaining) < 0.01:
            boat_angle = target_angle % 360
            rotating = False
            rotation_direction = 0
    boat_angle %= 360

    # --- PHYSICS ---
    forward_direction = pygame.Vector2(0, -1).rotate(boat_angle)

    if input_buffer > 0.01:
        total_accel = BASE_ACCEL + ACCEL_PER_PRESS * input_buffer
        if left_pressed != right_pressed:
            total_accel *= SINGLE_KEY_ACCEL_MULT
        boat_velocity += forward_direction * total_accel * dt

    speed = boat_velocity.length()
    if speed > MAX_SPEED:
        boat_velocity = (boat_velocity / speed) * MAX_SPEED

    if speed > 0.01:
        velocity_direction = boat_velocity.normalize()
        alignment = velocity_direction.dot(forward_direction)
        sideways_factor = abs(alignment)
        sideways_effect_multiplier = SIDEWAYS_DRIFT_MULT
        if left_pressed != right_pressed:
            sideways_effect_multiplier *= SINGLE_KEY_SIDEWAYS_MULT
        friction_multiplier = BASE_FRICTION + (1 - sideways_factor) * (SIDEWAYS_FRICTION - BASE_FRICTION) * sideways_effect_multiplier
        boat_velocity *= friction_multiplier
    else:
        boat_velocity = pygame.Vector2(0, 0)

    # Update position
    boat_pos += boat_velocity

    # --- COLLISION WITH TMX RECTS ---
    collided = False
    for rect in collision_rects:
        if circle_rect_collision(boat_pos.x, boat_pos.y, boat_collision_radius, rect):
            collided = True
            break

    if collided:
        # Reset on collision
        boat_pos = INITIAL_BOAT_POS.copy()
        boat_velocity = pygame.Vector2(0, 0)
        boat_angle = 0
        rotating = False

    # --- DRAW ---
    screen.blit(map_surface, (0, 0))
    draw_boat(screen, boat_pos, boat_angle)

    #Timer
    timer_color = (255, 0, 0) if timer_seconds <= 10 else (255, 255, 255)  # red if <= 10 seconds, white otherwise
    timer_text = font.render(f"{timer_seconds:.1f}", True, timer_color)
    timer_rect = timer_text.get_rect(midtop=(WIDTH // 2, 20))

    #Shake effect for timer
    if timer_seconds <= 10:
        shake_x = random.randint(-2, 2)
        shake_y = random.randint(-2, 2)
        timer_rect.x += shake_x
        timer_rect.y += shake_y

    screen.blit(timer_text, timer_rect)

    pygame.display.flip()

pygame.quit()
sys.exit()