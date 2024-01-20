import threading
import PySimpleGUI as sg
import keyboard
import time
import requests
# import math

textLengthMultiplier = 2
maxTime = 120
ANKI_URL = "http://localhost:8765"

def getCurrentCard():
    payload = {
        "action": "guiCurrentCard",
        "version": 5
    }
    r = requests.post(ANKI_URL, json=payload)

    return r.json()


class KeyWatcher:
    def __init__(self):
        self.running = True

    def on_key_event(self, e):
        if keyboard.is_pressed('ctrl+shift+.'):
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


currentCard = getCurrentCard()
# print(currentCard)
currentKanji = currentCard["result"]["fields"]["keyword"]["value"]
# print(currentCard)

layout = [
    [
        sg.Text(
            currentKanji,
            size=len(currentKanji)*textLengthMultiplier,
            background_color="green",
            text_color="white",
            expand_x=True,
            expand_y=True,
            font=("BIZ UDGothic", 150,  "")
        )
    ],
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

startTime = time.time()
while key_watcher.running:
    event, values = window.read(timeout=10)
    now = time.time()
    fadeAmount = min((now - startTime) / maxTime, 1)
    window.set_alpha(fadeAmount)
    # print(event, values)

window.close()
