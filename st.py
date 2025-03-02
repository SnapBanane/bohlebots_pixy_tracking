import pygame
import sys
import random
import serial
import numpy as np
from mapping import render_grid, create_heatmap

# Field dimensions (scaled for window size)
SCALE_FACTOR = 6
FIELD_WIDTH = 203 * SCALE_FACTOR
FIELD_HEIGHT = 135 * SCALE_FACTOR
MARGIN = 20 * (SCALE_FACTOR / 5)

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = FIELD_WIDTH + MARGIN * 2, FIELD_HEIGHT + MARGIN * 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixy2 Multi-Robot Tracking")

# Colors
COLORS = {1: (255, 0, 0), 2: (255, 255, 0), 3: (0, 255, 0), 4: (0, 0, 255)}
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
YELLOW = (242, 214, 34)
BLUE = (34, 51, 242)

# Open Serial Port
try:
    ser = serial.Serial("COM9", 115200, timeout=1)
except serial.SerialException:
    print("Error: Could not open serial port. Ensure ESP32 is connected.")
    ser = None  # If serial fails, continue without it

# Initialize a 2D array to store robot positions
heatmap = np.zeros((32, 32), dtype=int)

def render_field():
    screen.fill(GREEN)
    pygame.draw.rect(screen, WHITE, (MARGIN, MARGIN, FIELD_WIDTH, FIELD_HEIGHT), 2)
    pygame.draw.line(screen, WHITE, (MARGIN + FIELD_WIDTH // 2, MARGIN), 
                     (MARGIN + FIELD_WIDTH // 2, MARGIN + FIELD_HEIGHT), 2)
    pygame.draw.circle(screen, WHITE, (MARGIN + FIELD_WIDTH // 2, MARGIN + FIELD_HEIGHT // 2), 5)
    pygame.draw.circle(screen, WHITE, (MARGIN + FIELD_WIDTH // 2, MARGIN + FIELD_HEIGHT // 2), 60 * SCALE_FACTOR / 2, 2)

    goal_width = FIELD_HEIGHT / 3  
    goal_depth = (7.4 * SCALE_FACTOR) / MARGIN * 4  

    pygame.draw.rect(screen, YELLOW, (MARGIN - goal_depth, MARGIN + FIELD_HEIGHT // 2 - goal_width // 2, goal_depth, goal_width))  
    pygame.draw.rect(screen, BLUE, (MARGIN + FIELD_WIDTH, MARGIN + FIELD_HEIGHT // 2 - goal_width // 2, goal_depth, goal_width))  

def render_robots(robot_positions, heatmap):
    for robot_id, pos in robot_positions.items():
        pygame.draw.circle(screen, COLORS.get(robot_id, WHITE), pos, 25)
        
        # Calculate the grid position
        grid_x = (pos[0] - MARGIN) // (FIELD_WIDTH // 32)
        grid_y = (pos[1] - MARGIN) // (FIELD_HEIGHT // 32)
        
        # Update the heatmap
        if 0 <= grid_x < 32 and 0 <= grid_y < 32:
            heatmap[int(grid_y), int(grid_x)] += 1

def render_mode_indicator(mode, font):
    text_surface = font.render(f"Mode: {mode.capitalize()}", True, WHITE)
    screen.blit(text_surface, (10, 10))

def read_serial_data():
    """
    Reads and processes serial data from ESP32.
    """
    if ser is None:
        return None  # Skip if serial is not available
    try:
        data = ser.readline().decode().strip()  # Read a line from ESP32
        if data:
            parts = data.split(",")  # Expect format "id,x,y"
            if len(parts) == 3:
                robot_id, x, y = map(int, parts)
                
                # Scale and transform coordinates
                x = int((300 - x) * (FIELD_WIDTH / 300))
                y = int((200 - y) * (FIELD_HEIGHT / 200))
                
                return (robot_id, x + MARGIN, y + MARGIN)  # Return transformed coordinates with margin
    except (ValueError, serial.SerialException):
        print("Serial read error")
    return None

def generate_starting_positions():
    center_x = MARGIN + FIELD_WIDTH // 2
    center_y = MARGIN + FIELD_HEIGHT // 2
    radius = 30 * SCALE_FACTOR

    # Positions inside and outside the circle
    position_inside_left = (center_x - 25, center_y)
    position_outside_left = (center_x - radius - 25, center_y + (random.randint(-radius, radius) // 2))
    position_inside_right = (center_x + 25, center_y)
    position_outside_right = (center_x + radius + 25, center_y + (random.randint(-radius, radius) // 2))

    # Valid combinations ensuring one inside, one outside
    combinations = [
        (position_inside_left, position_outside_right),
        (position_outside_left, position_inside_right)
    ]

    # Randomly choose a combination
    combination = random.choice(combinations)

    # Assign positions to the robots
    positions = {
        1 : combination[0],  # Robot with kickoff
        2 : combination[1]  # Robot without kickoff
    }

    return positions

def handle_mode_switch(robot_positions, font, heatmap):
    mode = "manual"  # Default mode is manual
    grid = "off"
    input_active = False  # Flag to check if input is active
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m and not input_active:  # Switch to manual mode
                    mode = "manual"
                    print("Manual Mode")
                elif event.key == pygame.K_a and not input_active:  # Switch to auto mode
                    mode = "auto"
                    print("Auto Mode")
                elif event.key == pygame.K_h:  # Press 'h' to create heat map
                    create_heatmap(heatmap)
                    return
                elif event.key == pygame.K_g: # Toggle Grid
                    if grid == "off":
                        grid = "on"
                    else:
                        grid = "off"
                
                if mode == "manual" and event.key == pygame.K_RETURN:  # When in manual mode, allow input
                    input_active = True
                    user_input = get_text_input(robot_positions, font)
                    if user_input.lower() == 'q':
                        pygame.quit()
                        sys.exit()
                    elif user_input:
                        try:
                            # Parse the input and update robot positions
                            robot_id, x, y = map(int, user_input.split(","))
                            # Check bounds and ensure the robot stays within the field
                            x = max(MARGIN, min(MARGIN + FIELD_WIDTH, x))
                            y = max(MARGIN, min(MARGIN + FIELD_HEIGHT, y))
                            robot_positions[robot_id] = (x, y)
                        except ValueError:
                            print("Invalid input format. Please use the format: ID,X,Y")
                    input_active = False

        # Handle automatic mode behavior
        if mode == "auto":
            # Simulate reading serial data and slow down movement
            for robot_id in robot_positions.keys():
                # Move the robot by a small amount (e.g., 5 units) every frame
                new_x = robot_positions[robot_id][0] + random.randint(-5, 5)
                new_y = robot_positions[robot_id][1] + random.randint(-5, 5)
                # Check bounds and ensure the robot stays within the field
                new_x = max(MARGIN, min(MARGIN + FIELD_WIDTH, new_x))
                new_y = max(MARGIN, min(MARGIN + FIELD_HEIGHT, new_y))
                robot_positions[robot_id] = (new_x, new_y)

        # Render the field, mode indicator, and robots
        render_field()
        if grid == "on":  # Only render grid in manual mode
            render_grid(screen, FIELD_WIDTH, FIELD_HEIGHT, MARGIN, SCALE_FACTOR)
        render_robots(robot_positions, heatmap)
        render_mode_indicator(mode, font)
        pygame.display.flip()  # Update the screen

def get_text_input(robot_positions, font):
    input_text = ""
    input_box = pygame.Rect(20, HEIGHT - 40, 440, 40)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if ser:
                    ser.close()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_text  
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode  

                screen.fill(GREEN)
                render_field()
                render_robots(robot_positions, heatmap)
                pygame.draw.rect(screen, WHITE, input_box, 2)
                text_surface = font.render(input_text, True, WHITE)
                screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))
                pygame.display.flip()

def create_heatmap(heatmap):
    import matplotlib.pyplot as plt
    import numpy as np

    # Print the heatmap array for debugging
    print("Heatmap array:")
    print(np.array2string(heatmap, separator=', '))

    plt.imshow(heatmap, cmap='hot', interpolation='nearest')
    plt.colorbar()
    plt.title("Robot Heatmap")
    plt.show()

def main():
    robot_positions = generate_starting_positions()  # Generate starting positions for robots
    font = pygame.font.Font(None, 36)
    heatmap = np.zeros((32, 32), dtype=int)  # Initialize heatmap

    # Render field once on start to avoid black screen
    render_field()

    # render_grid(screen, FIELD_WIDTH, FIELD_HEIGHT, MARGIN, SCALE_FACTOR)
    
    pygame.display.flip()  # Update screen to show the field

    handle_mode_switch(robot_positions, font, heatmap)

    pygame.quit()

if __name__ == "__main__":
    main()
