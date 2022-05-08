from kiwoom.kiwoom import *
from PyQt5.QtWidgets import *
import sys

class UI_class():
    def __init__(self):
        print("UI 클래스 입니다.")

        # 어플리케이션을 초기화
        self.app = QApplication(sys.argv)
        self.Kiwoom = Kiwoom()

        self.app.exec_()
