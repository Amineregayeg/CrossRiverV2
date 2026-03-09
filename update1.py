import pygame
import sys
import math

pygame.init()

# Window
WIDTH, HEIGHT = 1450, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cross River")

clock = pygame.time.Clock()

# Boat
boat_pos = pygame.Vector2(WIDTH // 2, 650)
boat_velocity = pygame.Vector2(0, 0)  # 2D velocity vector
boat_angle = 0  # Angle in degrees (0 = up)

# Input tracking for momentum
left_pressed = False
right_pressed = False
input_buffer = 0  # Accumulates presses for momentum scaling
input_decay_time = 0.4  # Seconds before momentum decays

# Constants
MAX_SPEED = 12
ROTATION_SPEED = 25  # degrees per frame when turning
BASE_ACCEL = 0.8  # Base acceleration per frame
ACCEL_PER_PRESS = 0.5  # Extra acceleration per buffered press
BASE_FRICTION = 0.98  # Multiplier per frame (0.98 = 2% friction per frame)
SIDEWAYS_FRICTION = 0.92  # Extra friction when boat is rotated away from velocity direction

def draw_boat(surface, position, angle):
    # Restored original Rectangle shape
    boat_shape = [
        pygame.Vector2(5, -10),   # front right
        pygame.Vector2(5, 10),    # back right
        pygame.Vector2(-5, 10),   # back left
        pygame.Vector2(-5, -10)   # front left
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
                boat_angle += ROTATION_SPEED
                input_buffer += 1
                last_input_time = current_time
                input_this_frame = True
            
            if event.key == pygame.K_RIGHT:
                boat_angle -= ROTATION_SPEED
                input_buffer += 1
                last_input_time = current_time
                input_this_frame = True

    # Decay input buffer over time (momentum fades), but only if no input this frame
    if not input_this_frame:
        if current_time - last_input_time > input_decay_time:
            input_buffer = 0
        else:
            # Gradually fade it out
            input_buffer *= math.exp(-dt / input_decay_time)
                

    # --- PHYSICS ---
    # Get boat's forward direction (up = 0 degrees)
    forward_direction = pygame.Vector2(0, -1).rotate(boat_angle)
    
    # Only apply acceleration when input_buffer > 0 (recent button presses)
    if input_buffer > 0.01:
        total_accel = BASE_ACCEL + ACCEL_PER_PRESS * input_buffer
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
        friction_multiplier = BASE_FRICTION + (1 - sideways_factor) * (SIDEWAYS_FRICTION - BASE_FRICTION)
        boat_velocity *= friction_multiplier
    else:
        boat_velocity = pygame.Vector2(0, 0)
    
    # Update position
    boat_pos += boat_velocity

    # --- DRAWING ---
    screen.fill((100, 120, 230))  # River background

    draw_boat(screen, boat_pos, boat_angle)

    pygame.display.flip()

pygame.quit()
sys.exit()