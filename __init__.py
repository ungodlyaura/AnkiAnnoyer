# Author: ungodlyaura
# Send bug reports or feature requests on the GitHub: https://github.com/ungodlyaura/AnkiAnnoyer

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import keyboard
import time
from aqt import mw, gui_hooks
from aqt.qt import QLabel, QVBoxLayout, QFont, QCoreApplication, QApplication, QWidget, Qt

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
text_size = 1
font_style = "BIZ UDGothic"
# Other
instant_answer = True  # True instantly show the answer | False fade the answer in


##################################################################################################

def show_answer():
    # noinspection PyProtectedMember
    mw.reviewer._showAnswer()


def undo_answer():
    mw.undo()


def rate_card(ease):
    if mw.reviewer.state == "question":
        # noinspection PyProtectedMember
        mw.reviewer._showAnswer()
    mw.reviewer.card.answer(ease)


paused = False
cooldown = False
startTime = time.time()


def on_key_event(e):
    global paused
    if not paused:
        if e.scan_code in range(2, 12):  # Remove "in range(2,12)" to allow normal numbers
            return False
        if keyboard.is_pressed(rate_again_keybind):
            print("rate again")
            rate_card(1)
        if keyboard.is_pressed(rate_bad_keybind):
            print("rate bad")
            rate_card(2)
        if keyboard.is_pressed(rate_good_keybind):
            print("rate good")
            rate_card(3)
        if keyboard.is_pressed(rate_easy_keybind):
            print("rate easy")
            rate_card(4)
        if keyboard.is_pressed(undo_answer_keybind):
            print("undo answer")
            undo_answer()
        if keyboard.is_pressed(show_answer_keybind):
            print("show answer")
            show_answer()


# Use keyboard's hook for capturing key's globally
keyboard.hook(on_key_event)


# Use for creating an invisible window object that displays text
class WindowObject(QWidget):
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
        global text_color, text_size
        answer_current_text = mw.reviewer.card.answer()
        question_current_text = mw.reviewer.card.question()
        screen = self.screen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()

        font_size = int(min(screen_width * text_size / (len(question_current_text)), 450))
        font = QFont(font_style, font_size)
        self.text_widget.setFont(font)
        self.text_widget.setText(question_current_text)
        self.text_widget.setStyleSheet(f"color: {text_color}; background: transparent;")

        font_size_question = int(min(screen_width * text_size / (len(answer_current_text)), 400))
        font_question = QFont(font_style, font_size_question)
        self.question_text_widget.setFont(font_question)
        self.question_text_widget.setText(answer_current_text)
        self.question_text_widget.setStyleSheet(f"color: {text_color}; background: transparent;")
        if mw.reviewer.state == "question":
            self.question_text_widget.setVisible(False)
        else:
            self.question_text_widget.setVisible(True)

    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)


def window_loop(window):
    global cooldown, startTime
    startTime = time.time()
    while not cooldown:
        now = time.time()
        window.set_opacity(min((now - startTime) / time_limit, 1) ** opacity_scale)
        QCoreApplication.processEvents()
        if mw.reviewer.state == "question" and auto_show_answer and now - startTime > auto_show_time:
            print("Auto showing answer")
            show_answer()
        elif mw.reviewer.state == "answer" and auto_rate_again and now - startTime > auto_rate_time:
            print("Auto rate again")
            rate_card(1)
        # wait
        pass


def main():
    global cooldown
    # Make the window object (that displays text on screen)
    app = QApplication([])
    window = WindowObject()

    while True:
        # Pause the script for the cooldown time
        cooldown_start_time = time.time()
        while mw.reviewer.state == "question" and not time.time() - cooldown_start_time > answer_cooldown:
            QCoreApplication.processEvents()
            pass
            # wait
        cooldown = False

        # If window_loop ending, it means new card.
        window_loop(window)
        window.set_opacity(0)

    window.close()


def show_question():
    global startTime, cooldown
    # show_question means new card, so start a cooldown
    cooldown = True


def show_answer():
    global startTime, instant_answer, time_limit

    if instant_answer:
        startTime = startTime - time_limit
    else:
        startTime = time.time()


gui_hooks.reviewer_did_show_question.append(show_question)
gui_hooks.reviewer_did_show_answer.append(show_answer)

#main()
