from PyQt5.QAxContainer import *  # Kiwoon클래스가 상속받는 QAxWidget클래스를 갖고 있다
from PyQt5.QtCore import *  # QEventLoop를 갖는다
from config.errorCode import error_code


class Kiwoom(QAxWidget):
    # container역할
    def __init__(self):
        super().__init__()

        print("키움 클래스입니다.")
        ################################################################### 이벤트 루프 모음
        self.login_event_loop = QEventLoop()
        self.detail_account_info_loop = QEventLoop()
        self.checkLastPageMyStock = False
        self.checkFirstPageMyStock = True
        ##################################################################################

        ################################################################## 스크린번호 모음
        self.generalScreenNo = "2000"
        self.screen_calculation_stock = "4000"
        ##################################################################################

        #################################################################### 클래스 변수모음
        self.account_num = None
        self.account_stock_dict = {}
        self.outstanding_stock_dict = {}
        # 계좌관련 변수
        self.use_money = None
        self.use_money_percent = 0.4
        ##################################################################################

        ############### 실행부분
        self.get_ocx_instance()
        self.event_slots()
        self.signal_login_commConnect()
        # self.checkCurrentConnectState()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_myStock(first=True)  # 계좌평가잔고내역요청
        self.outstandingStock()

    # PyQt5를 통해 키움 증권프로그램에 접속하기 위한 절차
    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")
        # print("commconnect %s" % self.dynamicCall("CommConnect()"))
        # dynamicCall자체로 그냥 호출에 대한 출력이 이뤄지기도 한다
        # 그런데 서버로부터 리턴을 받아야 출력이 될텐데 리턴을 못받는 경우와 받는 경우의 구분을 어떻게 하지?
        self.login_event_loop = QEventLoop()  # 로그인 시도 시 역할은?
        # ans. 로그인이 완료됐다는 키움서버응답을 받아야지만 다음 과정이 진행되도록 막는 기능을
        # 이벤트 루프를 만들었다가 제거하는 방식으로 한다.

        self.login_event_loop.exec_()  # 로그인이 완료될 때까지 기다려주도록 하는 코드

    #########################################################################################슬롯 모음
    # 로그인, tr함수 호출 등에 사용하는 이벤트를 담는 함수
    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)  # 어떻게 self에 On...함수가 들어가 있지? Ans. Kiwoom이 QAxWidget을 상속받고 있어서
        # 이벤트를 걸어놔야 tr요청을 할 수 있고 이벤트는 다음의 진행을 블록하는 기능읗 하기에 원하는 일이 모두
        # 끝나면 이벤트를 종료시켜줘야 한다.
        # 이벤트의 종료는 키움서버에서 해당 요청에 대한 값을 주었을 때 이를 인식하고 발생하는 이벤트로
        # login_slot이 실행되고 그러면 그 slot안에서 발생시켰던 loop을 꺼줘야 다음 코드로 넘어같다.
        # 여기선 login_event_loop.exit()이다.
        self.OnReceiveTrData.connect(self.trData_slot)

    #real이벤트와 그냥 이벤트의 차이가 머지? 그리고 컨스트럭터에 위 함수 추가 필요하다
    def real_event_slots(self):
        # 체결받은 시점이 언제인지 알려주는 이벤트
        self.OnReceiveChejanData.connect(self.chejan_slot)


    def trData_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        tr데이터 요청에 의한 리턴이 이 함수 내로 이뤄진다
        :param sScrNo: 스크린번호
        :param sRQName: 내가요청했을 때 지은 tr함수 이름
        :param sTrCode: 요청 id
        :param sRecordName: 사용안함 그냥 받아드리자. 출력이 되는 값이 없어
        :param sPrevNext: 다음페이지가 있는지
        :return:
        '''

        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "예수금")
            print(deposit)
            print("예수금 타입 %s " % type(deposit))
            print("예수금 %s" % int(deposit))

            self.use_money = int(deposit) * self.use_money_percent

            availMoney = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % int(availMoney))

            self.detail_account_info_loop.exit()

        elif sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0,
                                               "총매입금액")
            total_buy_money_result = int(total_buy_money)
            print("총매입금액 %s" % total_buy_money_result)

            total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName,
                                                      0,
                                                      "총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)
            print("총수익률(%%) %s" % total_profit_loss_rate_result)

            cnt = self.dynamicCall("GetRepeatCnt(String, String)", sTrCode, sRQName)
            print("cnt = %s이고 sPrevNext는 %s" % (cnt, sPrevNext))  # sPrevNext는 다음페이지가 있으면 "2" 아니면 "0"이나 ""을 리턴
            temp = 0

            for i in range(cnt):
                # A002233이런식의 출력, strip는 strip(...)에서 ...안의 문자열을 문자의 양끝에 있을시 제거해 준다. 만약 공백이면 빈칸을 제거한다.
                code = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목번호")
                code_name = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i,
                                                  "보유수량")
                buy_price = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i,
                                              "수익률(%)")
                current_price = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i,
                                                 "현재가")
                total_bought_stock_price = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode,
                                                            sRQName, i, "매입금액")
                possible_quantity_to_sell = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode,
                                                             sRQName, i, "매매가능수량")

                code = code.strip()[1:]
                code_name = code_name.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_bought_stock_price = int(total_bought_stock_price.strip())
                possible_quantity_to_sell = int(possible_quantity_to_sell.strip())

                self.account_stock_dict[code] = {
                    "종목명": code_name,
                    "보유수량": stock_quantity,
                    "매입가": buy_price,
                    "수익률(%)": learn_rate,
                    "현재가": current_price,
                    "매입금액": total_bought_stock_price,
                    "매매가능수량": possible_quantity_to_sell
                }

                print("Key: %s and values: %s" % (code, self.account_stock_dict[code]))

            # for k, v in self.account_stock_dict.items():
            #     print("key is %s and its values [%s]" % (k, v))

            if sPrevNext == "2":
                self.detail_account_myStock(sPrevNext="2", first=False)
            else:
                self.detail_account_info_loop.exit()

        elif sRQName == "미체결요청":
            print("trData_slot의 미체결요청에 들어옴")

            cnt = self.dynamicCall("GetRepeatCnt(String, String)", sTrCode, sRQName)

            for i in range(cnt):
                # A002233이런식의 출력, strip는 strip(...)에서 ...안의 문자열을 문자의 양끝에 있을시 제거해 준다. 만약 공백이면 빈칸을 제거한다.
                code = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목명")
                orderNumber = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "쳬결번호")
                orderStatus = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i,
                                                  "주문상태")
                orderQunat = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "주문수량")
                orderPrice = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i,
                                              "주문가격")
                orderGubun = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i,
                                                 "주문구분")
                outstanding = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "미체결수량")
                chekyel = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "쳬결량")

                code = code.strip()
                code_name = code_name.strip()
                orderNumber = int(orderNumber.strip())
                orderStatus = orderStatus.strip()
                orderQunat = int(orderQunat.strip())
                orderPrice = int(orderPrice.strip())
                orderGubun0 = orderGubun.strip().lstrip('+').lstrip('-')
                print(orderGubun)
                print(orderGubun0)
                outstanding = int(outstanding.strip())
                chekyel = int(chekyel.strip())

                if orderNumber not in self.outstanding_stock_dict:
                    self.outstanding_stock_dict[orderNumber] = {
                        "종목코드": code,
                        "종목명": code_name,
                        "주문상태": orderStatus,
                        "주문가격": learn_rate,
                        "주문구분": current_price,
                        "주문수량": total_bought_stock_price,
                        "미체결수량": possible_quantity_to_sell,
                        "체결량":
                    }

    #OnReceiveChejan에 대한 서버로 부터 리시브받은 데이터 홀용하는 슬롯
    def chejan_slot(self, sGubun, nItenCnt, sFidList):
        sGubun = int(sGubun)

        if sGubun == 0:
            print("주문체결통보")

        elif sGubun == 1:
            print("잔고통보")

        else:
            print("특이신호")

    def login_slot(self, errCode):
        err = str(error_code(errCode))
        print("errorCode: %s" % err)  # 로그인 코드로 0이 들어올 때가 성공 아니면 실패

        if errCode == 0:
            self.login_event_loop.exit()
        else:
            pass
            #0이 아닐 시 오류를 핸들링하고 만약 그래도 안되는 문제면 프로그램을 종료시키는 코드 필요
    ##########################################################################################endOfSlots

    # 주식을 주문하는 함수
    def buy_stock(self):
        self.dynamicCall("SendOrder(String, String, String, int, String, int, int, String",
                         "신규매도")


    # 현재의 통신상태를 반환하는 함수
    # def checkCurrentConnectState(self):
    #     print("enter checkCurr")
    #     temp = self.dynamicCall("GetConnectState()")
    #     print(temp)

    def get_account_info(self):
        account_list = self.dynamicCall("GetLoginInfo(String)", 'ACCNO')
        print("가져온 raw 계좌번호 목록 %s" % str(account_list))
        self.account_num = int(account_list.split(';')[1])
        # print('나의 보유 계좌번호(모의투자계좌) %s 해당 계좌번호를 클래스 변수에 저장' % self.account_num)  # 8022731111

    def detail_account_info(self, first=False):
        print("예수금을 요청하는 함수 진입")

        # 여기선 tr데이터를 받을 때 서버로 어떤 입력값을 보낼지 결정하는 부분 tr데이터는 다 SetInputValue를 사용
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String", "조회구분", "2")

        # 여긴 입력된 값으로 무슨 요청을 할지 여긴 예수금 상세현황 요청을 하는 것이고
        # 내가정한 tr함수의 이름, tr번호, preNext, 화면번호
        self.dynamicCall("CommRqData(String, String, Int, String)", "예수금상세현황요청", "opw00001", "0", self.generalScreenNo)

        # 화면번호
        # 내가 원하는 화면번호를 만들고 거기의 요청의 묶음을 정할 수 있다 한 화면에 100개의 요청 묶음이 가능
        # 단 화면은 200개까지 만들 수 있고
        # ("DisconnectRealData(QString)", "2000")하면 화면 번호 내 데이터가 다 날라가고
        #  ("SetRealRemove(Qstring, QString)", "2000", "예수금상세현황요청") 하면 화면에 한 요청만 날라가고

        # 이벤트루프를 이용해 키움서버로부터 받은 테이터가 비동기적인 것을 동기화시켜서 코드 진행시키기
        self.detail_account_info_loop.exec_()

    def detail_account_myStock(self, sPrevNext="0", first=False):
        print("계좌평가잔고내역을 요청하는 함수 진입")


        # 여기선 tr데이터를 받을 때 서버로 어떤 입력값을 보낼지 결정하는 부분 tr데이터는 다 SetInputValue를 사용
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String", "비밀번호", 0000)
        self.dynamicCall("SetInputValue(String, String", "비밀번호입력매체구분", 00)
        self.dynamicCall("SetInputValue(String, String", "조회구분", 2)

        # 여긴 입력된 값으로 무슨 요청을 할지 여긴 예수금 상세현황 요청을 하는 것이고
        # 내가정한 tr함수의 이름, tr번호, preNext, 화면번호
        self.dynamicCall("CommRqData(String, String, Int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, "2000")

        # 이벤트루프를 이용해 키움서버로부터 받은 테이터가 비동기적인 것을 동기화시켜서 코드 진행시키기
        if first == True:
            self.detail_account_info_loop.exec_()

    def outstandingStock(self, sPrevNext="0"):
        '''
        미체결 종목을 받아오기 위해 요청을 보내는 함수
        :param sPrevNext: 굳이 필요없으나 통일성을 위해 넣우둠
        :return:
        '''
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String", "매매구분", "0")
        self.dynamicCall("SetInputValue(String, String", "체결구분", "1")
        self.dynamicCall("SetInputValue(String, String", "종목코드", "")

        self.dynamicCall("CommRqData(String, String, Int, String)", "미체결요청", "opt10075", sPrevNext, "2000")

        self.detail_account_info_loop.exec_()



    # 일봉 데이터를 받아와 언제 사야할지를 얘측하는 지표로 쓰려는 거지
    def day_kiwoom_db(self, code=None, date=None, sPrevNext='0'):

        self.dynamicCall("SetInputValue(String, String)", "종목코드", code)
        self.dynamicCall("SetInputValue(String, String)", "수정주가구분", "1")

        if date != None:
            self.dynamicCall("SetInputValue(String, String)", "기준일자", date)

        self.dynamicCall("CommRqData(String, String, int, String)", "주식일봉차트조회요청", "opt10081", sPrevNext, self.screen_calculation_stock)


    # 근데 현재 코스탁에 어떠한 종목들이 있는지 알지 못하니 이를 가져와야 할텐데 다행이 기타함수에서 종목가져올 수 있다.
    def get_event_from_market(self, market_event):
        '''
        종목코드들 반환
        :param market_event:
        :return:
        '''

        event_list = self.dynamicCall("GetCodeListByMarket(String", market_event) #"000120;001241;151124;"
        event_list = event_list.split(';')[:-1]

        return event_list

    def calculator_func(self):
        '''
        종목분석 실행용 함수
        :return:
        '''

        event_list = self.get_event_from_market("10")
        print("코스닥 개수 %s" % len(event_list))


    # tr요청 3.6초보다 빨리 가져오면 프로그램이 튕기는 문제가 발생한다>