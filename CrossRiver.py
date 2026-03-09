import pygame
import sys
import math

pygame.init()

# Window
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cross River")

clock = pygame.time.Clock()

# Boat
boat_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
boat_speed = 0
boat_angle = 0

ACCELERATION = 0.2
MAX_SPEED = 5
ROTATION_SPEED = 3
FRICTION = 0.05

def draw_boat(surface, position, angle):
    # Boat shape (triangle)
    boat_shape = [
        pygame.Vector2(15, -30),   # front
        pygame.Vector2(15, 30),   # right
        pygame.Vector2(-15, 30),
        pygame.Vector2(-15, -30)   # left
    ]

    rotated_shape = []
    for point in boat_shape:
        rotated_point = point.rotate(angle)
        rotated_shape.append(position + rotated_point)

    pygame.draw.polygon(surface, (139, 69, 19), rotated_shape)

# --- MAIN GAME LOOP ---
running = True
while running:
    clock.tick(60)

    # 1. Event Handling (Pulse & Snap)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # When key is first pressed down
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                boat_angle = -25    # Snap to 25 degrees Right
                boat_speed += 3.0   # The "Pulse" (Impulse)
            
            if event.key == pygame.K_RIGHT:
                boat_angle = 25     # Snap to 25 degrees Left
                boat_speed += 3.0   # The "Pulse" (Impulse)

    # 2. Acceleration (Optional: keep if you still want UP/DOWN to work normally)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        boat_speed += ACCELERATION
    if keys[pygame.K_DOWN]:
        boat_speed -= ACCELERATION

    # 3. Speed limits
    boat_speed = max(-MAX_SPEED, min(MAX_SPEED, boat_speed))

    # 4. Friction (Water Resistance)
    if boat_speed > 0:
        boat_speed -= FRICTION
        if boat_speed < 0: boat_speed = 0
    elif boat_speed < 0:
        boat_speed += FRICTION
        if boat_speed > 0: boat_speed = 0

    # 5. Movement Calculation
    # Note: We calculate direction based on the current boat_angle
    direction = pygame.Vector2(0, -1).rotate(-boat_angle)
    boat_pos += direction * boat_speed

    # 6. Rendering (Drawing)
    screen.fill((34, 139, 34))  # Grass background

    # Draw the River
    pygame.draw.rect(screen, (0, 100, 255), (0, 200, WIDTH, 200))

    # Draw the Boat
    draw_boat(screen, boat_pos, boat_angle)

    pygame.display.flip()
    pygame.display.flip()

pygame.quit()
sys.exit()