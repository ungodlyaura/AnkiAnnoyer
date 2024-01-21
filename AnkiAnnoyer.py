import threading
import PySimpleGUI as sg
import keyboard
import time
import requests


text_length_multiplier = 2 # 1 for english 2 for japanese
time_limit = 2400 # seconds but /2 for some reason
answer_cooldown = 120 # seconds
close_keybind = 'ctrl+shift+.'

ANKI_URL = "http://localhost:8765"

def getCurrentCard():
    payload = {
        "action": "guiCurrentCard",
        "version": 5
    }
    r = requests.post(ANKI_URL, json=payload)

    return r.json()


# key hook to listen for ctrl+shift+.
class KeyWatcher:
    def __init__(self):
        self.running = True

    def on_key_event(self, e):
        if keyboard.is_pressed(close_keybind):
            print("Ctrl + Shift + Full Stop pressed!")
            self.running = False

    def start_watching(self):
        keyboard.hook(self.on_key_event)


# Create an instance of KeyWatcher
key_watcher = KeyWatcher()

# Create a thread to run the key watcher
key_watcher_thread = threading.Thread(target=key_watcher.start_watching)

# Start the thread
key_watcher_thread.start()


currentText = getCurrentCard()["result"]["fields"]["keyword"]["value"]



# create a new window with updated text
def updateWindow():
    print(currentText)
    layout = [
        [
            sg.Text(
                currentText,
                size=len(currentText)*text_length_multiplier,
                background_color="green",
                text_color="white",
                expand_x=True,
                expand_y=True,
                font=("BIZ UDGothic", 450 - (len(currentText)*10),  "")
            )
        ]
    ]

    window = sg.Window(
        "Window Title",
        layout,
        transparent_color="green",
        keep_on_top=True,
        no_titlebar=True,
        background_color="green",
        alpha_channel=0
    )
    return window





#checks if ctrl + shift + . has been called
while key_watcher.running:
    lastKanji = currentText

    print("cooldown!")
    time.sleep(answer_cooldown)
    print("annoying time!")
    startTime = time.time()

    window = updateWindow() # get new window
    while currentText == lastKanji and key_watcher.running:
        event, values = window.read(timeout=10)
        now = time.time()
        fadeAmount = min((now - startTime) / time_limit, 1)
        window.set_alpha(fadeAmount)

        currentText = getCurrentCard()["result"]["fields"]["keyword"]["value"]
    
    window.close() #close the window


