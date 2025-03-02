import pygame
import sys
import random
import serial
from mapping import render_grid

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

def render_robots(robot_positions):
    for robot_id, pos in robot_positions.items():
        pygame.draw.circle(screen, COLORS.get(robot_id, WHITE), pos, 25)

def render_mode_indicator(mode, font):
    text_surface = font.render(f"Mode: {mode.capitalize()}", True, WHITE)
    screen.blit(text_surface, (10, 10))

def read_serial_data():
    """Reads and processes serial data from ESP32."""
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

def handle_mode_switch(robot_positions, font):
    mode = "manual"  
    input_active = False  

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if ser:
                    ser.close()  # Close serial port before exiting
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m and not input_active:
                    mode = "manual"
                    print("Switched to Manual Mode")
                elif event.key == pygame.K_a and not input_active:
                    mode = "auto"
                    print("Switched to Auto Mode")
                elif mode == "manual" and event.key == pygame.K_RETURN:
                    input_active = True
                    user_input = get_text_input(robot_positions, font)
                    if user_input.lower() == 'q':
                        pygame.quit()
                        sys.exit()
                    elif user_input:
                        try:
                            robot_id, x, y = map(int, user_input.split(","))
                            x = max(MARGIN, min(MARGIN + FIELD_WIDTH, x))
                            y = max(MARGIN, min(MARGIN + FIELD_HEIGHT, y))
                            robot_positions[robot_id] = (x, y)
                        except ValueError:
                            print("Invalid input format: Use 'ID,X,Y'")
                    input_active = False

        if mode == "auto":
            serial_data = read_serial_data()
            if serial_data:
                robot_id, x, y = serial_data
                x = max(MARGIN, min(MARGIN + FIELD_WIDTH, x))
                y = max(MARGIN, min(MARGIN + FIELD_HEIGHT, y))
                robot_positions[robot_id] = (x, y)

        render_field()
        if mode == "manual":
            render_grid(screen, FIELD_WIDTH, FIELD_HEIGHT, MARGIN, SCALE_FACTOR)
        render_robots(robot_positions)
        render_mode_indicator(mode, font)
        pygame.display.flip()

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
                render_robots(robot_positions)
                pygame.draw.rect(screen, WHITE, input_box, 2)
                text_surface = font.render(input_text, True, WHITE)
                screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))
                pygame.display.flip()

def main():
    robot_positions = {1: (200, 200), 2: (400, 200)}
    font = pygame.font.Font(None, 36)

    render_field()
    render_grid(screen, FIELD_WIDTH, FIELD_HEIGHT, MARGIN, SCALE_FACTOR)
    pygame.display.flip()  

    handle_mode_switch(robot_positions, font)

    if ser:
        ser.close()

if __name__ == "__main__":
    main()
