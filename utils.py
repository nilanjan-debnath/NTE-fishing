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
LOOP_LIMIT = 1500  # For main.py: Set to -1 for infinite loop, or >0 for a count
SCREEN_CAPTURE_DELAY = 0.03
KEY_PRESS_DELAY = 0.01
MAX_HOLD_SECONDS = 1.5
AUTO_SELL_AND_BUY = True
SELL_AND_BUY_AFTER = 90

# --- HSV Constants ---
LOWER_YELLOW = np.array([20, 100, 100])
UPPER_YELLOW = np.array([40, 255, 255])
LOWER_GREEN = np.array([45, 100, 100])
UPPER_GREEN = np.array([85, 255, 255])


def get_x_coords(mask):
    """Finds the center, left, and right X-coordinates of the largest contour."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)

        # 1. Get the bounding box to find the left and right edges
        x, _y, w, _h = cv2.boundingRect(largest)
        left_x = x
        right_x = x + w

        # 2. Calculate the center of mass
        M = cv2.moments(largest)
        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])

            # Return all three values as a tuple
            return center_x, left_x, right_x

    # Return Nones if nothing is found
    return None, None, None
