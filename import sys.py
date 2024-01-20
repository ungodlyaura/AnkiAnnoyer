import sys
import time
import requests
import dxcam
# import json

from PyQt5 import QtGui, QtCore, uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QGraphicsOpacityEffect

#from PySide2 import QtCore, QtWidgets, QtGui

ANKI_URL = "http://localhost:8765"

lastKanji = "東"

maxTime = 60

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # always on top
        # remove buttons

        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.text)
        self.setLayout(self.layout)
        self.eff = QGraphicsOpacityEffect(self)
        self.resize(100,100)


    @QtCore.pyqtSlot()
    def updateWindow(self,size,currentKanji,timeLeft):
        
        self.text.setText(currentKanji)
        self.eff.setOpacity(timeLeft/maxTime)


    def updateWindowLoop(self):
       
        # currentCard = getCurrentCard()
        # currentKanji = currentCard.question # request current card
        currentKanji = "sugmaballs"
        timeLeft = maxTime
        lastKanji = currentKanji # update window to get kanji
        while currentKanji == lastKanji:
            time.sleep(1)
            timeLeft += -1
            print("poyo")
            size = [600-timeLeft,600-timeLeft]
            if size[0] < 20:
                size[0] = 20
            if size[1] < 20:
                size[1] = 20
            self.updateWindow(size,currentKanji,timeLeft)

app = QtWidgets.QApplication([])

widget = MyWidget()
widget.resize(800, 600)
widget.show()
# widget.hide()

timer = QtCore.QTimer()
timer.timeout.connect(widget.updateWindow)
timer.start()




def getCurrentCard():
    payload = {
        "action": "guiCurrentCard",
        "version": 5
    }
    r = requests.post(ANKI_URL, json=payload)

    return r.json




sys.exit(app.exec_())


