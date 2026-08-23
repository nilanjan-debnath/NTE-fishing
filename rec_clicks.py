from pynput import keyboard, mouse


# --- Mouse Callback ---
def on_click(x, y, button, pressed):
    if pressed:
        print({"type": "mouse", "button": button.name, "coordinates": (int(x), int(y))})


# --- Keyboard Callback ---
def on_press(key):
    try:
        # Standard alphanumeric keys
        # print(f"Key pressed: '{key.char}'")
        print({"type": "keyboard", "button": key.char})
    except AttributeError:
        # Special keys (Space, Shift, Esc, etc.)
        # print(f"Special key pressed: {key.name}")
        print({"type": "keyboard", "button": key.name})


print("Listening for mouse clicks and keystrokes...")

# Start both listeners
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener = keyboard.Listener(on_press=on_press)

mouse_listener.start()
keyboard_listener.start()

# The main thread will wait here until the keyboard listener stops (when Esc is pressed)
keyboard_listener.join()

# Once the keyboard listener finishes, stop the mouse listener so the script can exit cleanly
mouse_listener.stop()
print("Exited cleanly.")
