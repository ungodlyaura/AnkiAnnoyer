import threading
import PySimpleGUI as sg
import keyboard
import time
import requests
from glom import glom


# Timing
time_limit = 300 # seconds
answer_cooldown = 300 # seconds
# Keybinds
close_app_keybind = 'ctrl+shift+.'
show_answer_keybind = '0'
rate_again_keybind = '1'
rate_bad_keybind = '2'
rate_good_keybind = '3'
rate_easy_keybind = '4'
undo_answer_keybind = '5'
# Text Type
text_color = "white"
text_length_multiplier = 2 # 1 for english 2 for japanese
text_length_multiplier2 = 1 # for showing the answer
# Pathway
question_pathway = 'result.fields.keyword.value' # change this to the pathway of your deck's question and below one to the answer
answer_pathway = 'result.fields.kanji.value'

# TODO keybind to pause/unpause the script


ANKI_URL = "http://localhost:8765"

def getCurrentCard():
    payload = {
        "action": "guiCurrentCard",
        "version": 5
    }
    r = requests.post(ANKI_URL, json=payload)

    return r.json()

def showAnswer():
    payload = {
        "action": "guiShowAnswer",
        "version": 5
    }
    r = requests.post(ANKI_URL, json=payload)

    return r.json()

def undoAnswer():
    payload = {
        "action": "guiUndo",
        "version": 5
    }
    r = requests.post(ANKI_URL, json=payload)

    return r.json()

def rateCard(rate):
    payload = {
        "action": "guiAnswerCard",
        "version": 5,
        "params": {
            "ease": rate
        }
    }
    r = requests.post(ANKI_URL, json=payload)

    return r.json()


# key hook to listen for ctrl+shift+.
class KeyWatcher:
    def __init__(self):
        self.running = True
        self.answer_showing = False

    def on_key_event(self, e):
        if e.scan_code in range(2, 11): 
            return False
        if keyboard.is_pressed(close_app_keybind):
            print("Stopping app!")
            self.running = False
        if keyboard.is_pressed(rate_again_keybind):
            print("rate again")
            self.answer_showing = False
            rateCard(1)
            getNewText()
        if keyboard.is_pressed(rate_bad_keybind):
            print("rate bad")
            self.answer_showing = False
            rateCard(2)
            getNewText()
        if keyboard.is_pressed(rate_good_keybind):
            print("rate good")
            self.answer_showing = False
            rateCard(3)
            getNewText()
        if keyboard.is_pressed(rate_easy_keybind):
            print("rate easy")
            self.answer_showing = False
            rateCard(4)
            getNewText()
        if keyboard.is_pressed(undo_answer_keybind):
            print("undo answer")
            self.answer_showing = False
            undoAnswer()
            getNewText()
        if keyboard.is_pressed(show_answer_keybind):
            print("show answer")
            self.answer_showing = True
            showAnswer()
            getNewText()

    def start_watching(self):
        keyboard.hook(self.on_key_event)


# Create an instance of KeyWatcher
key_watcher = KeyWatcher()

# Create a thread to run the key watcher
key_watcher_thread = threading.Thread(target=key_watcher.start_watching)

# Start the thread
key_watcher_thread.start()


current_text = glom(getCurrentCard(),question_pathway)


def getNewText():
    global current_text
    if key_watcher.answer_showing:
        current_text = glom(getCurrentCard(),answer_pathway)
    else:
        current_text = glom(getCurrentCard(),question_pathway)


# create a new window with updated text
def updateWindow():
    global text_color
    print(current_text)
    
    if key_watcher.answer_showing:
        font_size = int(min(1920 / (len(current_text)*text_length_multiplier2), 450))
        layout = [
            [
                sg.Text(
                    glom(getCurrentCard(),question_pathway),
                    size=len(current_text)*text_length_multiplier2,
                    background_color="green",
                    text_color=text_color,
                    expand_x=True,
                    expand_y=True,
                    font=("BIZ UDGothic", font_size,  "")
                )
            ],
            [
                sg.Text(
                    current_text,
                    size=len(current_text)*text_length_multiplier2,
                    background_color="green",
                    text_color=text_color,
                    expand_x=True,
                    expand_y=True,
                    font=("BIZ UDGothic", font_size,  "")
                )
            ]
        ]
    else:
        font_size = int(min(1920 / (len(current_text)*text_length_multiplier), 450))
        layout = [
            [
                sg.Text(
                    current_text,
                    size=len(current_text)*text_length_multiplier,
                    background_color="green",
                    text_color=text_color,
                    expand_x=True,
                    expand_y=True,
                    font=("BIZ UDGothic", font_size,  "")
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



def windowThing():
    global current_text
    last_text = current_text
    window = updateWindow() # get new window
    startTime = time.time()

    while current_text == last_text and key_watcher.running:
        window.read(timeout=10)
        now = time.time()
        fadeAmount = min((now - startTime) / time_limit, 1)
        window.set_alpha(fadeAmount)
    window.close() #close the window

    return current_text



#checks if ctrl + shift + . has been called
while key_watcher.running:
    print("cooldown!")
    temp_time = answer_cooldown*10
    while temp_time > 0 and key_watcher.running:
        temp_time += -1
        time.sleep(0.1)

    print("annoying time!")
    current_text = windowThing()
    if key_watcher.answer_showing:
        current_text = windowThing()



