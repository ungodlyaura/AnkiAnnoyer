import os
import asyncio
import time

try:
    import aiohttp
except ImportError:
    print("Trying to install aiohttp")
    os.system('python -m pip install aiohttp')
import aiohttp

try:
    from glom import glom
except ImportError:
    print("Trying to install glom")
    os.system('python -m pip install glom')
from glom import glom

try:
    from PyQt5 import QtCore, QtGui, QtWidgets, QtTest
except ImportError:
    print("Trying to install PyQt5")
    os.system('python -m pip install PyQt5')
from PyQt5 import QtCore, QtGui, QtWidgets, QtTest
qWait = QtTest.QTest.qWait

try:
    import keyboard
except ImportError:
    print("Trying to install keyboard")
    os.system('python -m pip install keyboard')
import keyboard

# Timing
time_limit = 120  # seconds
answer_cooldown = 60  # seconds
auto_show_answer = True
auto_show_time = time_limit + 30  # seconds
auto_rate_again = True
auto_rate_time = 30
# Keybindings
#close_app_keybind = '-'  # Use + between combinations. Numbers are for num pad.
#pause_app_keybind = '='
#show_answer_keybind = '\''
#rate_again_keybind = '['
#rate_bad_keybind = ']'
#rate_good_keybind = '\\'
#rate_easy_keybind = ';'
#undo_answer_keybind = '.'
close_app_keybind = 'f21'  # Use + between combinations. Numbers are for num pad.
pause_app_keybind = 'f20'
show_answer_keybind = 'f14'
rate_again_keybind = 'f15'
rate_bad_keybind = 'f16'
rate_good_keybind = 'f17'
rate_easy_keybind = 'f18'
undo_answer_keybind = 'f19'
# Text Type
text_color = "red"
text_size = 1
# Pathway
question_value = 'keyword'  # edit any card and place the field value you want as question/answer (cap sensitive)
answer_value = 'kanji'
# Other
instant_answer = True  # True instantly show the answer, False fade the answer in over time

ANKI_URL = "http://localhost:8765"


async def async_post(url, json):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json) as response:
            return await response.json()

async def getCurrentCard():
    payload = {
        "action": "guiCurrentCard",
        "version": 5
    }
    return await async_post(ANKI_URL, payload)

async def showAnswer():
    payload = {
        "action": "guiShowAnswer",
        "version": 5
    }
    return await async_post(ANKI_URL, payload)

async def undoAnswer():
    payload = {
        "action": "guiUndo",
        "version": 5
    }
    return await async_post(ANKI_URL, payload)

async def rateCard(rate):
    payload = {
        "action": "guiAnswerCard",
        "version": 5,
        "params": {
            "ease": rate
        }
    }
    return await async_post(ANKI_URL, payload)

answer_current_text = "None"
question_current_text = "None"

async def getNewText():
    global answer_current_text, question_current_text
    try:
        card_data = await getCurrentCard()
        answer_current_text = glom(card_data, 'result.fields.' + answer_value + '.value')
        question_current_text = glom(card_data, 'result.fields.' + question_value + '.value')
    except:
        answer_current_text = "No Card"
        question_current_text = "No Card"


class KeyWatcher:
    def __init__(self):
        self.running = True
        self.answer_showing = False
        self.paused = False

    async def update_text_loop(self):
        while self.running:
            await getNewText()
            await asyncio.sleep(1)

    def on_key_event(self, e):
        if e.scan_code in range(2, 12):  # Remove "in range(2,12)" to allow normal numbers
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
            asyncio.run(rateCard(1))
        if keyboard.is_pressed(rate_bad_keybind):
            print("rate bad")
            self.answer_showing = False
            asyncio.run(rateCard(2))
        if keyboard.is_pressed(rate_good_keybind):
            print("rate good")
            self.answer_showing = False
            asyncio.run(rateCard(3))
        if keyboard.is_pressed(rate_easy_keybind):
            print("rate easy")
            self.answer_showing = False
            asyncio.run(rateCard(4))
        if keyboard.is_pressed(undo_answer_keybind):
            print("undo answer")
            self.answer_showing = False
            asyncio.run(undoAnswer())
        if keyboard.is_pressed(show_answer_keybind):
            print("show answer")
            self.answer_showing = True
            asyncio.run(showAnswer())

    def start_watching(self):
        keyboard.hook(self.on_key_event)

key_watcher = KeyWatcher()

class AnkiWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowTransparentForInput
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.text_widget = QtWidgets.QLabel("", self)
        self.text_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.text_widget)

        self.question_text_widget = QtWidgets.QLabel("", self)
        self.question_text_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.question_text_widget)

        self.showFullScreen()
        self.update_text()
        self.set_opacity(0)

    def update_text(self):
        global question_current_text, text_color, key_watcher, text_size

        screen = self.screen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()

        font_size = int(min(screen_width * text_size / (len(question_current_text)), 450))
        font = QtGui.QFont("BIZ UDGothic", font_size)
        self.text_widget.setFont(font)
        self.text_widget.setText(question_current_text)
        self.text_widget.setStyleSheet(f"color: {text_color}; background: transparent;")

        font_size_question = int(min(screen_width * text_size / (len(answer_current_text)), 400))
        font_question = QtGui.QFont("BIZ UDGothic", font_size_question)
        self.question_text_widget.setFont(font_question)
        self.question_text_widget.setText(answer_current_text)
        self.question_text_widget.setStyleSheet(f"color: {text_color}; background: transparent;")
        self.question_text_widget.setVisible(key_watcher.answer_showing)

    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)


async def windowThing(window):
    global question_current_text
    startTime = time.time()
    current_text = question_current_text
    current_step = key_watcher.answer_showing

    while current_step == key_watcher.answer_showing and current_text == question_current_text and key_watcher.running and not key_watcher.paused:
        await asyncio.sleep(0.1)
        now = time.time()
        fadeAmount = min((now - startTime) / time_limit, 1) ** 3
        if auto_show_answer and not key_watcher.answer_showing and now - startTime > auto_show_time:
            print("Auto showing answer")
            key_watcher.answer_showing = True
            await showAnswer()
        elif auto_rate_again and key_watcher.answer_showing and current_step == True and now - startTime > auto_rate_time:
            print("Auto rate again")
            key_watcher.answer_showing = False
            await rateCard(1)
        if key_watcher.answer_showing and instant_answer:
            window.set_opacity(1)
        else:
            window.set_opacity(fadeAmount)
        QtCore.QCoreApplication.processEvents()

    window.set_opacity(0)

    if current_text != question_current_text:
        key_watcher.answer_showing = False


async def main():
    global question_current_text
    loop = asyncio.get_running_loop()
    asyncio.create_task(key_watcher.update_text_loop())
    loop.run_in_executor(None, key_watcher.start_watching)

    app = QtWidgets.QApplication([])
    window = AnkiWindow()

    viewing_card = True
    while True:
        try:
            card_data = await getCurrentCard()
            question_current_text = glom(card_data, 'result.fields.' + question_value + '.value')
            break
        except KeyboardInterrupt:
            break
        except:
            if viewing_card:
                viewing_card = False
                print("Start a studying session! \nSelected question value: " + question_value + " \nSelected answer value: " + answer_value)
            if not key_watcher.running:
                break
            await asyncio.sleep(0.1)
            QtCore.QCoreApplication.processEvents()

    while key_watcher.running:
        print("cooldown!")
        while key_watcher.paused:
            QtCore.QCoreApplication.processEvents()
            await asyncio.sleep(0.1)
        startTime = time.time()
        now = time.time()
        while not now - startTime > answer_cooldown and key_watcher.running and not key_watcher.answer_showing:
            QtCore.QCoreApplication.processEvents()
            window.update_text()
            await asyncio.sleep(0.1)
            now = time.time()
        if not key_watcher.answer_showing:
            print(question_current_text)
            await windowThing(window)
        window.update_text()
        if key_watcher.answer_showing:
            await windowThing(window)

    window.close()

asyncio.run(main())
