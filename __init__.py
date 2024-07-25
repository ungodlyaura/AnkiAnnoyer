# Author: ungodlyaura
# Send bug reports or feature requests on the GitHub: https://github.com/ungodlyaura/AnkiAnnoyer

from aqt import mw
import os

try:
    import keyboard
except ImportError:
    print("Trying to install keyboard")
    os.system('python -m pip install keyboard')
import keyboard

close_app_keybind = 'f21'  # Use + between combinations. Numbers are for num pad.
pause_app_keybind = 'f20'
show_answer_keybind = 'f14'
rate_again_keybind = 'f15'
rate_bad_keybind = 'f16'
rate_good_keybind = 'f17'
rate_easy_keybind = 'f18'
undo_answer_keybind = 'f19'


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
    if keyboard.is_pressed(close_app_keybind):
        print("Stopping app!")
        running = False
    if keyboard.is_pressed(pause_app_keybind):
        if paused:
            paused = False
            print("Continuing")
        else:
            paused = True
            print("Pausing")
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


