# Img2Pen
Little script that can interpolate images to VRChat's using a Pencil

Status: Very alpha stage, on going project

![image](https://github.com/user-attachments/assets/9c81911f-033a-4650-97eb-8bd09d3beae7)

![image](https://github.com/user-attachments/assets/2b1f0094-cf4e-4f76-b7b0-f7c8b2a597d2)

![image](https://github.com/user-attachments/assets/37dc3149-b542-4f2a-9bc2-f1dd118b3f27)


It's a very basic script, nothing complex.
It will try to map out an image in grayscale with a threshold and use it for the pen in VRChat,
the user only has to run the script along side the VRchat window (windowed).

* GRID_WIDTH and GRID_HEIGHT determine the size in-game where the image will be plotted.
* STEP_SIZE and SCALE_FACTOR are the ones that can give more or less detail by adding padding and enlargement.
* METHODS, 0 and 1 are simple vert/horz plotters and 2 is a continuous plotter from left to right and back.
* THRESHOLD holds the minimal value that would indicate if there should be a pixel plotted.
* SX and SY are starting points, these are for internal reference where the plotter initiate its begin.
* DELAY is set to 0.02 , but sometimes the pen stops working, turning this value higher to 0.04+ would fix that.

CONTROLS:
Q for stopping
P for pausing
-/+ for adjusting speed (delay)

Config template:
```
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
```

