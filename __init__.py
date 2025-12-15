# Author: ungodlyaura
# Send bug reports or feature requests on the GitHub:
# https://github.com/ungodlyaura/AnkiAnnoyer

# ============================================================
# Standard library
# ============================================================

import os
import sys
import ctypes
import threading
import re
import time
from html import unescape
from html.parser import HTMLParser

# ============================================================
# Anki / Qt
# ============================================================

from aqt import mw, gui_hooks
from aqt.qt import (
    QAction,
    QMenu,
    QColorDialog,
    QInputDialog,
    QLabel,
    QVBoxLayout,
    QFont,
    QCoreApplication,
    Qt,
    pyqtSignal,
    QLineEdit,
    QSizePolicy,
    QWidget,
)

# ============================================================
# Local imports
# ============================================================

# Ensure addon directory is importable (for keyboard helper)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import keyboard


# ============================================================
# Config and globals
# ============================================================

config = mw.addonManager.getConfig(__name__)
print(config)

cooldown = False


# ============================================================
# Windows focus detection
# ============================================================

def anki_is_active():
    """Return True if Anki's window is currently focused (Windows only)."""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value == os.getpid()


# ============================================================
# Reviewer helpers
# ============================================================

def show_answer():
    # noinspection PyProtectedMember
    mw.reviewer._showAnswer()


def undo_answer():
    mw.undo()


def rate_card(ease):
    if mw.reviewer.state == "question":
        # noinspection PyProtectedMember
        mw.reviewer._showAnswer()
    # noinspection PyProtectedMember
    mw.reviewer._answerCard(ease)


# ============================================================
# Text extraction / formatting
# ============================================================

AUDIO_TOKEN_RE = re.compile(r"\[anki:play:[^\]]+\]", re.IGNORECASE)


class AnkiTextExtractor(HTMLParser):
    """HTML parser that extracts visible text while skipping non-content fields."""

    def __init__(self):
        super().__init__()
        self.result = []
        self._skip_stack = []

        # Tags whose contents should never be shown
        self._skip_tags = {
            "rt", "style", "script", "input",
            "audio", "button", "svg",
        }

        # Tags that imply a newline
        self._nl_tags = {
            "br", "hr", "p", "div", "section",
        }

        # Class-name keywords that indicate non-text fields
        self._skip_class_keywords = {
            "tag", "tags", "card-tags", "card-tags-container",
            "sound", "audio", "tts",
        }

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "").lower()

        if tag in self._skip_tags or any(k in cls for k in self._skip_class_keywords):
            self._skip_stack.append(tag)
            return

        if tag in self._nl_tags:
            self.result.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if self._skip_stack:
            self._skip_stack.pop()
            return

        if tag in self._nl_tags:
            self.result.append("\n")

    def handle_data(self, data):
        if not self._skip_stack:
            self.result.append(data)

    def handle_entityref(self, name):
        self.handle_data(unescape(f"&{name};"))

    def handle_charref(self, name):
        self.handle_data(unescape(f"&#{name};"))

    def handle_comment(self, data):
        pass


def format_card(html_text):
    """Convert card HTML into clean, readable plain text."""
    if not html_text:
        return ""

    # Remove non-HTML Anki audio tokens
    html_text = AUDIO_TOKEN_RE.sub("", html_text)

    parser = AnkiTextExtractor()
    parser.feed(html_text)
    parser.close()

    text = unescape("".join(parser.result))

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()

def clamp_percent(value, min_value=1, max_value=100):
    return max(min(value, max_value), min_value)

def clamp_font(size, min_size=8, max_size=200):
    return max(min(size, max_size), min_size)


# ============================================================
# Menu / settings UI
# ============================================================

def init_menu():
    mw.addon_view_menu = QMenu("&AnkiAnnoyer", mw)
    mw.form.menubar.insertMenu(
        mw.form.menuTools.menuAction(),
        mw.addon_view_menu,
    )

    # Main toggles
    menu_toggle = QAction("Enable AnkiAnnoyer", mw, checkable=True)
    menu_auto_show_answer = QAction("Auto Show Answer", mw, checkable=True)
    menu_auto_rate_again = QAction("Auto Rate Again", mw, checkable=True)

    # Timings submenu
    timings_menu = QMenu("Timings", mw)
    menu_time_limit = QAction("Set Time Limit", mw)
    menu_answer_cooldown = QAction("Set Answer Cooldown", mw)
    menu_auto_show_time = QAction("Set Auto Show Time", mw)
    menu_auto_rate_time = QAction("Set Auto Rate Time", mw)

    timings_menu.addActions([
        menu_time_limit,
        menu_answer_cooldown,
        menu_auto_show_time,
        menu_auto_rate_time,
    ])

    # Keybinds submenu
    keybinds_menu = QMenu("Keybinds", mw)
    menu_show_answer_keybind = QAction("Set Show Answer Keybind", mw)
    menu_rate_again_keybind = QAction("Set Rate Again Keybind", mw)
    menu_rate_bad_keybind = QAction("Set Rate Bad Keybind", mw)
    menu_rate_good_keybind = QAction("Set Rate Good Keybind", mw)
    menu_rate_easy_keybind = QAction("Set Rate Easy Keybind", mw)
    menu_undo_answer_keybind = QAction("Set Undo Answer Keybind", mw)
    menu_pause_keybind = QAction("Set Pause Keybind", mw)

    keybinds_menu.addActions([
        menu_show_answer_keybind,
        menu_rate_again_keybind,
        menu_rate_bad_keybind,
        menu_rate_good_keybind,
        menu_rate_easy_keybind,
        menu_undo_answer_keybind,
        menu_pause_keybind,
    ])

    # Text style submenu
    text_style_menu = QMenu("Text Style", mw)
    menu_set_text_color = QAction("Set Text Color", mw)
    menu_set_font_style = QAction("Set Font Style", mw)
    menu_question_size = QAction("Set Question Size", mw)
    menu_answer_size = QAction("Set Answer Size", mw)
    menu_text_width = QAction("Set Text Width (%)", mw)

    text_style_menu.addActions([
        menu_set_text_color,
        menu_set_font_style,
        menu_question_size,
        menu_answer_size,
        menu_text_width,
    ])

    menu_text_width.triggered.connect(set_width_percent)

    # Extra submenu
    extra_menu = QMenu("Extra", mw)
    menu_opacity_scale = QAction("Set Opacity Scale", mw)
    menu_instant_answer = QAction("Instant Show Answer", mw, checkable=True)

    menu_hide_when_anki_active = QAction(
        "Hide While Anki Is Focused",
        mw,
        checkable=True,
    )
    menu_hide_when_anki_active.setChecked(
        config.get("hide_when_anki_active", True)
    )

    extra_menu.addActions([
        menu_opacity_scale,
        menu_instant_answer,
        menu_hide_when_anki_active,
    ])

    menu_hide_when_anki_active.triggered.connect(
        lambda: toggle_config("hide_when_anki_active")
    )

    # Assemble main menu
    mw.addon_view_menu.addActions([
        menu_toggle,
        menu_auto_show_answer,
        menu_auto_rate_again,
    ])
    mw.addon_view_menu.addMenu(timings_menu)
    mw.addon_view_menu.addMenu(keybinds_menu)
    mw.addon_view_menu.addMenu(text_style_menu)
    mw.addon_view_menu.addMenu(extra_menu)

    # Initial states
    menu_toggle.setChecked(not bool(config["paused"]))
    menu_auto_show_answer.setChecked(config["auto_show_answer"])
    menu_auto_rate_again.setChecked(config["auto_rate_again"])
    menu_instant_answer.setChecked(config["instant_answer"])

    # Connections
    menu_time_limit.triggered.connect(
        lambda: set_value("time_limit", "Set time limit (seconds):", config["time_limit"])
    )
    menu_answer_cooldown.triggered.connect(
        lambda: set_value("answer_cooldown", "Set answer cooldown (seconds):", config["answer_cooldown"])
    )
    menu_toggle.triggered.connect(lambda: toggle_config("paused"))
    menu_auto_show_answer.triggered.connect(lambda: toggle_config("auto_show_answer"))
    menu_auto_rate_again.triggered.connect(lambda: toggle_config("auto_rate_again"))

    menu_pause_keybind.triggered.connect(
        lambda: set_keybind("pause_app_keybind", "Set keybind for Pause:", config["pause_app_keybind"])
    )
    menu_show_answer_keybind.triggered.connect(
        lambda: set_keybind("show_answer_keybind", "Set keybind for Show Answer:", config["show_answer_keybind"])
    )
    menu_rate_again_keybind.triggered.connect(
        lambda: set_keybind("rate_again_keybind", "Set keybind for Rate Again:", config["rate_again_keybind"])
    )
    menu_rate_bad_keybind.triggered.connect(
        lambda: set_keybind("rate_bad_keybind", "Set keybind for Rate Bad:", config["rate_bad_keybind"])
    )
    menu_rate_good_keybind.triggered.connect(
        lambda: set_keybind("rate_good_keybind", "Set keybind for Rate Good:", config["rate_good_keybind"])
    )
    menu_rate_easy_keybind.triggered.connect(
        lambda: set_keybind("rate_easy_keybind", "Set keybind for Rate Easy:", config["rate_easy_keybind"])
    )
    menu_undo_answer_keybind.triggered.connect(
        lambda: set_keybind("undo_answer_keybind", "Set keybind for Undo Answer:", config["undo_answer_keybind"])
    )

    menu_set_text_color.triggered.connect(set_text_color)
    menu_set_font_style.triggered.connect(
        lambda: set_text_value("font_style", "Set font style:", config["font_style"])
    )

    menu_auto_show_time.triggered.connect(
        lambda: set_value("auto_show_time", "Set auto show time (seconds):", config["auto_show_time"])
    )
    menu_auto_rate_time.triggered.connect(
        lambda: set_value("auto_rate_time", "Set auto rate time (seconds):", config["auto_rate_time"])
    )

    menu_instant_answer.triggered.connect(lambda: toggle_config("instant_answer"))
    menu_opacity_scale.triggered.connect(
        lambda: set_value("opacity_scale", "Set opacity scale:", config["opacity_scale"])
    )
    menu_question_size.triggered.connect(
        lambda: set_value("question_size", "Set question text size:", config["question_size"])
    )
    menu_answer_size.triggered.connect(
        lambda: set_value("answer_size", "Set answer text size:", config["answer_size"])
    )


# ============================================================
# Config helpers
# ============================================================

def set_text_value(key, prompt, default):
    value, accepted = QInputDialog.getText(
        mw,
        "AnkiAnnoyer",
        prompt,
        QLineEdit.EchoMode.Normal,
        default,
    )
    if accepted:
        config[key] = value
        mw.addonManager.writeConfig(__name__, config)


def set_value(key, prompt, default):
    value, accepted = QInputDialog.getInt(mw, "AnkiAnnoyer", prompt, default)
    if accepted:
        config[key] = value
        mw.addonManager.writeConfig(__name__, config)

    main.background_task.window.update_text_signal.emit()


def toggle_config(key):
    config[key] = not config[key]
    mw.addonManager.writeConfig(__name__, config)


def set_keybind(key, prompt, default):
    keybind, accepted = QInputDialog.getText(
        mw,
        "AnkiAnnoyer",
        prompt,
        QLineEdit.EchoMode.Normal,
        default,
    )
    if accepted:
        config[key] = keybind
        mw.addonManager.writeConfig(__name__, config)


def set_text_color():
    color = QColorDialog.getColor()
    if color.isValid():
        config["text_color"] = color.name()
        mw.addonManager.writeConfig(__name__, config)


def set_font(key, prompt, default):
    font, accepted = QInputDialog.getText(mw, "AnkiAnnoyer", prompt, default)
    if accepted:
        config[key] = font
        mw.addonManager.writeConfig(__name__, config)

def set_width_percent():
    from aqt.qt import QDialog, QVBoxLayout, QSlider, QLabel

    dlg = QDialog(mw)
    dlg.setWindowTitle("Text Width (%)")

    layout = QVBoxLayout(dlg)

    label = QLabel(f"{config['text_width_percent']}%", dlg)

    slider = QSlider(Qt.Orientation.Horizontal, dlg)
    slider.setRange(0, 100)
    slider.setValue(config["text_width_percent"])

    def on_change(value):
        label.setText(f"{value}%")
        config["text_width_percent"] = value
        mw.addonManager.writeConfig(__name__, config)
        if main.window:
            main.window.update_text_signal.emit()

    slider.valueChanged.connect(on_change)

    layout.addWidget(label)
    layout.addWidget(slider)

    dlg.show()


# ============================================================
# Overlay window
# ============================================================

class WindowObject(QWidget):
    update_text_signal = pyqtSignal()
    set_opacity_signal = pyqtSignal(float)
    show_answer_signal = pyqtSignal()
    rate_signal = pyqtSignal(int)
    undo_signal = pyqtSignal()
    set_visible_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        # Window flags
        self.setWindowTitle("AnkiAnnoyer")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Fullscreen geometry
        screen = self.screen().availableGeometry()
        self.setGeometry(screen)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Text widgets
        self.question_text_widget = QLabel("", self)
        self.answer_text_widget = QLabel("", self)

        for widget in (self.question_text_widget, self.answer_text_widget):
            widget.setTextFormat(Qt.TextFormat.PlainText)
            widget.setWordWrap(True)
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            widget.setStyleSheet("background: transparent;")
            widget.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

        layout.addWidget(self.question_text_widget)
        layout.addWidget(self.answer_text_widget)

        self.setLayout(layout)
        self.showFullScreen()

        # Signals
        self.update_text_signal.connect(self.update_text)
        self.set_opacity_signal.connect(self.set_opacity)
        self.show_answer_signal.connect(show_answer)
        self.rate_signal.connect(rate_card)
        self.undo_signal.connect(undo_answer)
        self.set_visible_signal.connect(self.setVisible)

    def update_text(self):
        # Fetch card text
        question_text = ""
        answer_text = ""

        if mw.reviewer.card:
            question_text = format_card(mw.reviewer.card.question())
            answer_text = format_card(mw.reviewer.card.answer())

        # Visibility
        showing_question = mw.reviewer.state == "question"
        self.question_text_widget.setVisible(showing_question)
        self.answer_text_widget.setVisible(not showing_question)

        # Fonts
        font_family = config["font_style"]
        self.question_text_widget.setFont(
            QFont(font_family, clamp_font(config["question_size"]))
        )
        self.answer_text_widget.setFont(
            QFont(font_family, clamp_font(config["answer_size"]))
        )

        # Text
        self.question_text_widget.setText(question_text)
        self.answer_text_widget.setText(answer_text)

        # Layout constraints
        screen = self.screen().availableGeometry()
        width_percent = clamp_percent(config["text_width_percent"])
        max_width = int(screen.width() * (width_percent / 100))

        for widget in (self.question_text_widget, self.answer_text_widget):
            widget.setMaximumWidth(max_width)
            widget.setWordWrap(True)
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            widget.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred,
            )

        # Styling
        style = f"color: {config['text_color']}; background: transparent;"
        self.question_text_widget.setStyleSheet(style)
        self.answer_text_widget.setStyleSheet(style)

        self.question_text_widget.adjustSize()
        self.answer_text_widget.adjustSize()
        self.layout().invalidate()

    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)


# ============================================================
# Background timing logic
# ============================================================

class BackgroundTask(threading.Thread):
    def __init__(self, window):
        super().__init__(daemon=True)
        self.window = window
        self.startTime = time.time()
        self.running = True

    def new_card(self):
        self.startTime = time.time()
        self.window.set_opacity_signal.emit(0.0)
        print("new card")

        if config["instant_answer"] and mw.reviewer.state == "answer":
            self.startTime = time.time() - config["time_limit"]

        self.window.update_text_signal.emit()

        while not cooldown and not config["paused"] and self.running and self.window:
            if config.get("hide_when_anki_active", True):
                self.window.set_visible_signal.emit(not anki_is_active())
            else:
                self.window.set_visible_signal.emit(True)

            opacity = min(
                (time.time() - self.startTime) / config["time_limit"],
                1,
            ) ** config["opacity_scale"]

            self.window.set_opacity_signal.emit(opacity)

            if (
                mw.reviewer.state == "question"
                and config["auto_show_answer"]
                and time.time() - self.startTime > config["auto_show_time"]
            ):
                print("Auto showing answer")
                self.window.show_answer_signal.emit()
                self.startTime = time.time()

            elif mw.reviewer.state == "answer" and config["auto_rate_again"]:
                if (
                    config["instant_answer"]
                    and time.time() - self.startTime
                    > config["auto_rate_time"] + config["time_limit"]
                ):
                    print("Auto rate again")
                    self.window.rate_signal.emit(0)

                elif (
                    not config["instant_answer"]
                    and time.time() - self.startTime > config["auto_rate_time"]
                ):
                    print("Auto rate again")
                    self.window.rate_signal.emit(0)

            time.sleep(0.1)

    def run(self):
        global cooldown

        while self.running and self.window and mw.reviewer:
            print("cooldown")
            self.window.set_opacity_signal.emit(0.0)

            cooldown_start_time = time.time()
            time.sleep(0.1)

            while (
                mw.reviewer.state != "answer"
                and not time.time() - cooldown_start_time > config["answer_cooldown"]
                and self.window
            ):
                time.sleep(0.1)

            cooldown = False
            self.new_card()


# ============================================================
# Main plugin controller
# ============================================================

class Main:
    def __init__(self):
        init_menu()

        self.window = None
        self.background_task = None

        keyboard.hook(self.on_key_event)

        gui_hooks.reviewer_did_show_question.append(self.on_show_question)
        gui_hooks.reviewer_did_show_answer.append(self.on_show_answer)
        gui_hooks.reviewer_will_end.append(self.on_stop_study)

        gui_hooks.profile_did_open.append(self.start_plugin)
        gui_hooks.profile_will_close.append(self.on_anki_close)

        QCoreApplication.instance().aboutToQuit.connect(self.on_anki_close)

    def start_plugin(self):
        self.window = WindowObject()
        self.background_task = BackgroundTask(self.window)
        self.background_task.start()

    def on_show_question(self, card):
        global cooldown
        cooldown = True
        self.window.set_opacity_signal.emit(0.0)
        self.window.update_text_signal.emit()

    def on_show_answer(self, card):
        if not self.window or not self.background_task:
            return

        if not config["instant_answer"]:
            self.background_task.startTime = time.time()
        else:
            self.background_task.startTime = time.time() - config["time_limit"]

        self.window.update_text_signal.emit()

    def on_stop_study(self):
        global cooldown
        if not self.window:
            return
        cooldown = True
        self.window.update_text_signal.emit()

    def on_key_event(self, e):
        if config["paused"]:
            return

        if e.scan_code in range(2, 12):
            return False

        if keyboard.is_pressed(config["rate_again_keybind"]):
            self.window.rate_signal.emit(1)
        if keyboard.is_pressed(config["rate_bad_keybind"]):
            self.window.rate_signal.emit(2)
        if keyboard.is_pressed(config["rate_good_keybind"]):
            self.window.rate_signal.emit(3)
        if keyboard.is_pressed(config["rate_easy_keybind"]):
            self.window.rate_signal.emit(4)
        if keyboard.is_pressed(config["undo_answer_keybind"]):
            self.window.undo_signal.emit()
        if keyboard.is_pressed(config["show_answer_keybind"]):
            self.window.show_answer_signal.emit()
        if keyboard.is_pressed(config["pause_app_keybind"]):
            toggle_config("paused")

    def on_anki_close(self):
        if self.background_task:
            self.background_task.running = False
            self.background_task.join(timeout=1)
            self.background_task = None

        if self.window:
            self.window.close()
            self.window.deleteLater()
            self.window = None

main = Main()
