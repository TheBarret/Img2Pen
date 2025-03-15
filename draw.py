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

# Configuration
METHOD          = 2     # 0 = horizontal, 1 = vertical, 2 = continuous lines
THRESHOLD       = 127   # color threshold trigger (mid)
GRID_WIDTH      = 50  # columns
GRID_HEIGHT     = 50  # rows
STEP_SIZE       = 4   # step
SCALE_FACTOR    = 2   # scaler
SX              = 512  # Starting X position
SY              = 512  # Starting Y position
DELAY           = 0.02  # Delay between movements
PAUSE_KEY       = "p"  # Key to pause/resume
QUIT_KEY        = "q"  # Key to quit
SPEED_UP        = "="  # Key to increase speed
SPEED_DOWN      = "-"  # Key to decrease speed
FILENAME        = ""   # placeholder filename

# Global variables for control
paused = False
quit_requested = False

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

def draw_horizontal_lines(hwnd, image_path, start_x, start_y):
    """Draw an image using horizontal scan lines."""
    global paused, quit_requested
    activate_window(hwnd)
    image = Image.open(image_path).convert("L")     # Convert to grayscale
    image = image.resize((GRID_WIDTH, GRID_HEIGHT)) # Resize to fit the grid
    pixels = image.load()
    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    for row in range(GRID_HEIGHT):
        col = 0
        while col < GRID_WIDTH:
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
            if pixels[col, row] < THRESHOLD:
                move_mouse_relative(0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(DELAY)
                while col < GRID_WIDTH and pixels[col, row] < THRESHOLD:
                    move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)
                    time.sleep(DELAY)
                    col += 1
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(DELAY)
            else:
                move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)
                time.sleep(DELAY)
                col += 1
        move_mouse_relative(-GRID_WIDTH * STEP_SIZE * SCALE_FACTOR, STEP_SIZE * SCALE_FACTOR)
        time.sleep(0.3)
        
    return True

def draw_vertical_lines(hwnd, image_path, start_x, start_y):
    """Draw an image using vertical scan lines."""
    global paused, quit_requested
    activate_window(hwnd)
    image = Image.open(image_path).convert("L")     # Convert to grayscale
    image = image.resize((GRID_WIDTH, GRID_HEIGHT)) # Resize to fit the grid
    pixels = image.load()
    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    for col in range(GRID_WIDTH):
        row = 0
        while row < GRID_HEIGHT:
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
            if pixels[col, row] < THRESHOLD:
                move_mouse_relative(0, 0)  # Ensure the cursor is in the correct position
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(DELAY)
                while row < GRID_HEIGHT and pixels[col, row] < THRESHOLD:
                    move_mouse_relative(0, STEP_SIZE * SCALE_FACTOR)
                    time.sleep(DELAY)
                    row += 1
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(DELAY)
            else:
                move_mouse_relative(0, STEP_SIZE * SCALE_FACTOR)
                row += 1
                time.sleep(DELAY)
        move_mouse_relative(STEP_SIZE * SCALE_FACTOR, -GRID_HEIGHT * STEP_SIZE * SCALE_FACTOR)
        time.sleep(DELAY)
        
    return True
    
def draw_continuous_lines(hwnd, image_path, start_x, start_y):
    """Draw an image using continuous horizontal scan lines."""
    global paused, quit_requested
    activate_window(hwnd)
    image = Image.open(image_path).convert("L")     # Convert to grayscale
    image = image.resize((GRID_WIDTH, GRID_HEIGHT)) # Resize to fit the grid
    pixels = image.load()
    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.1)
    
    for row in range(GRID_HEIGHT):
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
            # Left to right
            for col in range(GRID_WIDTH):
                handle_hotkeys()
                if pixels[col, row] < THRESHOLD:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    #time.sleep(DELAY)
                move_mouse_relative(STEP_SIZE * SCALE_FACTOR, 0)
                time.sleep(DELAY)
                if pixels[col, row] >= THRESHOLD:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(DELAY)
        else:
            # Right to left
            for col in range(GRID_WIDTH - 1, -1, -1):
                handle_hotkeys()
                if pixels[col, row] < THRESHOLD:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    #time.sleep(DELAY)
                move_mouse_relative(-STEP_SIZE * SCALE_FACTOR, 0)
                time.sleep(DELAY)
                if pixels[col, row] >= THRESHOLD:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(DELAY)
        
        # Move down to the next row
        move_mouse_relative(0, STEP_SIZE * SCALE_FACTOR)
        time.sleep(0.3)
    
    return True

if __name__ == "__main__":
    try:
        if len(sys.argv) >= 2:
            if sys.argv[1] == '*':
                image_files = [f for f in os.listdir('.') if f.endswith(('.png', '.jpg'))]
                if not image_files:
                    print("Error: No files found")
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
        if METHOD == 0:
            draw_horizontal_lines(get_vrchat_window(), FILENAME, SX, SY)
        elif METHOD == 1:
            draw_vertical_lines(get_vrchat_window(), FILENAME, SX, SY)
        elif METHOD == 2:
            draw_continuous_lines(get_vrchat_window(), FILENAME, SX, SY)
        else:
            print("Error: draw method undefined")
        print("Finished")
    except Exception as e:
        print(f"Error: {e}")
        print("Usage: python draw.py [image_file] [grid_width] [grid_height]")
        print("[Random image: python draw.py * [grid_width] [grid_height]]")