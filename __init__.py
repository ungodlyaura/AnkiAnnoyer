# Author: ungodlyaura
# Send bug reports or feature requests on the GitHub: https://github.com/ungodlyaura/AnkiAnnoyer

import os
import sys
import threading
import re
from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu, QKeySequence, QColorDialog, QInputDialog, QLabel, QVBoxLayout, QFont, \
    QCoreApplication, Qt, pyqtSignal, QLineEdit, QSpacerItem, QSizePolicy, QWidget

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import keyboard
import time

# Config and global variables
config = mw.addonManager.getConfig(__name__)

cooldown = False

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
        # noinspection PyProtectedMember
        mw.reviewer._showAnswer()
    # noinspection PyProtectedMember
    mw.reviewer._answerCard(ease)


# UI Element Initialization
def init_menu():
    mw.addon_view_menu = QMenu("""&AnkiAnnoyer""", mw)
    mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(), mw.addon_view_menu)

    # Primary options
    menu_toggle = QAction("Enable AnkiAnnoyer", mw, checkable=True)
    menu_auto_show_answer = QAction("Auto Show Answer", mw, checkable=True)
    menu_auto_rate_again = QAction("Auto Rate Again", mw, checkable=True)

    # Timings submenu
    timings_menu = QMenu("Timings", mw)
    menu_time_limit = QAction("Set Time Limit", mw)
    menu_answer_cooldown = QAction("Set Answer Cooldown", mw)
    menu_auto_show_time = QAction("Set Auto Show Time", mw)
    menu_auto_rate_time = QAction("Set Auto Rate Time", mw)
    timings_menu.addAction(menu_time_limit)
    timings_menu.addAction(menu_answer_cooldown)
    timings_menu.addAction(menu_auto_show_time)
    timings_menu.addAction(menu_auto_rate_time)

    # Keybinds submenu
    keybinds_menu = QMenu("Keybinds", mw)
    menu_show_answer_keybind = QAction("Set Show Answer Keybind", mw)
    menu_rate_again_keybind = QAction("Set Rate Again Keybind", mw)
    menu_rate_bad_keybind = QAction("Set Rate Bad Keybind", mw)
    menu_rate_good_keybind = QAction("Set Rate Good Keybind", mw)
    menu_rate_easy_keybind = QAction("Set Rate Easy Keybind", mw)
    menu_undo_answer_keybind = QAction("Set Undo Answer Keybind", mw)
    menu_pause_keybind = QAction("Set Pause Keybind", mw)
    keybinds_menu.addAction(menu_show_answer_keybind)
    keybinds_menu.addAction(menu_rate_again_keybind)
    keybinds_menu.addAction(menu_rate_bad_keybind)
    keybinds_menu.addAction(menu_rate_good_keybind)
    keybinds_menu.addAction(menu_rate_easy_keybind)
    keybinds_menu.addAction(menu_undo_answer_keybind)
    keybinds_menu.addAction(menu_pause_keybind)

    # Text Style submenu
    text_style_menu = QMenu("Text Style", mw)
    menu_set_text_color = QAction("Set Text Color", mw)
    menu_set_font_style = QAction("Set Font Style", mw)
    menu_question_size = QAction("Set Question Size", mw)
    menu_answer_size = QAction("Set Answer Size", mw)
    text_style_menu.addAction(menu_set_text_color)
    text_style_menu.addAction(menu_set_font_style)
    text_style_menu.addAction(menu_question_size)
    text_style_menu.addAction(menu_answer_size)

    # Extra submenu
    extra_menu = QMenu("Extra", mw)
    menu_opacity_scale = QAction("Set Opacity Scale", mw)
    menu_instant_answer = QAction("Instant Show Answer", mw, checkable=True)
    extra_menu.addAction(menu_opacity_scale)
    extra_menu.addAction(menu_instant_answer)

    # Add primary actions and submenus to the main menu
    mw.addon_view_menu.addAction(menu_toggle)
    mw.addon_view_menu.addAction(menu_auto_show_answer)
    mw.addon_view_menu.addAction(menu_auto_rate_again)
    mw.addon_view_menu.addMenu(timings_menu)
    mw.addon_view_menu.addMenu(keybinds_menu)
    mw.addon_view_menu.addMenu(text_style_menu)
    mw.addon_view_menu.addMenu(extra_menu)

    # Set initial check state for checkable options
    menu_toggle.setChecked(not bool(config['paused']))
    menu_auto_show_answer.setChecked(config['auto_show_answer'])
    menu_auto_rate_again.setChecked(config['auto_rate_again'])
    menu_instant_answer.setChecked(config['instant_answer'])

    # Connect menu actions to functions
    menu_time_limit.triggered.connect(
        lambda: set_value("time_limit", "Set time limit (seconds):", config['time_limit']))
    menu_answer_cooldown.triggered.connect(
        lambda: set_value("answer_cooldown", "Set answer cooldown (seconds):", config['answer_cooldown']))
    menu_toggle.triggered.connect(lambda: toggle_config("paused"))
    menu_auto_show_answer.triggered.connect(lambda: toggle_config("auto_show_answer"))
    menu_auto_rate_again.triggered.connect(lambda: toggle_config("auto_rate_again"))
    menu_pause_keybind.triggered.connect(
        lambda: set_keybind("pause_app_keybind", "Set keybind for Pause:", config['pause_app_keybind']))
    menu_show_answer_keybind.triggered.connect(
        lambda: set_keybind("show_answer_keybind", "Set keybind for Show Answer:", config['show_answer_keybind']))
    menu_rate_again_keybind.triggered.connect(
        lambda: set_keybind("rate_again_keybind", "Set keybind for Rate Again:", config['rate_again_keybind']))
    menu_rate_bad_keybind.triggered.connect(
        lambda: set_keybind("rate_bad_keybind", "Set keybind for Rate Bad:", config['rate_bad_keybind']))
    menu_rate_good_keybind.triggered.connect(
        lambda: set_keybind("rate_good_keybind", "Set keybind for Rate Good:", config['rate_good_keybind']))
    menu_rate_easy_keybind.triggered.connect(
        lambda: set_keybind("rate_easy_keybind", "Set keybind for Rate Easy:", config['rate_easy_keybind']))
    menu_undo_answer_keybind.triggered.connect(
        lambda: set_keybind("undo_answer_keybind", "Set keybind for Undo Answer:", config['undo_answer_keybind']))
    menu_set_text_color.triggered.connect(set_text_color)
    menu_set_font_style.triggered.connect(lambda: set_text_value("font_style", "Set font style:", config['font_style']))
    menu_auto_show_time.triggered.connect(lambda: set_value("auto_show_time", "Set auto show time (seconds):", config['auto_show_time']))
    menu_auto_rate_time.triggered.connect(
        lambda: set_value("auto_rate_time", "Set auto rate time (seconds):", config['auto_rate_time']))
    menu_instant_answer.triggered.connect(lambda: toggle_config("instant_answer"))
    menu_opacity_scale.triggered.connect(
        lambda: set_value("opacity_scale", "Set opacity scale:", config['opacity_scale']))
    menu_question_size.triggered.connect(
        lambda: set_value("question_size", "Set question text size:", config['question_size']))
    menu_answer_size.triggered.connect(
        lambda: set_value("answer_size", "Set answer text size:", config['answer_size']))


# Utility functions for settings

def set_text_value(key, prompt, default):
    value, accepted = QInputDialog.getText(mw, "AnkiAnnoyer", prompt, QLineEdit.EchoMode.Normal, default)
    if accepted:
        config[key] = value
        mw.addonManager.writeConfig(__name__, config)


def set_value(key, prompt, default):
    value, accepted = QInputDialog.getInt(mw, "AnkiAnnoyer", prompt, default)
    if accepted:
        config[key] = value
        mw.addonManager.writeConfig(__name__, config)


def toggle_config(key):
    config[key] = not config[key]
    mw.addonManager.writeConfig(__name__, config)


def set_keybind(key, prompt, default):
    keybind, accepted = QInputDialog.getText(mw, "AnkiAnnoyer", prompt, QLineEdit.EchoMode.Normal, default)
    if accepted:
        config[key] = keybind
        mw.addonManager.writeConfig(__name__, config)


def set_text_color():
    color = QColorDialog.getColor()
    if color.isValid():
        config['text_color'] = color.name()
        mw.addonManager.writeConfig(__name__, config)


def set_font(key, prompt, default):
    font, accepted = QInputDialog.getText(mw, "AnkiAnnoyer", prompt, default)
    if accepted:
        config[key] = font
        mw.addonManager.writeConfig(__name__, config)


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

        self.myLayout = QVBoxLayout()
        self.setLayout(self.myLayout)

        screen = self.screen().availableGeometry()
        self.setMaximumHeight(screen.height())
        self.setFixedWidth(screen.width() * 0.8)

        # Center alignment
        self.myLayout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Spacers and widgets
        self.top_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.myLayout.addItem(self.top_spacer)

        self.question_text_widget = QLabel("", self)
        self.question_text_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.myLayout.addWidget(self.question_text_widget)

        self.answer_text_widget = QLabel("", self)
        self.answer_text_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.myLayout.addWidget(self.answer_text_widget)

        self.bottom_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.myLayout.addItem(self.bottom_spacer)

        self.showFullScreen()

        # Signal connections
        self.update_text_signal.connect(self.update_text)
        self.set_opacity_signal.connect(self.set_opacity)
        self.process_events_signal.connect(process_events)
        self.show_answer_signal.connect(show_answer)
        self.rate_signal.connect(rate_card)
        self.undo_signal.connect(undo_answer)

    # Update the text content and ensure central alignment
    def update_text(self):
        # Get current text from Anki card
        answer_current_text = "None"
        question_current_text = "None"

        if mw.reviewer.card and mw.reviewer.card.answer():
            answer_current_text = format_card(mw.reviewer.card.answer())
            question_current_text = format_card(mw.reviewer.card.question())

        # Show question or answer based on reviewer's state
        if mw.reviewer.state == "question":
            self.question_text_widget.setVisible(True)
            self.answer_text_widget.setVisible(False)
        else:
            self.question_text_widget.setVisible(False)
            self.answer_text_widget.setVisible(True)

        # Set the text for the question and answer widgets
        self.question_text_widget.setText(question_current_text)
        self.answer_text_widget.setText(answer_current_text)

        # Set font style and size for the question and answer widgets
        self.question_text_widget.setFont(QFont(config['font_style'], config['question_size']))
        self.answer_text_widget.setFont(QFont(config['font_style'], config['answer_size']))

        # Apply the styles (color, transparent background)
        self.question_text_widget.setStyleSheet(f"color: {config['text_color']}; background: transparent;")
        self.answer_text_widget.setStyleSheet(f"color: {config['text_color']}; background: transparent;")

        # Ensure widgets adjust to the center properly
        self.question_text_widget.adjustSize()  # Adjust size after changing text
        self.answer_text_widget.adjustSize()  # Adjust size after changing text

        # Get screen geometry and set the window position
        screen_geometry = self.screen().availableGeometry()
        window_width = screen_geometry.width()
        window_height = screen_geometry.height()

        # Set the window size to fit the screen and position it in the center
        self.setGeometry(
            (window_width - self.width()) // 2,  # Center X
            (window_height - self.height()) // 2,  # Center Y
            window_width,  # Window width
            window_height  # Window height
        )

        # Set layout alignment to ensure the widgets are centered
        self.myLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer_text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ensure that the layout is updated and adjusted correctly
        self.myLayout.update()
        self.adjustSize()

    def set_opacity(self, opacity):
        # Qt limitation on some platforms may prevent setting window opacity.
        self.setWindowOpacity(opacity)


class BackgroundTask(threading.Thread):
    def __init__(self, window):
        super().__init__()
        self.startTime = time.time()
        self.window = window
        self.running = True

    def stop(self):
        print("try to stop")
        self.running = False
        if hasattr(self.window, 'timer'):
            self.window.timer.stop()
        self.window.close()
        self.window = None

    def new_card(self):
        self.startTime = time.time()
        print("new card")
        while not cooldown and not config['paused'] and self.running and self.window:

            opacity = min((time.time() - self.startTime) / config['time_limit'], 1) ** config['opacity_scale']
            # Emit signal to update opacity
            self.window.set_opacity_signal.emit(opacity)
            self.window.process_events_signal.emit()
            self.window.update_text_signal.emit()

            if mw.reviewer.state == "question" and config['auto_show_answer'] and time.time() - self.startTime > config[
                'auto_show_time']:
                print("Auto showing answer")
                self.window.show_answer_signal.emit()
                self.startTime = time.time()
            elif mw.reviewer.state == "answer" and config['auto_rate_again']:
                print(
                    f"instant answer: {config['instant_answer']} | current seconds: {time.time() - self.startTime} | target seconds: {config['auto_rate_time'] + config['time_limit']} | autorate: {config['auto_rate_time']} | timelimit: {config['time_limit']}")
                if config['instant_answer'] and time.time() - self.startTime > config['auto_rate_time'] + config[
                    'time_limit']:
                    print("Auto rate again")
                    self.window.rate_signal.emit(1)
                elif not config['instant_answer'] and time.time() - self.startTime > config['auto_rate_time']:
                    print("Auto rate again")
                    self.window.rate_signal.emit(1)
            time.sleep(0.1)

    def run(self):
        global cooldown
        while self.running and self.window:
            time.sleep(0.1)
            print("cooldown")
            self.window.set_opacity_signal.emit(0)
            cooldown_start_time = time.time()
            self.new_card()
            self.window.process_events_signal.emit()
            while mw.reviewer.state != "answer" and not time.time() - cooldown_start_time > config['answer_cooldown'] and self.window:
                self.window.process_events_signal.emit()
                time.sleep(0.1)
            cooldown = False
        # Cause error to close, because I give up
        self.window.process_events_signal.emit()
        exit()


class Main:
    def on_show_question(self, card):
        global cooldown
        print("question shown")
        cooldown = True
        self.window.update_text_signal.emit()

    def on_show_answer(self, card):
        if not config['instant_answer']:
            self.background_task.startTime = time.time()
        else:
            self.background_task.startTime = time.time() - config["time_limit"]
        self.window.update_text_signal.emit()

    def on_key_event(self, e):
        if not config['paused']:
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
            if keyboard.is_pressed(config['pause_app_keybind']):
                print("paused")
                config['paused'] = not config['paused']

    def on_anki_close(self):
        print("Anki is closing, clean up background tasks.")
        if self.background_task:
            self.background_task.stop()

    def start_plugin(self):
        self.window = WindowObject()
        self.background_task = BackgroundTask(self.window)
        self.background_task.start()

    def __init__(self):
        init_menu()
        keyboard.hook(self.on_key_event)
        gui_hooks.reviewer_did_show_question.append(self.on_show_question)
        gui_hooks.reviewer_did_show_answer.append(self.on_show_answer)
        self.window = None
        self.background_task = None
        gui_hooks.profile_did_open.append(self.start_plugin)
        gui_hooks.profile_will_close.append(self.on_anki_close)


main = Main()
