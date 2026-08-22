import threading
import time

import cv2
import mss
import numpy as np
import pyautogui

pyautogui.FAILSAFE = True

# --- HSV Constants ---
LOWER_YELLOW = np.array([20, 100, 100])
UPPER_YELLOW = np.array([40, 255, 255])
LOWER_GREEN = np.array([45, 100, 100])
UPPER_GREEN = np.array([85, 255, 255])


# --- Shared State Object ---
class BotState:
    def __init__(self):
        self.lock = threading.Lock()
        self.action = None  # 'a', 'd', 'recast', or None
        self.presses_left = 0  # How many more times to press


bot_state = BotState()


def get_center_x(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest)
        if M["m00"] != 0:
            return int(M["m10"] / M["m00"])
    return None


def action_worker():
    """Thread 2: Executes keystrokes and can be interrupted mid-sequence."""
    while True:
        action_to_take = None

        # 1. Safely read the current command from the Vision Thread
        with bot_state.lock:
            if bot_state.presses_left > 0:
                action_to_take = bot_state.action
                # Consume one press (or the whole recast flag)
                bot_state.presses_left -= 1

        # 2. Execute the action
        if action_to_take == "a":
            pyautogui.press("a")
            time.sleep(0.01)  # Tiny delay for the game to register
        elif action_to_take == "d":
            pyautogui.press("d")
            time.sleep(0.01)
        elif action_to_take == "recast":
            print("[Action] Bars lost. Starting 1s wait/recast sequence...")
            time.sleep(1)
            pyautogui.press("f")
            print("[Action] Recast complete. Resuming tracking.")
            # Clear state just in case vision queued up junk during the wait
            with bot_state.lock:
                bot_state.action = None
                bot_state.presses_left = 0
        else:
            time.sleep(0.01)  # Idle sleep to prevent maxing out the CPU


def vision_worker():
    """Thread 1: Captures screen, calculates logic, and overwrites commands."""
    print("Starting Vision Thread in 3 seconds... Switch to game!")
    time.sleep(3)

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        while True:
            # 1. Capture and crop (using your optimized partition math)
            img = np.array(sct.grab(monitor))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            h, w = img_bgr.shape[:2]
            crop_h = int(h * 0.25)
            partition = 31
            start_w = int(w * partition / 100)
            end_w = int(w * (100 - partition) / 100)
            img_bgr_cropped = img_bgr[0:crop_h, start_w:end_w]

            active_width = end_w - start_w

            # 2. Color Detection
            hsv = cv2.cvtColor(img_bgr_cropped, cv2.COLOR_BGR2HSV)
            mask_yellow = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)
            mask_green = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)

            x_yellow = get_center_x(mask_yellow)
            x_green = get_center_x(mask_green)

            # 3. Logic & Thread Communication
            with bot_state.lock:
                if x_yellow is not None and x_green is not None:
                    # Found bars! Calculate distance and overwrite command
                    distance = abs(x_yellow - x_green)
                    num_presses = max(1, round((distance / active_width) * 15))

                    bot_state.action = "d" if x_yellow < x_green else "a"
                    # THIS is where the interruption happens.
                    # If Action Thread was doing 10 'a's, it is now instantly doing 'd's.
                    bot_state.presses_left = num_presses

                else:
                    # No bars found. Trigger recast sequence if not already running.
                    if bot_state.action != "recast":
                        bot_state.action = "recast"
                        bot_state.presses_left = 1

            # Cap vision loop to ~20 FPS so we don't cook your CPU
            time.sleep(0.05)


if __name__ == "__main__":
    # Start the Action thread in the background
    action_thread = threading.Thread(target=action_worker, daemon=True)
    action_thread.start()

    # Run the Vision thread on the main process
    vision_worker()
