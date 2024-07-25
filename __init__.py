# Author: ungodlyaura
# Send bug reports or feature requests on the GitHub: https://github.com/ungodlyaura/AnkiAnnoyer
print("starting1")
from aqt import mw
import os
import time
import sys
sys.path.insert(0,os.path.dirname(os.path.realpath(__file__)))
import keyboard
# from PyQt5 import QtCore, QtGui, QtWidgets, QtTest

# import aqt.qt as qt
from aqt.qt import QLabel, QVBoxLayout, QFont, QCoreApplication, QApplication, QWidget, Qt
print("starting2")


# Timing
time_limit = 12  # seconds
answer_cooldown = 6  # seconds
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


answer_showing = False
paused = True


def on_key_event(e):
    global answer_showing, paused
    if e.scan_code in range(2, 12):  # Remove "in range(2,12)" to allow normal numbers
        return False
    if keyboard.is_pressed(rate_again_keybind):
        print("rate again")
        answer_showing = False
        rateCard(1)
    if keyboard.is_pressed(rate_bad_keybind):
        print("rate bad")
        answer_showing = False
        rateCard(2)
    if keyboard.is_pressed(rate_good_keybind):
        print("rate good")
        answer_showing = False
        rateCard(3)
    if keyboard.is_pressed(rate_easy_keybind):
        print("rate easy")
        answer_showing = False
        rateCard(4)
    if keyboard.is_pressed(undo_answer_keybind):
        print("undo answer")
        answer_showing = False
        undoAnswer()
    if keyboard.is_pressed(show_answer_keybind):
        print("show answer")
        answer_showing = True
        showAnswer()


keyboard.hook(on_key_event)

answer_current_text = "None"
question_current_text = "None"


class AnkiWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.text_widget = QLabel("", self)
        self.text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.text_widget)

        self.question_text_widget = QLabel("", self)
        self.question_text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.question_text_widget)

        self.showFullScreen()
        self.update_text()

    def update_text(self):
        global question_current_text, text_color, text_size, answer_showing

        screen = self.screen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()

        font_size = int(min(screen_width * text_size / (len(question_current_text)), 450))
        font = QFont("BIZ UDGothic", font_size)
        self.text_widget.setFont(font)
        self.text_widget.setText(question_current_text)
        self.text_widget.setStyleSheet(f"color: {text_color}; background: transparent;")

        font_size_question = int(min(screen_width * text_size / (len(answer_current_text)), 400))
        font_question = QFont("BIZ UDGothic", font_size_question)
        self.question_text_widget.setFont(font_question)
        self.question_text_widget.setText(answer_current_text)
        self.question_text_widget.setStyleSheet(f"color: {text_color}; background: transparent;")
        self.question_text_widget.setVisible(answer_showing)

    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)


def windowThing(window):
    global question_current_text, answer_showing
    startTime = time.time()
    current_text = question_current_text
    current_step = answer_showing

    while current_step == answer_showing and current_text == question_current_text and not paused:
        # qWait(100)
        now = time.time()
        fadeAmount = min((now - startTime) / time_limit, 1) ** 3
        if auto_show_answer and not answer_showing and now - startTime > auto_show_time:
            print("Auto showing answer")
            answer_showing = True
            showAnswer()
        elif auto_rate_again and answer_showing and current_step == True and now - startTime > auto_rate_time:
            print("Auto rate again")
            answer_showing = False
            rateCard(1)
        if answer_showing and instant_answer:
            window.set_opacity(1)
        else:
            window.set_opacity(fadeAmount)
        QCoreApplication.processEvents()

    window.set_opacity(0)

    if current_text != question_current_text:
        answer_showing = False


def main():
    global question_current_text

    app = QApplication([])
    window = AnkiWindow()

    while True:
        print("cooldown!")
        while paused:
            QCoreApplication.processEvents()
            pass
            # qWait(100)
        startTime = time.time()
        now = time.time()
        while not now - startTime > answer_cooldown and not answer_showing:
            QCoreApplication.processEvents()
            print(question_current_text)
            window.update_text()
            # qWait(100)
            now = time.time()
        if not answer_showing:
            windowThing(window)
        window.update_text()
        if answer_showing:
            windowThing(window)

    window.close()


main()
