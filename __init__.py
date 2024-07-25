# Author: ungodlyaura
# Send bug reports or feature requests on the GitHub: https://github.com/ungodlyaura/AnkiAnnoyer

from aqt import mw
import os
import time

try:
    import keyboard
except ImportError:
    os.system('python -m pip install keyboard')
import keyboard

try:
    from PyQt5 import QtCore, QtGui, QtWidgets, QtTest
except ImportError:
    os.system('python -m pip install PyQt5')
from PyQt5 import QtCore, QtGui, QtWidgets, QtTest

qWait = QtTest.QTest.qWait

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


def showAnswer():
    mw.reviewer._showAnswer()


def undoAnswer():
    mw.undo()


def rateCard(ease):
    mw.reviewer.card.answer(ease)


running = True
answer_showing = False
paused = False


def on_key_event(e):
    global running, answer_showing, paused
    if e.scan_code in range(2, 12):  # Remove "in range(2,12)" to allow normal numbers
        return False
    if keyboard.is_pressed(rate_again_keybind):
        answer_showing = False
        rateCard(1)
    if keyboard.is_pressed(rate_bad_keybind):
        answer_showing = False
        rateCard(2)
    if keyboard.is_pressed(rate_good_keybind):
        answer_showing = False
        rateCard(3)
    if keyboard.is_pressed(rate_easy_keybind):
        answer_showing = False
        rateCard(4)
    if keyboard.is_pressed(undo_answer_keybind):
        answer_showing = False
        undoAnswer()
    if keyboard.is_pressed(show_answer_keybind):
        answer_showing = True
        showAnswer()


keyboard.hook(on_key_event)

answer_current_text = "None"
question_current_text = "None"


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

    def update_text(self):
        global question_current_text, text_color, text_size, answer_showing

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
        self.question_text_widget.setVisible(answer_showing)

    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)


async def windowThing(window):
    global question_current_text, answer_showing
    startTime = time.time()
    current_text = question_current_text
    current_step = answer_showing

    while current_step == answer_showing and current_text == question_current_text and running and not paused:
        qWait(100)
        now = time.time()
        fadeAmount = min((now - startTime) / time_limit, 1) ** 3
        if auto_show_answer and not answer_showing and now - startTime > auto_show_time:
            answer_showing = True
            showAnswer()
        elif auto_rate_again and answer_showing and current_step == True and now - startTime > auto_rate_time:
            answer_showing = False
            rateCard(1)
        if answer_showing and instant_answer:
            window.set_opacity(1)
        else:
            window.set_opacity(fadeAmount)
        QtCore.QCoreApplication.processEvents()

    window.set_opacity(0)

    if current_text != question_current_text:
        answer_showing = False


def main():
    global question_current_text

    app = QtWidgets.QApplication([])
    window = AnkiWindow()

    while running:
        while paused:
            qWait(100)
        startTime = time.time()
        now = time.time()
        while not now - startTime > answer_cooldown and running and not answer_showing:
            window.update_text()
            qWait(100)
            now = time.time()
        if not answer_showing:
            windowThing(window)
        window.update_text()
        if answer_showing:
            windowThing(window)

    window.close()


if __name__ == "__main__":
    main()
