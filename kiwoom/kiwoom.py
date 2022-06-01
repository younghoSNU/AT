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
        self.account_num = 8022731111
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
        self.OnEventConnect.connect(self.login_slot) # 어떻게 self에 On...함수가 들어가 있지? Ans. Kiwoom이 QAxWidget을 상속받고 있어서
        #이벤트를 걸어놔야 tr요청을 할 수 있고 이벤트는 다음의 진행을 블록하는 기능읗 하기에 원하는 일이 모두
        #끝나면 이벤트를 종료시켜줘야 한다.
        #이벤트의 종료는 키움서버에서 해당 요청에 대한 값을 주었을 때 이를 인식하고 발생하는 이벤트로
        #login_slot이 실행되고 그러면 그 slot안에서 발생시켰던 loop을 꺼줘야 다음 코드로 넘어같다.
        #여기선 login_event_loop.exit()이다.
        self.OnReceiveTrData.connect(self.trData_slot)


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
        print('나의 보유 계좌번호 %s' % account_num) # 7006831831

    def detail_account_info(self):
        print("예수금을 요청하는 함수 진입")

        #여기선 tr데이터를 받을 때 서버로 어떤 입력값을 보낼지 결정하는 부분 tr데이터는 다 SetInputValue를 사용
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String", "비밀번호", 0000)
        self.dynamicCall("SetInputValue(String, String", "비밀번호입력매체구분", 00)
        self.dynamicCall("SetInputValue(String, String", "조회구분", 2)


        #여긴 입력된 값으로 무슨 요청을 할지 여긴 예수금 상세현황 요청을 하는 것이고
        #내가정한 tr함수의 이름, tr번호, preNext, 화면번호
        self.dynamicCall("CommRqData(String, String, Int, String)", "예수금상세현황요청", "opw00001", "0", "1000")

        #화면번호
        # 내가 원하는 화면번호를 만들고 거기의 요청의 묶음을 정할 수 있다 한 화면에 100개의 요청 묶음이 가능
        # 단 화면은 200개까지 만들 수 있고
        # ("DisconnectRealData(QString)", "2000")하면 화면 번호 내 데이터가 다 날라가고
        #  ("SetRealRemove(Qstring, QString)", "2000", "예수금상세현황요청") 하면 화면에 한 요청만 날라가고

    def trData_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''

        :param sScrNo: 스크린번호
        :param sRQName: 내가요청했을 때 지은 tr함수 이름
        :param sTrCode: 요청 id
        :param sRecordName: 사용안함
        :param sPrevNext: 다음페이지가 있는지
        :return:
        '''

        if sRQName == "예수금상세현황요청"
        print("")