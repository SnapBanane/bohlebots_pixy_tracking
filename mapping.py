import pygame
import numpy as np
import matplotlib.pyplot as plt

def render_grid(screen, field_width, field_height, margin, scale_factor):
    font = pygame.font.Font(None, 20)  # Small font for numbering
    num_columns = 32
    num_rows = 32
    square_width = (field_width) / num_columns  # Width of each square
    square_height = (field_height) / num_rows  # Height of each square

    if square_width <= 0 or square_height <= 0:
        raise ValueError("square_size must be a positive integer")

    for i, x in enumerate(np.arange(margin, field_width, square_width)):
        for j, y in enumerate(np.arange(margin, field_height, square_height)):
            pygame.draw.line(screen, (255, 0, 0), (x, margin), (x, field_height+margin), 1)
            pygame.draw.line(screen, (255, 0, 0), (margin, y), (field_width+margin, y), 1)

            # Draw number at the center of each square
            text = font.render(f"{i},{j}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(x + square_width / 2, y + square_height / 2))
            screen.blit(text, text_rect)

def store_robot_positions(robot_positions):
    with open("robot_positions.txt", "w") as f:
        for robot_id, (x, y) in robot_positions.items():
            f.write(f"{robot_id},{x},{y}\n")

def create_heatmap(heatmap):
    import matplotlib.pyplot as plt

    plt.imshow(heatmap, cmap='hot', interpolation='nearest')
    plt.colorbar()
    plt.title("Robot Heatmap")
    plt.show()