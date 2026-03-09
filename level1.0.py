import pygame
import sys
import math

pygame.init()

# Window
WIDTH, HEIGHT = 1250, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cross River")

clock = pygame.time.Clock()

# Boat
INITIAL_BOAT_POS = pygame.Vector2(WIDTH // 2, 600)
boat_pos = INITIAL_BOAT_POS.copy()
boat_velocity = pygame.Vector2(0, 0)  # 2D velocity vector
boat_angle = 0  # Angle in degrees (0 = up)

# Input tracking for momentum
left_pressed = False
right_pressed = False
input_buffer = 0  # Accumulates presses for momentum scaling
input_decay_time = 0.25  # Seconds before momentum decays (reduced for snappier accel)

# Constants
MAX_SPEED = 10  # reduced max speed
ROTATION_SPEED = 450  # degrees per second when turning (increased for much faster rotation)
ROTATION_STEP = 25  # degrees per click
BASE_ACCEL = 0.6  # Base acceleration per frame (reduced)
ACCEL_PER_PRESS = 0.35  # Extra acceleration per buffered press (reduced)
BASE_FRICTION = 0.99  # Multiplier per frame (0.99 = 1% friction per frame; increased for slipperier water)
SIDEWAYS_FRICTION = 0.985  # Extra friction when boat is rotated away from velocity direction (reduced to allow more sliding)
# Drift & acceleration tuning
SIDEWAYS_DRIFT_MULT = 0.75  # 1.0 = original sideways effect; <1 reduces sideways friction globally (reduced slightly)
SINGLE_KEY_ACCEL_MULT = 0.8  # Accel multiplier when exactly one rotation key is held
SINGLE_KEY_SIDEWAYS_MULT = 0.55  # Additional reduction to sideways effect when single key pressed (reduced slightly) 
def draw_boat(surface, position, angle):
    # Restored original Rectangle shape
    boat_shape = [
        pygame.Vector2(5, -9),   # front right
        pygame.Vector2(5, 9),    # back right
        pygame.Vector2(-5, 9),   # back left
        pygame.Vector2(-5, -9)   # front left
    ]

    rotated_shape = []
    for point in boat_shape:
        # Rotate point and add to current position
        rotated_point = point.rotate(angle)
        rotated_shape.append(position + rotated_point)

    pygame.draw.polygon(surface, (139, 69, 19), rotated_shape)

running = True
last_input_time = pygame.time.get_ticks() / 1000.0
input_this_frame = False

# Rotation state for discrete click-based rotations
rotating = False
rotation_start_angle = boat_angle
rotation_direction = 0  # 1 = left/increase, -1 = right/decrease, 0 = none/cancel
target_angle = boat_angle
down_pressed = False

while running:
    dt = clock.tick(60) / 1000.0  # Delta time in seconds
    current_time = pygame.time.get_ticks() / 1000.0
    input_this_frame = False

    # --- INPUT HANDLING ---
    keys = pygame.key.get_pressed()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                # Only trigger on the initial keydown (ignore repeats while held)
                if not left_pressed:
                    left_pressed = True
                    if not rotating:
                        rotation_start_angle = boat_angle
                        rotation_direction = 1
                        target_angle = (rotation_start_angle + ROTATION_STEP) % 360
                        rotating = True
                    else:
                        # If currently rotating the opposite way, cancel back to start
                        if rotation_direction == -1:
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
                    else:
                        if rotation_direction == 1:
                            target_angle = rotation_start_angle % 360
                            rotation_direction = 0
                input_buffer += 1
                last_input_time = current_time
                input_this_frame = True

            if event.key == pygame.K_DOWN:
                # Down click rotates by ROTATION_STEP degrees (smoothly)
                if not down_pressed:
                    down_pressed = True
                    if not rotating:
                        rotation_start_angle = boat_angle
                        rotation_direction = 1
                        target_angle = (rotation_start_angle + ROTATION_STEP) % 360
                        rotating = True
                    else:
                        if rotation_direction == -1:
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

    # Decay input buffer over time (momentum fades), but only if no input this frame
    if not input_this_frame:
        if current_time - last_input_time > input_decay_time:
            input_buffer = 0
        else:
            # Gradually fade it out
            input_buffer *= math.exp(-dt / input_decay_time)
                

    # Smooth discrete rotations toward target_angle using shortest angular difference
    if rotating:
        # Compute shortest signed angle difference in (-180, 180]
        diff = (target_angle - boat_angle + 180) % 360 - 180
        # Move up to ROTATION_SPEED * dt toward the target, don't overshoot
        max_step = ROTATION_SPEED * dt
        step = math.copysign(min(abs(diff), max_step), diff)
        boat_angle += step
        # Recompute remaining diff and snap if close
        remaining = (target_angle - boat_angle + 180) % 360 - 180
        if abs(remaining) < 0.01:
            boat_angle = target_angle % 360
            rotating = False
            rotation_direction = 0
    # Keep angle in range [0, 360)
    boat_angle %= 360

    # --- PHYSICS ---
    # Get boat's forward direction (up = 0 degrees)
    forward_direction = pygame.Vector2(0, -1).rotate(boat_angle)
    
    # Only apply acceleration when input_buffer > 0 (recent button presses)
    if input_buffer > 0.01:
        total_accel = BASE_ACCEL + ACCEL_PER_PRESS * input_buffer
        # Reduce forward acceleration if exactly one rotation key is active
        if left_pressed != right_pressed:
            total_accel *= SINGLE_KEY_ACCEL_MULT
        boat_velocity += forward_direction * total_accel * dt
    
    # Speed limit (magnitude of velocity vector)
    speed = boat_velocity.length()
    if speed > MAX_SPEED:
        boat_velocity = (boat_velocity / speed) * MAX_SPEED
    
    # Apply friction (stronger when boat is moving sideways)
    if speed > 0.01:
        velocity_direction = boat_velocity.normalize()
        # Dot product: 1 = aligned with boat, 0 = perpendicular, -1 = backwards
        alignment = velocity_direction.dot(forward_direction)
        # Sideways factor: 1 = forward, 0 = sideways
        sideways_factor = abs(alignment)
        # Mix friction: normal friction forward, extra friction sideways
        # Reduce sideways friction globally, and further when exactly one rotation key is held
        sideways_effect_multiplier = SIDEWAYS_DRIFT_MULT
        if left_pressed != right_pressed:
            sideways_effect_multiplier *= SINGLE_KEY_SIDEWAYS_MULT
        friction_multiplier = BASE_FRICTION + (1 - sideways_factor) * (SIDEWAYS_FRICTION - BASE_FRICTION) * sideways_effect_multiplier
        boat_velocity *= friction_multiplier
    else:
        boat_velocity = pygame.Vector2(0, 0)
    
    # Update position
    boat_pos += boat_velocity

    # --- COLLISION DETECTION ---
    # Check collision with all cubes
    left_cube_width = 200
    right_cube_width = 200
    
    # Simple AABB collision detection (using boat center point with a collision radius)
    boat_collision_radius = 15
    
    # Define all cubes as (x, y, width, height)
    cubes = [
        (0, 0, left_cube_width, HEIGHT),  # Left cube
        (WIDTH - right_cube_width, 0, right_cube_width, HEIGHT),  # Right cube
        (200, 450, 380, 200),  # Blue cube
        (200, 330, 750, 150),  # Red cube
        (670, 570, 500, 300),  # Black cube
        (330, 0, 720, 230),  # Dark green cube
    ]
    
    # Check collision with each cube
    for cube_x, cube_y, cube_w, cube_h in cubes:
        # Check if boat collides with cube (using AABB)
        if (boat_pos.x - boat_collision_radius < cube_x + cube_w and
            boat_pos.x + boat_collision_radius > cube_x and
            boat_pos.y - boat_collision_radius < cube_y + cube_h and
            boat_pos.y + boat_collision_radius > cube_y):
            boat_pos = INITIAL_BOAT_POS.copy()
            boat_velocity = pygame.Vector2(0, 0)
            boat_angle = 0  # Reset rotation to face ahead
            rotating = False
            break  # Exit loop after collision detected

    # --- DRAWING ---
    screen.fill((100, 120, 230))  # River background

    # Green cube on left side
    left_cube_width = 200
    left_cube_height = HEIGHT
    pygame.draw.rect(screen, (34, 139, 34), (0, 0, left_cube_width, left_cube_height))  # Dark green cube

    # Green cube on right side
    right_cube_width = 200
    right_cube_height = HEIGHT
    pygame.draw.rect(screen, (34, 139, 34), (WIDTH - right_cube_width, 0, right_cube_width, right_cube_height))  # Dark green cube
   
    # Other cubes (x, y, width, height) (34, 139, 34)
    pygame.draw.rect(screen, (34, 139, 34), (200, 450, 380, 200)) #blue
    pygame.draw.rect(screen, (34, 139, 34), (200, 330, 750, 150)) #red
    pygame.draw.rect(screen, (34, 139, 34), (670, 570, 500, 300)) #black
    pygame.draw.rect(screen, (34, 139, 34), (330, 0, 720, 230)) #dark green


    draw_boat(screen, boat_pos, boat_angle)

    pygame.display.flip()

pygame.quit()
sys.exit()