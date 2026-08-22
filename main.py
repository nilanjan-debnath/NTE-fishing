import threading
import time

import cv2
import mss
import numpy as np
import pyautogui

# Import shared variables and functions
from utils import (
    CROP_H_PERCENT,
    KEY_PRESS_DELAY,
    LOOP_LIMIT,
    LOWER_GREEN,
    LOWER_YELLOW,
    PARTITION_PERCENT,
    SCREEN_CAPTURE_DELAY,
    UPPER_GREEN,
    UPPER_YELLOW,
    get_center_x,
)

pyautogui.FAILSAFE = True


class BotState:
    def __init__(self):
        self.lock = threading.Lock()
        self.action = None  
        self.presses_left = 0  
        self.is_running = True
        self.loops_remaining = LOOP_LIMIT


bot_state = BotState()


def action_worker():
    """Thread 2: Executes keystrokes and can be interrupted mid-sequence."""
    while bot_state.is_running:
        action_to_take = None

        with bot_state.lock:
            if bot_state.presses_left > 0:
                action_to_take = bot_state.action
                bot_state.presses_left -= 1

        if action_to_take == "a":
            pyautogui.press("a")
            time.sleep(KEY_PRESS_DELAY)
        elif action_to_take == "d":
            pyautogui.press("d")
            time.sleep(KEY_PRESS_DELAY)
        elif action_to_take == "recast":
            print("[Action] Bars lost. Starting 1s wait/recast sequence...")
            time.sleep(1)
            pyautogui.press("f")
            print("[Action] Recast complete. Resuming tracking.")

            with bot_state.lock:
                bot_state.action = None
                bot_state.presses_left = 0
        else:
            time.sleep(0.01)


def vision_worker():
    """Thread 1: Captures screen, calculates logic, and overwrites commands."""
    print("Starting Vision Thread in 3 seconds... Switch to game!")
    time.sleep(3)

    in_minigame = False

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        
        # --- OPTIMIZATION: Pre-calculate the bounding box outside the loop ---
        w, h = monitor["width"], monitor["height"]
        crop_h = int(h * CROP_H_PERCENT)
        start_w = int(w * PARTITION_PERCENT / 100)
        end_w = int(w * (100 - PARTITION_PERCENT) / 100)
        active_width = end_w - start_w
        
        roi = {
            "top": monitor["top"],
            "left": monitor["left"] + start_w,
            "width": active_width,
            "height": crop_h
        }

        while bot_state.is_running:
            # OPTIMIZATION: Only grab the specific Region of Interest (ROI)
            img = np.array(sct.grab(roi))
            
            # OPTIMIZATION: Drop the Alpha channel using array slicing (faster than cv2.cvtColor)
            img_bgr_cropped = img[:, :, :3]

            hsv = cv2.cvtColor(img_bgr_cropped, cv2.COLOR_BGR2HSV)
            mask_yellow = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)
            mask_green = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)

            x_yellow = get_center_x(mask_yellow)
            x_green = get_center_x(mask_green)

            with bot_state.lock:
                if x_yellow is not None and x_green is not None:
                    if not in_minigame:
                        in_minigame = True
                        if bot_state.loops_remaining > 0:
                            bot_state.loops_remaining -= 1
                            print(f"[Vision] Minigame started! Remaining catches: {bot_state.loops_remaining}")

                    distance = abs(x_yellow - x_green)
                    num_presses = max(1, round((distance / active_width) * 15))

                    bot_state.action = "d" if x_yellow < x_green else "a"
                    bot_state.presses_left = num_presses

                else:
                    if in_minigame:
                        in_minigame = False
                        if bot_state.loops_remaining == 0:
                            print("[Vision] Loop limit reached. Shutting down bot...")
                            bot_state.is_running = False
                            break

                    if bot_state.action != "recast" and bot_state.is_running:
                        bot_state.action = "recast"
                        bot_state.presses_left = 1

            time.sleep(SCREEN_CAPTURE_DELAY)


if __name__ == "__main__":
    action_thread = threading.Thread(target=action_worker, daemon=True)
    action_thread.start()

    vision_worker()
    print("Program exited cleanly.")
