from pathlib import Path

import cv2
import numpy as np

# --- File Management ---
ARCHIVE_DIR = Path.cwd() / "archive"
IMAGE_DIR = ARCHIVE_DIR / "image"

# Ensure directories exist when this module is imported
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# --- Configuration Variables ---
CROP_H_PERCENT = 0.25  # 25% of the screen height
PARTITION_PERCENT = 31  # Cuts off 31% from both left and right sides
LOOP_LIMIT = 5  # For main.py: Set to -1 for infinite loop, or >0 for a count
SCREEN_CAPTURE_DELAY = 0.05
KEY_PRESS_DELAY = 0.01

# --- HSV Constants ---
LOWER_YELLOW = np.array([20, 100, 100])
UPPER_YELLOW = np.array([40, 255, 255])
LOWER_GREEN = np.array([45, 100, 100])
UPPER_GREEN = np.array([85, 255, 255])


# --- Shared Functions ---
def get_center_x(mask):
    """Finds the X-coordinate center of the largest contour in a binary mask."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest)
        if M["m00"] != 0:
            return int(M["m10"] / M["m00"])
    return None
