from pynput import keyboard

# Configuration for the keybind
keybind = '<f14>'

# Initialize sets to keep track of pressed keys
pressed_keys = set()
pressed_chars = set()


def on_press(key):

    # Add the pressed key to the appropriate set
    print(key.char())
    print(keyboard.HotKey.parse(keybind))
    pressed_keys.add(key)

    # Check if all keys in the keybind are pressed
    if all(k in pressed_keys for k in keybind):
        print("hello")


def on_release(key):
    # Remove the released key from the appropriate set
    pressed_keys.discard(key)


# Start listening to keyboard events
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
