import sys
import os
import win32gui
import win32con
import win32api
import time
import random
import math
import keyboard
from PIL import Image
import numpy as np

### Configuration ###

# Draw methods:
# 0 = zig-zag (horz)
# 1 = zig-zag (vert)
# 2 = zig-zag (vert/double)
# 3 = concentric spiral
# 4 = concentric squares

METHOD          = 3

# Quality and speed
THRESHOLD       = 127   # color threshold trigger (mid)
STEP_SIZE       = 5     # step
SCALE_FACTOR    = 2     # scaler
INVERSE         = True  # reverse polarity
DELAY           = 0.04  # Delay between movements

### END OF CONFIG ###
SX              = 512   # Starting X position
SY              = 512   # Starting Y position
GRID_WIDTH      = 50    # default columns
GRID_HEIGHT     = 50    # default rows
FILENAME        = ""    # placeholder filename
PAUSE_KEY       = "p"   # Key to pause/resume
QUIT_KEY        = "q"   # Key to quit
SPEED_UP        = "="   # Key to increase speed
SPEED_DOWN      = "-"   # Key to decrease speed
paused          = False
quit_requested  = False

def handle_hotkeys():
    """Handle hotkey presses."""
    global paused, quit_requested, DELAY
    if keyboard.is_pressed(PAUSE_KEY):
        paused = not paused
        print("Paused" if paused else "Resumed")
        # Debounce to avoid multiple toggles
        time.sleep(0.5)
    if keyboard.is_pressed(QUIT_KEY):
        quit_requested = True
        print("Quit requested...")
    if keyboard.is_pressed(SPEED_UP):
        DELAY = max(0.01, DELAY - 0.01)
        print(f"Speed: {DELAY}")
    if keyboard.is_pressed(SPEED_DOWN):
        DELAY += 0.01
        print(f"Speed: {DELAY}")

def get_vrchat_window():
    """Find the VRChat window by its title."""
    hwnd = win32gui.FindWindow(None, "VRChat")
    if not hwnd:
        raise Exception("VRChat window not found!")
    return hwnd

def activate_window(hwnd):
    """Activate the VRChat window."""
    win32gui.SetForegroundWindow(hwnd)
    # allow alt-tab to breath
    time.sleep(0.1)

def move_mouse_relative(dx, dy):
    """Move the mouse relative to its current position."""
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)

# little dirty hack for preventing pencil eraser feature
def hard_release():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def create_binary_image_cache(image_path, width, height, threshold):
    image = Image.open(image_path).convert("L")  # Convert to grayscale
    image = image.resize((width, height))        # Resize to grid dimensions
    pixels = np.array(image)
    
    # Create binary representation (1 for drawing pixels, 0 for non-drawing)
    binary_image = (pixels < threshold).astype(np.int8)
    
    # Create horizontal and vertical run-length encodings for each row and column
    h_runs = []
    for row in range(height):
        row_runs = []
        col = 0
        while col < width:
            if binary_image[row, col] == 1:  # Drawing pixel
                run_start = col
                while col < width and binary_image[row, col] == 1:
                    col += 1
                row_runs.append((run_start, col - 1))  # Store start and end indices
            else:
                col += 1
        h_runs.append(row_runs)
    
    v_runs = []
    for col in range(width):
        col_runs = []
        row = 0
        while row < height:
            if binary_image[row, col] == 1:  # Drawing pixel
                run_start = row
                while row < height and binary_image[row, col] == 1:
                    row += 1
                col_runs.append((run_start, row - 1))  # Store start and end indices
            else:
                row += 1
        v_runs.append(col_runs)
    
    return {
        'binary': binary_image,
        'h_runs': h_runs,
        'v_runs': v_runs
    }

def draw_horz_zigzag(hwnd, image_cache, start_x, start_y):
    """Draw an image using continuous horizontal scan lines with binary cache."""
    global paused, quit_requested
    activate_window(hwnd)
    binary_image = image_cache['binary']
    height, width = binary_image.shape
    
    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    
    for row in range(height):
        handle_hotkeys()
        if quit_requested:
            print("Drawing aborted")
            return False
        if paused:
            while paused:
                handle_hotkeys()
                if quit_requested:
                    print("Drawing aborted")
                    return False
                time.sleep(0.1)
        
        if row % 2 == 0:
            pen_down = False
            for col in range(width):
                handle_hotkeys()
                if binary_image[row, col] == 1:
                    if not pen_down:
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        pen_down = True
                else:
                    if pen_down:
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                        pen_down = False

                time.sleep(0.02)
                move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)

            if pen_down:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                hard_release()
        else:
            pen_down = False
            for col in range(width - 1, -1, -1):
                handle_hotkeys()
                if binary_image[row, col] == 1:  # Dark pixel (draw)
                    if not pen_down:
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        pen_down = True
                else:  # Light pixel (don't draw)
                    if pen_down:
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                        pen_down = False

                time.sleep(0.02)
                move_mouse_relative(-STEP_SIZE * SCALE_FACTOR, 0)

            if pen_down:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        move_mouse_relative(0, STEP_SIZE * SCALE_FACTOR)
    return True


def draw_spiral(hwnd, image_cache, start_x, start_y):
    """Draws the image in a spiral pattern from the center outward."""
    global paused, quit_requested, SCALE_FACTOR
    activate_window(hwnd)

    binary_image = image_cache['binary']
    height, width = binary_image.shape

    cx, cy = width // 2, height // 2
    x, y = cx, cy
    dx, dy = STEP_SIZE * SCALE_FACTOR, 0
    segment_length = 1
    step_count = 0
    turn_counter = 0

    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    state = 1
    if INVERSE: state = 0
    
    for _ in range(width * height):
        handle_hotkeys()
        if quit_requested:
            print("Drawing aborted")
            return False
        if paused:
            while paused:
                handle_hotkeys()
                if quit_requested:
                    print("Drawing aborted")
                    return False
                time.sleep(0.1)
    
        if 0 <= y < height and 0 <= x < width and binary_image[y, x] == state:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

        move_mouse_relative(dx, dy)
        time.sleep(DELAY)

        if 0 <= y < height and 0 <= x < width and binary_image[y, x] == state:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            hard_release()
       
        x += dx // (STEP_SIZE * SCALE_FACTOR)
        y += dy // (STEP_SIZE * SCALE_FACTOR)
        
        step_count += 1
            
        if step_count == segment_length:
            step_count = 0
            turn_counter += 1
            dx, dy = -dy, dx
            if turn_counter % 2 == 0:
                segment_length += 1
    return True

def draw_vertical_zigzag(hwnd, image_cache, start_x, start_y):
    """Draws the image using a vertical zigzag pattern."""
    global paused, quit_requested
    activate_window(hwnd)

    binary_image = image_cache['binary']
    height, width = binary_image.shape

    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    state = 1
    if INVERSE: state = 0

    for col in range(width):
        handle_hotkeys()
        if quit_requested:
            print("Drawing aborted")
            return False
        if paused:
            while paused:
                handle_hotkeys()
                if quit_requested:
                    print("Drawing aborted")
                    return False
                time.sleep(0.1)

        if col % 2 == 0:
            # Top to bottom
            for row in range(height):
                handle_hotkeys()
                if binary_image[row, col] == state:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                move_mouse_relative(0, STEP_SIZE * SCALE_FACTOR)
                time.sleep(DELAY)
                if binary_image[row, col] == state:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    hard_release()
        else:
            # Bottom to top
            for row in range(height - 1, -1, -1):
                handle_hotkeys()
                if binary_image[row, col] == state:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                move_mouse_relative(0, -STEP_SIZE * SCALE_FACTOR)
                time.sleep(DELAY)
                if binary_image[row, col] == state:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    hard_release()

        # Move to the next column
        move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)
    return True
    
def draw_double_line_zigzag(hwnd, image_cache, start_x, start_y):
    """Draws the image using a double-line vertical zigzag pattern."""
    global paused, quit_requested
    activate_window(hwnd)

    binary_image = image_cache['binary']
    height, width = binary_image.shape

    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    state = 1
    if INVERSE: state = 0

    for col in range(0, width, 2):  # Step by 2 to handle two lines at a time
        handle_hotkeys()
        if quit_requested:
            print("Drawing aborted")
            return False
        if paused:
            while paused:
                handle_hotkeys()
                if quit_requested:
                    print("Drawing aborted")
                    return False
                time.sleep(0.1)

        # First line: Top to bottom
        for row in range(height):
            handle_hotkeys()
            if col < width and binary_image[row, col] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            move_mouse_relative(0, STEP_SIZE * SCALE_FACTOR)
            time.sleep(DELAY)
            if col < width and binary_image[row, col] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                hard_release()

        # Move to the next column for the second line
        if col + 1 < width:
            move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)

        # Second line: Bottom to top
        for row in range(height - 1, -1, -1):
            handle_hotkeys()
            if col + 1 < width and binary_image[row, col + 1] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            move_mouse_relative(0, -STEP_SIZE * SCALE_FACTOR)
            time.sleep(DELAY)
            if col + 1 < width and binary_image[row, col + 1] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                hard_release()

        # Move to the next pair of columns
        if col + 2 < width:
            move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)
    return True

def draw_concentric_squares(hwnd, image_cache, start_x, start_y):
    """Draws the image using concentric squares."""
    global paused, quit_requested
    activate_window(hwnd)

    binary_image = image_cache['binary']
    height, width = binary_image.shape

    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    state = 1
    if INVERSE: state = 0

    left, right, top, bottom = 0, width - 1, 0, height - 1

    while left <= right and top <= bottom:
        handle_hotkeys()
        if quit_requested:
            print("Drawing aborted")
            return False
        if paused:
            while paused:
                handle_hotkeys()
                if quit_requested:
                    print("Drawing aborted")
                    return False
                time.sleep(0.1)

        # Draw top row (left to right)
        for col in range(left, right + 1):
            handle_hotkeys()
            if binary_image[top, col] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)
            time.sleep(DELAY)
            if binary_image[top, col] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                hard_release()

        # Move down to the next row
        move_mouse_relative(0, STEP_SIZE * SCALE_FACTOR)
        top += 1

        # Draw right column (top to bottom)
        for row in range(top, bottom + 1):
            handle_hotkeys()
            if binary_image[row, right] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            move_mouse_relative(0, STEP_SIZE * SCALE_FACTOR)
            time.sleep(DELAY)
            if binary_image[row, right] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                hard_release()

        # Move left to the next column
        move_mouse_relative(-STEP_SIZE * SCALE_FACTOR, 0)
        right -= 1

        # Draw bottom row (right to left)
        for col in range(right, left - 1, -1):
            handle_hotkeys()
            if binary_image[bottom, col] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            move_mouse_relative(-STEP_SIZE * SCALE_FACTOR, 0)
            time.sleep(DELAY)
            if binary_image[bottom, col] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                hard_release()

        # Move up to the next row
        move_mouse_relative(0, -STEP_SIZE * SCALE_FACTOR)
        bottom -= 1

        # Draw left column (bottom to top)
        for row in range(bottom, top - 1, -1):
            handle_hotkeys()
            if binary_image[row, left] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            move_mouse_relative(0, -STEP_SIZE * SCALE_FACTOR)
            time.sleep(DELAY)
            if binary_image[row, left] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                hard_release()

        # Move right to the next column
        move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)
        left += 1
    return True

def draw_row_by_row_with_gaps(hwnd, image_cache, start_x, start_y):
    """Draws the image row by row, skipping every other pixel."""
    global paused, quit_requested
    activate_window(hwnd)

    binary_image = image_cache['binary']
    height, width = binary_image.shape

    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    state = 1
    if INVERSE: state = 0

    for row in range(height):
        handle_hotkeys()
        if quit_requested:
            print("Drawing aborted")
            return False
        if paused:
            while paused:
                handle_hotkeys()
                if quit_requested:
                    print("Drawing aborted")
                    return False
                time.sleep(0.1)

        for col in range(0, width, 2):  # Skip every other pixel
            if binary_image[row, col] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            move_mouse_relative(STEP_SIZE * SCALE_FACTOR * 2, 0)  # Move twice the step size
            time.sleep(DELAY)
            if binary_image[row, col] == state:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                hard_release()

        # Move down to the next row
        move_mouse_relative(-width * STEP_SIZE * SCALE_FACTOR, STEP_SIZE * SCALE_FACTOR)
    return True

if __name__ == "__main__":
    try:
        if len(sys.argv) >= 2:
            if sys.argv[1] == '*':
                image_files = [f for f in os.listdir('.') if f.endswith(('.png', '.jpg', '.jpeg'))]
                if not image_files:
                    print("Error: No image files found")
                    sys.exit(1)
                FILENAME = random.choice(image_files)
            else:
                FILENAME = sys.argv[1]
            
        if len(sys.argv) >= 4:
            try:
                GRID_WIDTH = int(sys.argv[2])
                GRID_HEIGHT = int(sys.argv[3])
            except ValueError:
                print("Error: Grid dimensions must be integers")
                print("Usage: python draw.py [image_file] [grid_width] [grid_height]")
                sys.exit(1)
        
        # Check if file exists
        if not os.path.exists(FILENAME):
            print(f"Error: File '{FILENAME}' not found")
            sys.exit(1)
            
        print(f"File    : {FILENAME}")
        print(f"Method  : {METHOD}")
        print(f"Start   : {SX}x{SY}")
        print(f"Grid    : {GRID_WIDTH}x{GRID_HEIGHT}")
        print(f"Step    : {STEP_SIZE}")
        print(f"Scaler  : {SCALE_FACTOR}")
        print(f"Delay   : {DELAY}")
        print("Controls : P = Pause/Resume, Q = Quit, + = Speed up, - = Slow down")
        
        # Create the binary image cache
        print("Preprocessing image...")
        image_cache = create_binary_image_cache(FILENAME, GRID_WIDTH, GRID_HEIGHT, THRESHOLD)
        print("Preprocessing complete, starting to draw...")
        
        if METHOD == 0:
            draw_horz_zigzag(get_vrchat_window(), image_cache, SX, SY)
        elif METHOD == 1:
            draw_vertical_zigzag(get_vrchat_window(), image_cache, SX, SY)
        elif METHOD == 2:
            draw_double_line_zigzag(get_vrchat_window(), image_cache, SX, SY)
        elif METHOD == 3:
            draw_spiral(get_vrchat_window(), image_cache, SX, SY)
        elif METHOD == 4:
            draw_concentric_squares(get_vrchat_window(), image_cache, SX, SY)
        else:
            print("Error: draw method undefined")
        print("Finished")
    except Exception as e:
        print(f"Error: {e}")
        print("Usage: python draw.py [image_file] [grid_width] [grid_height]")
        print("[Random image: python draw.py * [grid_width] [grid_height]]")
