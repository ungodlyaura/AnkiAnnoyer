import threading
import PySimpleGUI as sg
import keyboard
import time
import requests
from glom import glom

############################################

# Timing
time_limit = 60  # seconds
answer_cooldown = 30  # seconds
auto_show_answer = True
auto_show_time = time_limit + answer_cooldown  # seconds
auto_rate_again = True
auto_rate_time = 30
# Keybindings
close_app_keybind = 'ctrl+.'  # Don't use numpad '.'
pause_app_keybind = 'ctrl+/'
show_answer_keybind = '\''  # numbers are for numpad
rate_again_keybind = '['
rate_bad_keybind = ']'
rate_good_keybind = '\\'
rate_easy_keybind = ';'
undo_answer_keybind = 'ctrl+\''
# Text Type
text_color = "red"
text_length_multiplier = 2  # 1 for english 2 for japanese
text_length_multiplier2 = 1  # for showing the answer
# Pathway
question_pathway = 'result.fields.keyword.value'  # change this to the pathway of your deck's question and below one to the answer
answer_pathway = 'result.fields.kanji.value'
# Other
instant_answer = True  # True instantly show the answer, False fade the answer in over time

############################################

ANKI_URL = "http://localhost:8765"

#  TODO
#  don't destroy window, use same one to make faster
#  stop use of ankiconnect, make into addon


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
        self.paused = False

    def on_key_event(self, e):
        if e.scan_code in range(2,
                                12) or e.scan_code == 83:  # Remove "in range(2,12)" to allow normal numbers | Remove e.scan_code == 83 to allow numpad '.'
            return False
        if keyboard.is_pressed(close_app_keybind):
            print("Stopping app!")
            self.running = False
        if keyboard.is_pressed(pause_app_keybind):
            if self.paused:
                self.paused = False
                print("Continuing")
            else:
                self.paused = True
                print("Pausing")
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

current_text = None
while not current_text:
    try:
        current_text = glom(getCurrentCard(), question_pathway)
    except:
        pass


def getNewText():
    global current_text
    try:
        if key_watcher.answer_showing:
            current_text = glom(getCurrentCard(), answer_pathway)
        else:
            current_text = glom(getCurrentCard(), question_pathway)
    except:
        current_text = "no card"


def updateWindow():
    global text_color
    print(current_text)

    if key_watcher.answer_showing:
        font_size = int(min(1920 / (len(current_text) * text_length_multiplier2), 450))
        layout = [
            [
                sg.Text(
                    glom(getCurrentCard(), question_pathway),
                    size=len(current_text) * text_length_multiplier2,
                    background_color="green",
                    text_color=text_color,
                    expand_x=True,
                    expand_y=True,
                    font=("BIZ UDGothic", font_size, "")
                )
            ],
            [
                sg.Text(
                    current_text,
                    size=len(current_text) * text_length_multiplier2,
                    background_color="green",
                    text_color=text_color,
                    expand_x=True,
                    expand_y=True,
                    font=("BIZ UDGothic", font_size, "")
                )
            ]
        ]
    else:
        font_size = int(min(1920 / (len(current_text) * text_length_multiplier), 450))
        layout = [
            [
                sg.Text(
                    current_text,
                    size=len(current_text) * text_length_multiplier,
                    background_color="green",
                    text_color=text_color,
                    expand_x=True,
                    expand_y=True,
                    font=("BIZ UDGothic", font_size, "")
                )
            ]
        ]

    window = sg.Window(
        "Window Title",
        layout,
        use_default_focus=False,
        transparent_color="green",
        keep_on_top=True,
        no_titlebar=True,
        background_color="green",
        alpha_channel=0
    )

    window.FocusSet = False
    return window


def windowThing():
    global current_text
    last_text = current_text

    window = updateWindow()
    window.read(timeout=10)

    startTime = time.time()

    while current_text == last_text and key_watcher.running:
        now = time.time()
        fadeAmount = min((now - startTime) / time_limit, 1)
        getNewText()
        if auto_show_answer and not key_watcher.answer_showing and now - startTime > auto_show_time:
            key_watcher.answer_showing = True
            showAnswer()
            getNewText()
        elif auto_rate_again and key_watcher.answer_showing and now - startTime > auto_rate_time:
            key_watcher.answer_showing = False
            rateCard(1)
            getNewText()
        if key_watcher.answer_showing and instant_answer:
            window.set_alpha(1)
        else:
            window.set_alpha(fadeAmount)
        while key_watcher.paused:
            window.set_alpha(0)
            time.sleep(0.1)
    window.close()  # close the window

    return current_text


# checks if ctrl + shift + . has been called
while key_watcher.running:
    print("cooldown!")
    temp_time = answer_cooldown * 10
    while temp_time > 0 and key_watcher.running and not key_watcher.answer_showing:
        temp_time += -1
        time.sleep(0.1)
    if not key_watcher.answer_showing:
        current_text = windowThing()
    if key_watcher.answer_showing:
        current_text = windowThing()
