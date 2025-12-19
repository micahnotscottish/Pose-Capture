import pygame
import random

# List to store all meteors
meteors = []

# Function to create new meteors
def spawn_meteor(screen_width):
    x = random.randint(0, screen_width - 30)  # random x position
    y = -30  # start above the screen
    speed = random.randint(3, 7)  # falling speed
    size = random.randint(20, 50)
    meteors.append({"x": x, "y": y, "speed": speed, "size": size})

# Function to update meteor positions and draw them
def update_and_draw_meteors(screen, color=(200, 0, 0)):
    for meteor in meteors:
        meteor["y"] += meteor["speed"]  # move meteor down
        pygame.draw.circle(screen, color, (meteor["x"], meteor["y"]), meteor["size"])

    # Remove meteors that go off screen
    meteors[:] = [m for m in meteors if m["y"] - m["size"] < screen.get_height()]
