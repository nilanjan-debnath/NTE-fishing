import sys
import time

import cv2
import mss
import numpy as np
import pyautogui

# Import shared variables and functions
from utils import (
    CROP_H_PERCENT,
    IMAGE_DIR,
    LOWER_GREEN,
    LOWER_YELLOW,
    PARTITION_PERCENT,
    UPPER_GREEN,
    UPPER_YELLOW,
    get_center_x,
)

pyautogui.FAILSAFE = True


def run_test():
    print("Starting test script in 3 seconds... Switch to game!")
    time.sleep(3)

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        # Pre-calculate ROI
        w, h = monitor["width"], monitor["height"]
        crop_h = int(h * CROP_H_PERCENT)
        start_w = int(w * PARTITION_PERCENT / 100)
        end_w = int(w * (100 - PARTITION_PERCENT) / 100)

        roi = {
            "top": monitor["top"],
            "left": monitor["left"] + start_w,
            "width": end_w - start_w,
            "height": crop_h,
        }

        while True:
            # Capture only the necessary region
            img = np.array(sct.grab(roi))
            img_bgr_cropped = img[:, :, :3]  # Fast BGRA to BGR

            # Color Detection
            hsv = cv2.cvtColor(img_bgr_cropped, cv2.COLOR_BGR2HSV)
            mask_yellow = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)
            mask_green = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)

            x_yellow = get_center_x(mask_yellow)
            x_green = get_center_x(mask_green)

            # Logic flow
            if x_yellow is not None and x_green is not None:
                print("Bars detected! Saving verification screenshot...")

                filename = "test_crop_verification.png"
                cv2.imwrite(IMAGE_DIR / filename, img_bgr_cropped)
                print(f"Saved {filename} to {IMAGE_DIR}")

                print("Pressing 'Esc' to cancel minigame.")
                pyautogui.press("esc")

                print("Exiting test script.")
                sys.exit(0)

            else:
                print("Bars not found. Pressing 'F'...")
                pyautogui.press("f")
                time.sleep(2)


if __name__ == "__main__":
    run_test()
