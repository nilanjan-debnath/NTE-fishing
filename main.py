import threading
import time

import cv2
import mss
import numpy as np
import pyautogui
from pynput import keyboard

from sell_and_buy import run_macro
from utils import (
    AUTO_SELL_AND_BUY,
    CROP_H_PERCENT,
    LOOP_LIMIT,
    LOWER_GREEN,
    LOWER_YELLOW,
    MAX_HOLD_SECONDS,
    PARTITION_PERCENT,
    SCREEN_CAPTURE_DELAY,
    SELL_AND_BUY_AFTER,
    UPPER_GREEN,
    UPPER_YELLOW,
    get_x_coords,
)

pyautogui.FAILSAFE = True


class BotState:
    def __init__(self):
        self.lock = threading.Lock()
        self.action = None  # 'a', 'd', 'recast', or None
        self.action_end_time = 0.0  # Timestamp of when to release the key
        self.is_running = True
        self.loop_limit = LOOP_LIMIT
        self.loop_count = 0
        self.auto_sell_and_buy = AUTO_SELL_AND_BUY
        self.sell_and_buy_after = SELL_AND_BUY_AFTER

    def loop_remains(self) -> int:
        if self.loop_limit > 0:
            return self.loop_limit - self.loop_count
        else:
            print("Script running without any limit")
            return 99999

    def should_sell_and_buy(self):
        if self.auto_sell_and_buy:
            return self.loop_count % self.sell_and_buy_after == 0
        return False


bot_state = BotState()


def trigger_kill_switch():
    """Callback function when Shift+Esc is pressed via pynput."""
    print("\n[Kill Switch] 'Shift + Esc' detected! Shutting down immediately...")
    bot_state.is_running = False


def action_worker():
    """Thread 2: Manages interruptible time-based key holds."""
    current_held_key = None

    while bot_state.is_running:
        with bot_state.lock:
            action_to_take = bot_state.action
            end_time = bot_state.action_end_time

        if action_to_take in ("a", "d"):
            # Check if we still have time on the clock to hold this key
            if time.time() < end_time:
                # If we need to press a new key, let go of the old one first
                if current_held_key != action_to_take:
                    if current_held_key:
                        pyautogui.keyUp(current_held_key)
                    pyautogui.keyDown(action_to_take)
                    current_held_key = action_to_take
            else:
                # Time expired! Release the key.
                if current_held_key:
                    pyautogui.keyUp(current_held_key)
                    current_held_key = None

                # Clear the action state so we don't keep evaluating it
                with bot_state.lock:
                    if bot_state.action == action_to_take:
                        bot_state.action = None

            time.sleep(0.01)

        elif action_to_take == "recast":
            if current_held_key:
                pyautogui.keyUp(current_held_key)
                current_held_key = None

            print("[Action] Bars lost. Starting 1s wait/recast sequence...")
            time.sleep(1)
            pyautogui.press("f")
            print("[Action] Recast complete. Resuming tracking.")

            with bot_state.lock:
                bot_state.action = None

        else:
            # Action is None (centered or waiting)
            if current_held_key:
                pyautogui.keyUp(current_held_key)
                current_held_key = None

            time.sleep(0.01)

    # --- Failsafe: Ensure keys are released when shutting down ---
    if current_held_key:
        pyautogui.keyUp(current_held_key)


def vision_worker():
    """Thread 1: Captures screen and calculates hold times."""
    print("Starting Vision Thread in 3 seconds... Switch to game!")
    time.sleep(3)

    in_minigame = False

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        w, h = monitor["width"], monitor["height"]
        crop_h = int(h * CROP_H_PERCENT)
        start_w = int(w * PARTITION_PERCENT / 100)
        end_w = int(w * (100 - PARTITION_PERCENT) / 100)
        active_width = end_w - start_w

        # deadzone_threshold = active_width * 0.02

        roi = {
            "top": monitor["top"],
            "left": monitor["left"] + start_w,
            "width": active_width,
            "height": crop_h,
        }

        while bot_state.is_running:
            img = np.array(sct.grab(roi))
            img_bgr_cropped = img[:, :, :3]

            hsv = cv2.cvtColor(img_bgr_cropped, cv2.COLOR_BGR2HSV)
            mask_yellow = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)
            mask_green = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)

            c_yellow, _, _ = get_x_coords(mask_yellow)
            c_green, l_green, r_green = get_x_coords(mask_green)

            with bot_state.lock:
                if (
                    c_yellow is not None
                    and c_green is not None
                    and l_green is not None
                    and r_green is not None
                ):
                    if c_yellow >= l_green and c_yellow <= r_green:
                        bot_state.action = None  # We are perfectly inside, do nothing
                    if not in_minigame:
                        in_minigame = True
                        print(f"Total catches until now {bot_state.loop_count}")
                        bot_state.loop_count += 1
                        if bot_state.loop_limit > 0:
                            print(
                                f"[Vision] Minigame started! Remaining catches: {bot_state.loop_remains()}"
                            )

                    distance = (
                        abs(c_yellow - l_green)
                        if c_yellow < c_green
                        else abs(c_yellow - r_green)
                    )

                    # NEW: Calculate hold duration instead of presses
                    distance_ratio = distance / active_width
                    hold_duration = distance_ratio * MAX_HOLD_SECONDS

                    # Set a minimum hold time (e.g., 0.02s) so very tiny corrections still register in-game
                    hold_duration = max(0.01, hold_duration)

                    bot_state.action = "d" if c_yellow < c_green else "a"
                    # Set the exact timestamp for when this action should expire
                    bot_state.action_end_time = time.time() + hold_duration

                else:
                    if in_minigame:
                        in_minigame = False
                        if bot_state.should_sell_and_buy():
                            run_macro()

                        if bot_state.loop_remains() == 0:
                            print("[Vision] Loop limit reached. Shutting down bot...")
                            bot_state.is_running = False
                            break

                    if bot_state.action != "recast" and bot_state.is_running:
                        bot_state.action = "recast"

            time.sleep(SCREEN_CAPTURE_DELAY)


if __name__ == "__main__":
    hotkey_listener = keyboard.GlobalHotKeys({"<shift>+<esc>": trigger_kill_switch})
    hotkey_listener.start()

    print("Kill switch active: Press 'Shift + Esc' at any time to exit.")

    action_thread = threading.Thread(target=action_worker, daemon=True)
    action_thread.start()

    vision_worker()
    print("Program exited cleanly.")
