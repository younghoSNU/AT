from PyQt5.QAxContainer import *
from PyQt5.QtCore import *


class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()

        print("키움 클래스입니다.")
        ############################## 이벤트 루프 모음
        self.login_event_loop = None
        ###########################################

        ###############################변수모음
        self.account_num = None
        #########################################3

        self.get_ocx_instance()
        self.event_slots()
        self.signal_login_commConnect()
        self.get_account_info()
    # PyQt5를 통해 키움 증권프로그램에 접속하기 위한 절차
    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
    
    # 로그인 등에 사용하는 이벤트를 담는 함수
    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) # 어떻게 self에 On...함수가 들어가 있지?

    def login_slot(self, errCode):
        print(errCode)  # 로그인 코드로 0이 들어올 때가 성공 아니면 실패
        self.login_event_loop.exit()

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop() # 로그인 시도시 역할?
        self.login_event_loop.exec_()   # 로그인이 완료될 때까지 기다려주도록 하는 코드

    def get_account_info(self):
        account_list = self.dynamicCall("GetLoginInfo(String)", 'ACCNO')

        account_num = account_list.split(';')[0]
        print('나의 보유 계좌번호 %s' % account_num)