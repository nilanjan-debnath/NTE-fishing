import time

import pyautogui

# Always keep this True so you can jam your mouse to the corner to abort!
pyautogui.FAILSAFE = True

actions = [
    {"type": "keyboard", "button": "q"},
    {"type": "mouse", "button": "left", "coordinates": (125, 414)},
    {"type": "mouse", "button": "left", "coordinates": (780, 825)},
    {"type": "mouse", "button": "left", "coordinates": (891, 619)},
    {"type": "mouse", "button": "left", "coordinates": (1154, 680)},
    {"type": "keyboard", "button": "esc"},
    {"type": "keyboard", "button": "r"},
    {"type": "mouse", "button": "left", "coordinates": (409, 192)},
    {"type": "mouse", "button": "left", "coordinates": (1390, 809)},
    {"type": "mouse", "button": "left", "coordinates": (1228, 859)},
    {"type": "mouse", "button": "left", "coordinates": (959, 634)},
    {"type": "mouse", "button": "left", "coordinates": (947, 701)},
    {"type": "keyboard", "button": "esc"},
]


def mouse_click(button: str, coordinates: tuple):
    pyautogui.moveTo(coordinates[0], coordinates[1], duration=0.2)
    if button == "left":
        pyautogui.click()
    else:
        pyautogui.rightClick()
    time.sleep(0.5)


def keyboard_type(button: str):
    pyautogui.press(button)
    time.sleep(0.5)


def run_macro():
    time.sleep(3)
    mouse_click("left", (100, 100))

    for action in actions:
        if action["type"] == "mouse":
            mouse_click(button=action["button"], coordinates=action["coordinates"])
        else:
            keyboard_type(button=action["button"])


if __name__ == "__main__":
    print("Starting macro in 3 seconds... Switch to your target window!")
    time.sleep(3)
    run_macro()
