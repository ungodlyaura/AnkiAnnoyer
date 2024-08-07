# Author: ungodlyaura
# Send bug reports or feature requests on the GitHub: https://github.com/ungodlyaura/AnkiAnnoyer

import os
import sys
import threading
import re

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import keyboard
import time
from aqt import mw, gui_hooks
from aqt.qt import QLabel, QVBoxLayout, QFont, QCoreApplication, QWidget, Qt, pyqtSignal

# Appease editor red squiggles - ensure mw is AnkiQt not None
if not mw:
    raise ImportError("Expected mw to be AnkiQt, instead was None")

config = mw.addonManager.getConfig(__name__)

paused = False  # Is the addon paused upon loading?
cooldown = False
startTime = time.time()
styleRegex = re.compile(r"<style.*>(.*)</style>", re.M | re.S)
anchorRegex = re.compile(r"<a.*>(.*)</a>", re.M | re.S)


def show_answer():
    # noinspection PyProtectedMember
    mw.reviewer._showAnswer()


def undo_answer():
    mw.undo()


def strip_styles(string):
    return re.sub(styleRegex, "", string)


def strip_anchors(string):
    return re.sub(anchorRegex, r"\g<1>", string)


def format_card(string):
    return strip_anchors(strip_styles(string))


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
        self.setWindowTitle("AnkiAnnoyer")  # Makes window easy to target for kwin window rules
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.myLayout = QVBoxLayout()
        self.setLayout(self.myLayout)

        self.question_text_widget = QLabel("", self)
        self.question_text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.myLayout.addWidget(self.question_text_widget)

        self.answer_text_widget = QLabel("", self)
        self.answer_text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.myLayout.addWidget(self.answer_text_widget)

        self.showFullScreen()

        self.update_text_signal.connect(self.update_text)
        self.set_opacity_signal.connect(self.set_opacity)
        self.process_events_signal.connect(process_events)
        self.show_answer_signal.connect(show_answer)
        self.rate_signal.connect(rate_card)
        self.undo_signal.connect(undo_answer)

    def update_text(self):
        print("updating text")
        answer_current_text = "None"
        question_current_text = "None"

        if mw.reviewer.card and mw.reviewer.card.answer():
            answer_current_text = format_card(mw.reviewer.card.answer())
            question_current_text = format_card(mw.reviewer.card.question())
            print("Question Text:", question_current_text);
            print("Answer Text:", answer_current_text);

        screen = self.screen()
        screen_width = 1920  # type: int
        if screen:
            screen_rect = screen.availableGeometry()
            screen_width = screen_rect.width()

        font_size = int(min(screen_width * config['text_size'] / (len(question_current_text)), 450))
        font = QFont(config['font_style'], font_size)
        self.question_text_widget.setFont(font)
        self.question_text_widget.setText(question_current_text)
        self.question_text_widget.setStyleSheet(f"color: {config['text_color']}; background: transparent;")

        font_size_question = int(min(screen_width * config['text_size2'] / (len(answer_current_text)), 400))
        font_question = QFont(config['font_style'], font_size_question)
        self.answer_text_widget.setFont(font_question)
        self.answer_text_widget.setText(answer_current_text)

        self.answer_text_widget.setStyleSheet(f"color: {config['text_color']}; background: transparent;")
        if mw.reviewer.state == "question":
            self.question_text_widget.setVisible(True)
            self.answer_text_widget.setVisible(False)
        else:
            self.question_text_widget.setVisible(False)
            self.answer_text_widget.setVisible(True)

    def set_opacity(self, opacity):
        # TODO: Doesn't work on linux
        # Warning as follows: "Qt warning: This plugin does not support setting window opacity"
        # Might just be a linux issue, maybe try target the QLabel (*_text_widget) instead?
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
        while not cooldown and not paused:
            now = time.time()
            opacity = min((now - startTime) / config['time_limit'], 1) ** config['opacity_scale']
            # Emit signal to update opacity
            self.window.set_opacity_signal.emit(opacity)
            self.window.update_text_signal.emit()
            self.window.process_events_signal.emit()

            if mw.reviewer.state == "question" and config['auto_show_answer'] and now - startTime > config['auto_show_time']:
                print("Auto showing answer")
                self.window.show_answer_signal.emit()
                startTime = time.time()
            elif mw.reviewer.state == "answer" and config['auto_rate_again'] and now - startTime > config['auto_rate_time']:
                print("Auto rate again")
                self.window.rate_signal.emit(1)

            time.sleep(0.1)

    def run(self):
        global cooldown, paused

        while not paused:
            # Pause the script for the cooldown time
            print("cooldown")
            cooldown_start_time = time.time()
            while mw.reviewer.state != "answer" and not time.time() - cooldown_start_time > config['answer_cooldown']:
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
    global startTime
    print("answer shown")
    if config['instant_answer']:
        startTime = startTime - config['time_limit']
    else:
        startTime = time.time()


def on_pause_key_event(e):
    global paused
    if keyboard.is_pressed(config['pause_app_keybind']):
        if paused:
            paused = False
        else:
            paused = True


keyboard.hook(on_pause_key_event)


class Main:
    def on_key_event(self, e):
        global paused
        if not paused:
            if e.scan_code in range(2, 12):  # Remove "in range(2,12)" to allow normal numbers
                return False
            if keyboard.is_pressed(config['rate_again_keybind']):
                print("rate again")
                self.window.rate_signal.emit(1)
            if keyboard.is_pressed(config['rate_bad_keybind']):
                print("rate bad")
                self.window.rate_signal.emit(2)
            if keyboard.is_pressed(config['rate_good_keybind']):
                print("rate good")
                self.window.rate_signal.emit(3)
            if keyboard.is_pressed(config['rate_easy_keybind']):
                print("rate easy")
                self.window.rate_signal.emit(4)
            if keyboard.is_pressed(config['undo_answer_keybind']):
                print("undo answer")
                self.window.undo_signal.emit()
            if keyboard.is_pressed(config['show_answer_keybind']):
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
