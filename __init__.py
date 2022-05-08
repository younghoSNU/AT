from ui.ui import UI_class
# from ui.ui improt * 이렇게 하면 파일 내 모든 클래스
# import ui.ui as aa 이런식으로도 접근가능

class Main():
    def __init__(self):
        print("실행할 메인 클래스")
        UI_class()




if __name__=="__main__":
    Main()
