import pygame
import numpy as np

def render_grid(screen, field_width, field_height, scale_factor):
    font = pygame.font.Font(None, 20)  # Small font for numbering
    square_width = field_width / 16  # Width of each square
    square_height = field_height / 16  # Height of each square

    if square_width <= 0 or square_height <= 0:
        raise ValueError("square_size must be a positive integer")

    for i, x in enumerate(np.arange(0, field_width, square_width)):
        for j, y in enumerate(np.arange(0, field_height, square_height)):
            pygame.draw.line(screen, (255, 0, 0), (x, 0), (x, field_height), 1)
            pygame.draw.line(screen, (255, 0, 0), (0, y), (field_width, y), 1)

            # Draw number at the center of each square
            text = font.render(f"{i},{j}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(x + square_width / 2, y + square_height / 2))
            screen.blit(text, text_rect)


