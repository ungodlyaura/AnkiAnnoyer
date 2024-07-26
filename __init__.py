# Author: ungodlyaura
# Send bug reports or feature requests on the GitHub: https://github.com/ungodlyaura/AnkiAnnoyer

import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import keyboard
import time
from aqt import mw, gui_hooks
from aqt.qt import QLabel, QVBoxLayout, QFont, QCoreApplication, QWidget, Qt, pyqtSignal

# Timing
time_limit = 12  # seconds
answer_cooldown = 6  # seconds
auto_show_answer = True
auto_show_time = time_limit + 30  # seconds
auto_rate_again = True
auto_rate_time = 30

# Keybindings
'''
close_app_keybind = '-'  # Use + between combinations. Numbers are for num pad.
pause_app_keybind = '='
show_answer_keybind = '\''
rate_again_keybind = '['
rate_bad_keybind = ']'
rate_good_keybind = '\\'
rate_easy_keybind = ';'
undo_answer_keybind = '.'
'''
close_app_keybind = 'f21'  # Use + between combinations. Numbers are for num pad.
pause_app_keybind = 'f20'
show_answer_keybind = 'f14'
rate_again_keybind = 'f15'
rate_bad_keybind = 'f16'
rate_good_keybind = 'f17'
rate_easy_keybind = 'f18'
undo_answer_keybind = 'f19'
# Text Type
opacity_scale = 3  # 1 = linear | higher means exponential | recommend around 3
text_color = "red"
text_size = 5
text_size2 = 1
font_style = "BIZ UDGothic"
# Other
instant_answer = True  # True instantly show the answer | False fade the answer in
paused = False  # Is the addon paused upon loading?

##################################################################################################

cooldown = False
startTime = time.time()


def show_answer():
    # noinspection PyProtectedMember
    mw.reviewer._showAnswer()


def undo_answer():
    mw.undo()


def rate_card(ease):
    if mw.reviewer.state == "question":
        pass
        # noinspection PyProtectedMember
        mw.reviewer._showAnswer()
    # noinspection PyProtectedMember
    mw.reviewer._answerCard(ease)


def process_events():
    QCoreApplication.processEvents()


# Use for creating an invisible window object that displays text
class WindowObject(QWidget):
    update_text_signal = pyqtSignal()
    set_opacity_signal = pyqtSignal(float)
    process_events_signal = pyqtSignal()
    show_answer_signal = pyqtSignal()
    rate_signal = pyqtSignal(int)
    undo_signal = pyqtSignal()

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

        self.question_text_widget = QLabel("", self)
        self.question_text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.question_text_widget)

        self.answer_text_widget = QLabel("", self)
        self.answer_text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.answer_text_widget)

        self.showFullScreen()

        self.update_text_signal.connect(self.update_text)
        self.set_opacity_signal.connect(self.set_opacity)
        self.process_events_signal.connect(process_events)
        self.show_answer_signal.connect(show_answer)
        self.rate_signal.connect(rate_card)
        self.undo_signal.connect(undo_answer)

    def update_text(self):
        print("updating text")
        global text_color, text_size
        answer_current_text = "None"
        question_current_text = "None"

        if mw.reviewer.card and mw.reviewer.card.answer():
            answer_current_text = mw.reviewer.card.answer()
            question_current_text = mw.reviewer.card.question()

        screen = self.screen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()

        font_size = int(min(screen_width * text_size / (len(question_current_text)), 450))
        font = QFont(font_style, font_size)
        self.question_text_widget.setFont(font)
        self.question_text_widget.setText(question_current_text)
        self.question_text_widget.setStyleSheet(f"color: {text_color}; background: transparent;")

        font_size_question = int(min(screen_width * text_size2 / (len(answer_current_text)), 400))
        font_question = QFont(font_style, font_size_question)
        self.answer_text_widget.setFont(font_question)
        self.answer_text_widget.setText(answer_current_text)
        self.answer_text_widget.setStyleSheet(f"color: {text_color}; background: transparent;")
        if mw.reviewer.state == "question":
            self.question_text_widget.setVisible(True)
            self.answer_text_widget.setVisible(False)
        else:
            self.question_text_widget.setVisible(False)
            self.answer_text_widget.setVisible(True)

    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)


class BackgroundTask(threading.Thread):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.daemon = True

    def new_card(self):
        global startTime
        startTime = time.time()
        print("new card")
        self.window.update_text_signal.emit()
        while not cooldown and not paused:
            now = time.time()
            opacity = min((now - startTime) / time_limit, 1) ** opacity_scale
            # Emit signal to update opacity
            self.window.set_opacity_signal.emit(opacity)
            self.window.process_events_signal.emit()

            if mw.reviewer.state == "question" and auto_show_answer and now - startTime > auto_show_time:
                print("Auto showing answer")
                self.window.show_answer_signal.emit()
                startTime = time.time()
                self.window.update_text_signal.emit()
            elif mw.reviewer.state == "answer" and auto_rate_again and now - startTime > auto_rate_time:
                print("Auto rate again")
                self.window.rate_signal.emit(1)

            time.sleep(0.1)

    def run(self):
        global cooldown, paused

        while not paused:
            # Pause the script for the cooldown time
            print("cooldown")
            cooldown_start_time = time.time()
            while mw.reviewer.state != "answer" and not time.time() - cooldown_start_time > answer_cooldown:
                self.window.process_events_signal.emit()
                time.sleep(0.1)
            cooldown = False

            # If window_loop ending, it means new card.
            self.new_card()
            self.window.set_opacity_signal.emit(0)

        self.window.close()


def on_show_question(card):
    global startTime, cooldown
    print("question shown")
    cooldown = True


def on_show_answer(card):
    global startTime, instant_answer, time_limit
    print("answer shown")
    if instant_answer:
        startTime = startTime - time_limit
    else:
        startTime = time.time()


class Main:
    def on_key_event(self, e):
        global paused
        if not paused:
            if e.scan_code in range(2, 12):  # Remove "in range(2,12)" to allow normal numbers
                return False
            if keyboard.is_pressed(rate_again_keybind):
                print("rate again")
                self.window.rate_signal.emit(1)
            if keyboard.is_pressed(rate_bad_keybind):
                print("rate bad")
                self.window.rate_signal.emit(2)
            if keyboard.is_pressed(rate_good_keybind):
                print("rate good")
                self.window.rate_signal.emit(3)
            if keyboard.is_pressed(rate_easy_keybind):
                print("rate easy")
                self.window.rate_signal.emit(4)
            if keyboard.is_pressed(undo_answer_keybind):
                print("undo answer")
                self.window.undo_signal.emit()
            if keyboard.is_pressed(show_answer_keybind):
                print("show answer")
                self.window.show_answer_signal.emit()

    def __init__(self):
        print("running main")
        # Make the window object (that displays text on screen)
        self.window = WindowObject()
        # Use keyboard's hook for capturing key's globally
        keyboard.hook(self.on_key_event)
        background_task = BackgroundTask(self.window)
        background_task.start()


gui_hooks.reviewer_did_show_question.append(on_show_question)
gui_hooks.reviewer_did_show_answer.append(on_show_answer)
Main()
