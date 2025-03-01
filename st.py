import pygame
import sys
import random
from mapping import render_grid

# Field dimensions (scaled for window size)
SCALE_FACTOR = 6
FIELD_WIDTH = 203 * SCALE_FACTOR  # Width of the field
FIELD_HEIGHT = 135 * SCALE_FACTOR  # Height of the field
MARGIN = 20 * (SCALE_FACTOR / 5)  # Margin for the borders

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = FIELD_WIDTH + MARGIN * 2, FIELD_HEIGHT + MARGIN * 2  # Window dimensions
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixy2 Multi-Robot Tracking")

# Colors for different robots
COLORS = {1: (255, 0, 0), 2: (0, 0, 255), 3: (0, 255, 0), 4: (255, 255, 0)}
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
YELLOW = (242, 214, 34)
BLUE = (34, 51, 242)

# Function to render soccer field lines
def render_field():
    screen.fill(GREEN)  # Green background for the soccer field
    
    # Draw outer border of the field
    pygame.draw.rect(screen, WHITE, (MARGIN, MARGIN, FIELD_WIDTH, FIELD_HEIGHT), 2)
    
    # Draw center line
    pygame.draw.line(screen, WHITE, (MARGIN + FIELD_WIDTH // 2, MARGIN), 
                     (MARGIN + FIELD_WIDTH // 2, MARGIN + FIELD_HEIGHT), 2)
    
    # Draw halfway mark (small dot at the center of the field)
    pygame.draw.circle(screen, WHITE, (MARGIN + FIELD_WIDTH // 2, MARGIN + FIELD_HEIGHT // 2), 5)
    
    # Draw center circle (radius 30 cm, scaled)
    pygame.draw.circle(screen, WHITE, (MARGIN + FIELD_WIDTH // 2, MARGIN + FIELD_HEIGHT // 2), 60 * SCALE_FACTOR / 2, 2)
    
    # **Updated Goal Rendering**: Goal area and goals at left and right sides
    goal_width = FIELD_HEIGHT / 3  # 3 meters scaled down to fit the field
    goal_depth = (7.4 * SCALE_FACTOR) / MARGIN * 4  # Depth of the goal (scaled to 10 cm for window)
    
    # Left goal (centered vertically on the left side)
    pygame.draw.rect(screen, YELLOW, (MARGIN - goal_depth, MARGIN + FIELD_HEIGHT // 2 - goal_width // 2, goal_depth, goal_width))  
    # Right goal (centered vertically on the right side)
    pygame.draw.rect(screen, BLUE, (MARGIN + FIELD_WIDTH, MARGIN + FIELD_HEIGHT // 2 - goal_width // 2, goal_depth, goal_width))  

# Function to render robots on the screen
def render_robots(robot_positions):
    for robot_id, pos in robot_positions.items():
        pygame.draw.circle(screen, COLORS.get(robot_id, (255, 255, 255)), pos, 15)

# Function to render the mode indicator
def render_mode_indicator(mode, font):
    mode_text = f"Mode: {mode.capitalize()}"
    text_surface = font.render(mode_text, True, WHITE)
    screen.blit(text_surface, (10, 10))  # Display in the top-left corner

# Function to handle text input
def get_text_input(robot_positions, font):
    input_text = ""
    input_active = True  # Flag to check if input is active
    input_box = pygame.Rect(20, HEIGHT - 40, 440, 40)  # Position and size of the input box
    cursor_color = WHITE  # Set the cursor color

    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_text  # Return the text when Enter is pressed
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]  # Remove last character on Backspace
                elif event.key == pygame.K_q:  # Press 'q' to quit
                    pygame.quit()
                    sys.exit()
                else:
                    input_text += event.unicode  # Add character to input

                # Redraw after key press
                screen.fill(GREEN)  # Green soccer field
                render_field()  # Redraw field
                render_robots(robot_positions)  # Redraw robots
                # Draw the input box
                pygame.draw.rect(screen, WHITE, input_box, 2)
                text_surface = font.render(input_text, True, WHITE)
                screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))  # Display input text

                # Draw cursor
                cursor_x = input_box.x + 5 + text_surface.get_width()
                pygame.draw.line(screen, cursor_color, (cursor_x, input_box.y + 5), (cursor_x, input_box.y + input_box.height - 5), 2)

                pygame.display.flip()  # Update display

# Function to switch between manual and auto mode
def handle_mode_switch(robot_positions, font):
    mode = "manual"  # Default mode is manual
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
                serial_data = read_serial_data(robot_id)
                try:
                    # Apply slower movement by reducing change in position
                    new_x = robot_positions[robot_id][0] + random.randint(-5, 5)
                    new_y = robot_positions[robot_id][1] + random.randint(-5, 5)
                    # Check bounds and ensure the robot stays within the field
                    new_x = max(MARGIN, min(MARGIN + FIELD_WIDTH, new_x))
                    new_y = max(MARGIN, min(MARGIN + FIELD_HEIGHT, new_y))
                    robot_positions[robot_id] = (new_x, new_y)
                except ValueError:
                    print("Error processing serial data.")

        # Render the field, mode indicator, and robots
        render_field()
        if mode == "manual":  # Only render grid in manual mode
            render_grid(screen, FIELD_WIDTH, FIELD_HEIGHT, SCALE_FACTOR)
        render_robots(robot_positions)
        render_mode_indicator(mode, font)
        pygame.display.flip()  # Update the screen

# Simulate reading serial data
def read_serial_data(robot_id):
    # Simulated serial data input (normally this would come from the ESP32)
    # Example: "1,100,150\n"
    return f"{robot_id},{random.randint(100, 500)},{random.randint(100, 400)}\n"  # Simulated serial data

# Main loop
def main():
    robot_positions = {1: (200, 200), 2: (400, 200)}  # Initial positions for two robots
    font = pygame.font.Font(None, 36)

    # Render field once on start to avoid black screen
    render_field()

    render_grid(screen, FIELD_WIDTH, FIELD_HEIGHT, SCALE_FACTOR)
    
    pygame.display.flip()  # Update screen to show the field

    handle_mode_switch(robot_positions, font)

    pygame.quit()

if __name__ == "__main__":
    main()
