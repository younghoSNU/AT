import os
import sys # 프로그램종료를 위한 exit()사용
from PyQt5.QAxContainer import *  # Kiwoon클래스가 상속받는 QAxWidget클래스를 갖고 있다
from PyQt5.QtCore import *  # QEventLoop를 갖는다
from config.errorCode import error_code
from PyQt5.QtTest import *
from config.kiwoomType import *

class Kiwoom(QAxWidget):
    # container역할
    def __init__(self):
        super().__init__()

        print("++++++++++++++++\nenter Kiwoom class\n++++++++++++++++")

        self.realType = RealType()
        ################################################################### 이벤트 루프 모음
        self.login_event_loop = QEventLoop()
        self.detail_account_info_loop = QEventLoop()
        self.calculator_event_loop = QEventLoop()
        self.checkLastPageMyStock = False
        self.checkFirstPageMyStock = True
        ##################################################################################

        ################################################################## 스크린번호 모음
        self.generalScreenNo = "2000"
        self.screen_calculation_stock = "4000"
        self.screenRealTimeStock = "5000" # 종목별 할당할 스크린 번호
        self.screenMemeStock = "6000" # 종목별로 할당할 주문용 스크린 번호
        self.screenForStartStop = "7000"
        ##################################################################################

        #################################################################### 클래스 변수모음
        self.moeuiAccount_num = None
        self.account_stock_dict = {}
        self.outstanding_stock_dict = {}
        # 계좌관련 변수
        self.deposit = None
        ##임시
        self.use_money = None
        self.use_money_percent = 0.4
        ##
        self.currentCalcCode = None # GetCommData로 일봉차트조회요청 시 다음 600개를 가져오려면 계속 종목코드가 필요한데 이를 전역에 두었다.
        self.calcData = [] # 어떤 종목을 분석하기 이전에 데이터를 불러올텐데 600일치 데이터를 불러올때마다 이 리스트에 넣는다
        self.portfolioStockDict = {}
        self.todayJangoDict = {}
        ##################################################################################

        ############### 실행부분
        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()
        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info() #예수금상세현황요청
        self.detail_account_myStock(first=True)  # 계좌평가잔고내역요청
        self.outstandingStock()

        # 이제 실시간 주식시장에서의 데이터를 불러오기 위해 잠시 주석처리해놓는다
        # self.calculator_func()  # 종목분석을 위한 함수로 나중에는 실시간 부분을 하나 만들거다

        self.readCode()
        self.screenNumSetting()

        #장의 시작과 끝을 알려주는 신호를 받기 위해 사용한다
        self.dynamicCall("SetRealReg(String, String, String, String)", self.screenForStartStop, '',
                         self.realType.REALTYPE["장시작시간"]["장운영구분"], "0")

        for code in self.portfolioStockDict.keys():
            screenNum = self.portfolioStockDict[code]['스크린번호']
            fid = self.realType.REALTYPE['주식체결']['체결시간'] # 체결시간을 fid로 넣으면 fid가 포함된
                                                               # realtype의 모든 정보를 다 다 가져온다
            self.dynamicCall("SetRealReg(String, String, String, String)", screenNum, code, fid, '1')

    # PyQt5를 통해 키움 증권프로그램에 접속하기 위한 절차
    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")
        # print("commconnect %s" % self.dynamicCall("CommConnect()"))
        # dynamicCall자체로 그냥 호출에 대한 출력이 이뤄지기도 한다
        # 그런데 서버로부터 리턴을 받아야 출력이 될텐데 리턴을 못받는 경우와 받는 경우의 구분을 어떻게 하지?

        # ans. 로그인이 완료됐다는 키움서버응답을 받아야지만 다음 과정이 진행되도록 막는 기능을
        # 이벤트 루프를 만들었다가 제거하는 방식으로 한다.

        self.login_event_loop.exec_()  # 로그인이 완료될 때까지 기다려주도록 하는 코드

    #########################################################################################슬롯 등록 모음
    # 로그인, tr함수 호출 등에 사용하는 이벤트를 담는 함수
    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)  # 어떻게 self에 On...함수가 들어가 있지? Ans. Kiwoom이 QAxWidget을 상속받고 있어서
        # 이벤트를 걸어놔야 tr요청을 할 수 있고 이벤트는 다음의 진행을 블록하는 기능읗 하기에 원하는 일이 모두
        # 끝나면 이벤트를 종료시켜줘야 한다.
        # 이벤트의 종료는 키움서버에서 해당 요청에 대한 값을 주었을 때 이를 인식하고 발생하는 이벤트로
        # login_slot이 실행되고 그러면 그 slot안에서 발생시켰던 loop을 꺼줘야 다음 코드로 넘어같다.
        # 여기선 login_event_loop.exit()이다.
        self.OnReceiveTrData.connect(self.trData_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    #real이벤트와 그냥 이벤트의 차이가 머지? sol. 그냥 이벤트는 정보를 요청했을 때만 데이터를 주지만
    # real은 어떤 정보를 받을지 미리 SetRealReg를 이용해 등록한 데이터를 매틱마다 받는다.
    # 매 틱마다 받는다는 사실 기억하자. 그리고 컨스트럭터에 위 함수 추가 필요하다
    def real_event_slots(self):
        # 실시간 데이터를 받기 위해 이벤트를 생성
        self.OnReceiveRealData.connect(self.realData_slot)
        # 실시간 데이터들 중 RealType의 '잔고'와 '주문체결'데이터를 받는 다체결받은 시점이 언제인지 알려주는 이벤트
        self.OnReceiveChejanData.connect(self.chejan_slot)
    ##################################################################################################

    ########################################################################등록한 슬롯 모음############
    def login_slot(self, errCode):
        '''
        로그인 후 슬롯으로 성공여부 수신
        :param errCode: int타입
        :return:
        '''
        # print("errCode의 타입", type(errCode))
        err = error_code(errCode)
        print("errorCode:", err)  # 로그인 코드로 0이 들어올 때가 성공 아니면 실패

        if errCode == 0:
            self.login_event_loop.exit()
        else:
            print("프로그램을 종료합니다")
            sys.exit(0)

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

        #지금은 sRQName으로 받는 정보를 구분하고 있지만 이름을 줄일 수도 있겠다. e.g. alphabet
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "예수금")
            deposit = int(deposit)
            # print(deposit)
            # print("예수금 타입 %s " % type(deposit))
            # print("예수금 %s" % int(deposit))
            self.deposit = deposit
            self.use_money =  deposit * self.use_money_percent

            availMoney = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % int(availMoney))

            self.detail_account_info_loop.exit()

        elif sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_money = int(total_buy_money)

            total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate = float(total_profit_loss_rate)

            print("총매입금액 %s" % total_buy_money)
            print("총수익률(%%) %s" % total_profit_loss_rate)

            # 한번의 요청으로 수신한 데이터 수이며 아래에 GetCommData에서 idx부분에 사용
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
                self.detail_account_myStock(sPrevNext=sPrevNext)
            else:
                self.detail_account_info_loop.exit()

        elif sRQName == "미체결요청":
            cnt = self.dynamicCall("GetRepeatCnt(String, String)", sTrCode, sRQName)
            print("미체결종목 수", cnt)
            print("미체결 딕셔너리 엔트리 수", len(self.outstanding_stock_dict))

            for i in range(cnt):
                # A002233이런식의 출력, strip는 strip(...)에서 ...안의 문자열을 문자의 양끝에 있을시 제거해 준다. 만약 공백이면 빈칸을 제거한다.
                code = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목명")
                orderNumber = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "주문번호")
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
                orderNumber = orderNumber.strip()
                orderStatus = orderStatus.strip()
                orderQunat = int(orderQunat.strip())
                orderPrice = int(orderPrice.strip())
                orderGubun0 = orderGubun.strip().lstrip('+').lstrip('-')
                outstanding = int(outstanding.strip())
                chekyel = chekyel.strip()

                if orderNumber not in self.outstanding_stock_dict:
                    self.outstanding_stock_dict[orderNumber] = {
                        "종목코드": code,
                        "종목명": code_name,
                        "주문번호": orderNumber,
                        "주문상태": orderStatus,
                        "주문구분": orderGubun0,
                        "주문가격": orderPrice,
                        "주문가격": orderPrice,
                        "주문수량": orderQunat,
                        "미체결수량": outstanding,
                        "체결량": chekyel
                    }

            for idx, key in enumerate(self.outstanding_stock_dict):
                print(idx, key, self.outstanding_stock_dict[key])

            if sPrevNext == "2":
                self.outstandingStock(sPrevNext=sPrevNext)
            else:
                self.detail_account_info_loop.exit()

        elif sRQName == "주식일봉차트조회요청":
            print("주식일봉차트조회요청 진입 in trData_slot")
            # code = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "종목코드")
            # code = code.strip()
            # print("%s의 일봉데이터 요청" % self.currentCalcCode) # 이전에 dynamicCall에서 code가져오는 것에서 변경했다

            cnt = self.dynamicCall("GetRepeatCnt(String, String)", sTrCode, sRQName)
            print("GetRepeatCnt로 한번에 가져오는 데이터량 %s" % cnt) # 보통 600개 데이터를 있다면 한번에 가져온다

            date = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "일자")
            lastDate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, cnt-1, "일자")
            date = int(date.strip())
            lastDate = int(lastDate.strip())

            print("가져온 데이터의 처음 일자 ", date, "마지막 일자 ", lastDate)

            # data = self.dynamicCall("GetCommDataEx(String, String)" sTrCode, sRQName) 으로 데이터를 받으면
            # [['', '현재가', '거래량', '거래대금', ..., '저가', ''], ['', '현재가', '거래량', '거래대금', ..., '저가', ''], ...]
            for i in range(cnt):
                data = []

                currentPrice = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "현재가")
                tradeQunat = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "거래량")
                cumulQunat = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "거래대금") # 이제까지 거래량의 의한 총 거래된 금액
                date = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "일자")
                startPrice = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "시가")
                highPrice = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "고가")
                lowPrice = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "저가")

                data.append("") # 이것을 넣주는 것은 나중에 GetCommDataEx를 쓸 때가 있는데 이 때 데이터출력과 형식을 맞춰주기 위해서다
                data.append(currentPrice.strip())
                data.append(tradeQunat.strip())
                data.append(cumulQunat.strip())
                data.append(date.strip())
                data.append(startPrice.strip())
                data.append(highPrice.strip())
                data.append(lowPrice.strip())
                data.append("")

                self.calcData.append(data.copy()) #copy()를 하면 shallow copy가 되고 deep이려면 copy.deepcopy(리스트)

            print("calcData 개수 증가 확인하기", len(self.calcData))

            if sPrevNext == '2':
                self.day_kiwoom_db(code=self.currentCalcCode, sPrevNext=sPrevNext)
            else:
            #어떤 종목에 대한 데이터는 다 불러온 상황
            #이 데이터를 갖고 종목분석시작
                length = len(self.calcData)
                print("총일 수", length)

                passAllCond = False

                # 120일 이평선만들기 전에 120치 데이터가 잇는지 확인
                if length >= 120:   # 120일 이평선 만들기
                    totalPrice = 0

                    for value in self.calcData[:120]:
                        totalPrice += int(value[1])

                    movingAvaerage120 = totalPrice / 120 # 확인하려는 시작일을 기준으로 120일 이평선을 만들어

            # 다음의 조건들을 만족해야 그린빌법칙을 확인할 수 잇다

                    startPriceCond = False
                    savedStartHPrice = None
                    startDateLrice = int(self.calcData[0][7])
                    startDateHPrcie = int(self.calcData[0][6])

                    # 1. 확인하려는 시작일의 고가와 저가 사이에 120일이평선이 걸쳐있는지 확인
                    if movingAvaerage120 >= startDateLrice and movingAvaerage120 <= startDateHPrcie:
                        print("120일 이평선이 오늘자의 저가와 고가 사이에 걸쳐있어")
                        startPriceCond = True
                        savedStartHPrice = startDateHPrcie

                    # 2. 과거 일봉들 이 120일 이평선보다 밑에있는지 모두 확인
                    savedPastLPrice = None

                    if startPriceCond:
                        movingAvaerage120Past = 0
                        priceLineCond = False

                        idx = 1
                        while True:

                            if len(self.calcData[idx:]) < 120:
                                print("120일치 데이터가 없다.") # 계속 프린터를 해주고 마지막에 프린터는 다 지우는 방법도 좋아보여
                                break

                            totalPricePast = 0

                            for value in self.calcData[idx:120+idx]:
                                totalPricePast += int(value[1])

                            movingAvaerage120Past = totalPricePast / 120

                            if movingAvaerage120Past <= int(self.calcData[idx][6]) and idx <= 20:
                                print("과거 20일 동안 이평선을 넘는 주가 있엇으면 탈락")
                                break

                            elif int(self.calcData[idx][7]) > movingAvaerage120Past and idx > 20:
                                print("과거 20일보더 더 과거인 지점 중에서 일봉이 이평선보다 높은 때 확인")
                                priceLineCond = True
                                savedPastLPrice = int(self.calcData[idx][7])
                                break

                            idx += 1

                        #2.번 조건에 걸리는 부분 중 20일 이상 과거에서 2번을 만족하면 해당 부분 이평선이 가장 최근 일자의 이평선 가격보다 낮은지 확인
                        # 그리고 해당 부분의 주가가 현재의 주가보다 낮은지 확인
                        if priceLineCond:
                            if movingAvaerage120 > movingAvaerage120Past and savedStartHPrice > savedPastLPrice:
                                print("포착된 이평선")
                                passAllCond = True


                # passAllCond = True

                if passAllCond:
                    print("그린빌 매수 4법칙 통과한 종목확인됨")

                    code_nm = self.dynamicCall("GetMasterCodeName(String)", self.currentCalcCode)

                    f = open("files/condition_stock.txt", 'a', encoding="utf8")
                    f.write("%s\t%s\t%s\n" % (self.currentCalcCode, code_nm, str(self.calcData[0][1])))
                    f.close()

                else:
                    print("조건통과 못해서 파일에 추가 x")

                self.calcData.clear()
                self.calculator_event_loop.exit()

    # 매 틱인 0.02초 정도 마다 받아올 수도 잇는데 한번 시간 확인해봐라
    def realData_slot(self, sCode, sRealType, sRealData): # sRealData 사용 강의에선 안함
        if sRealType == "장시작시간":
            fid = self.realType.REALTYPE[sRealType]['장운영구분 ']
            value = self.dynamicCall("GetCommRealData(string, int", sCode, fid)

            if value == '0':
                print('장 시작 전')
            elif value == '3':
                print('장 시작')
            elif value == '2':
                print('장 장료, 동시호가로 넘어감')
            elif value == '4':
                print("3시30분 장 종료")

                for code in self.portfolioStockDict.keys():
                    self.dynamicCall("SetRealRemove(String, String)", self.portfolioStockDict[code]["스크린번호"], code)

                self.fileDelete()
                self.calculator_func()

                sys.exit()

        elif sRealType == '주식체결':
            a = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['체결시간'])  # 출력 HHMMSS
            b = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['현재가'])  # 출력 : +(-)2520
            b = abs(int(b))

            c = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['전일대비'])  # 출력 : +(-)2520
            c = abs(int(c))

            d = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['등락율'])  # 출력 : +(-)12.98
            d = float(d)

            e = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['(최우선)매도호가'])  # 출력 : +(-)2520
            e = abs(int(e))

            f = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['(최우선)매수호가'])  # 출력 : +(-)2515
            f = abs(int(f))

            g = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['거래량'])  # 출력 : +240124 매수일때, -2034 매도일 때
            g = abs(int(g))

            h = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['누적거래량'])  # 출력 : 240124
            h = abs(int(h))

            i = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['고가'])  # 출력 : +(-)2530
            i = abs(int(i))

            j = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['시가'])  # 출력 : +(-)2530
            j = abs(int(j))

            k = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['저가'])  # 출력 : +(-)2530
            k = abs(int(k))

            self.portfolio_stock_dict[sCode].update({"체결시간": a})
            self.portfolio_stock_dict[sCode].update({"현재가": b})
            self.portfolio_stock_dict[sCode].update({"전일대비": c})
            self.portfolio_stock_dict[sCode].update({"등락율": d})
            self.portfolio_stock_dict[sCode].update({"(최우선)매도호가": e})
            self.portfolio_stock_dict[sCode].update({"(최우선)매수호가": f})
            self.portfolio_stock_dict[sCode].update({"거래량": g})
            self.portfolio_stock_dict[sCode].update({"누적거래량": h})
            self.portfolio_stock_dict[sCode].update({"고가": i})
            self.portfolio_stock_dict[sCode].update({"시가": j})
            self.portfolio_stock_dict[sCode].update({"저가": k})

            # 보유종목으로 갖고 있고 오늘구매한 잔고에 없을 때
            if sCode in self.account_stock_dict.keys() and sCode not in self.todayJangoDict.keys():
                stockInfo = self.account_stock_dict[sCode]
                memeRate = (b - stockInfo['매입가']) / stockInfo['매입가'] * 100

                # 근데 매매가능수량이 0일수도 있나?
                if stockInfo['매매가능수량'] > 0 and (memeRate > 5 or memeRate < -5):
                    orderSuccessQ = self.dynamicCall(
                        'SendOrder(String, String, String, int, String, int, int, String, String',
                        ["신규매도",
                        self.portfolioStockDict[sCode]['주문용스크린번호'],
                        self.moeuiAccount_num,
                        2,
                        sCode,
                        stockInfo['매매가능수량'],
                        0,
                        self.realType.SENDTYPE['거래구분']['시장가'],
                        '']
                    )

                    if orderSuccessQ == 0:
                        print('주문이 정상적으로 이뤄짐')
                        del self.account_stock_dict[sCode]
                    else:
                        print("주문실패")

            elif sCode in self.todayJangoDict.keys():
                stockInfo = self.todayJangoDict[sCode]
                memeRate = (b - stockInfo['매입단가']) / stockInfo['매입단가'] * 100

                if stockInfo['주문가능수량'] > 0 and (memeRate > 5 or memeRate < -5):
                    orderSuccessQ = self.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        ["신규매도",
                        self.portfolioStockDict[sCode]["주문용스크린번호"],
                        self.moeuiAccount_num,
                        2,
                        sCode,
                        stockInfo['주문가능수량'],
                        0, #시잗가주문이나 취소주문일때는 가격을 0으로 입력한다
                        self.realType.SENDTYPE['거래구분']['시장가'],
                        ""]
                    )


                    if orderSuccessQ == 0:
                        print("매도주문 전달 성공")
                    else:
                        print("매도주문 전달 실패")

            elif d > 2.0 and sCode not in self.todayJangoDict.keys():
                print("매수조건 통과 %s " % sCode)

                buyNum = (self.use_money * 0.1) / e # e는 매도호가 인데 매도호가로 매수를 해버리면 바로 구매가 가능하니까
                buyNum = int(buyNum)

                orderSuccessQ = self.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    ["신규매수",
                    self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                    self.moeuiAccount_num,
                    1,
                    sCode,
                    buyNum,
                    e,
                    self.realType.SENDTYPE['거래구분']['지정가'],
                    ""]
                )

                if orderSuccessQ == 0:
                    print("매수주문 전달 성공")
                else:
                    print("매수주문 전달 실패")

            #미체결종목에 대해서 매수취소를 진행해준다
            michekyelStockDict = list(self.outstanding_stock_dict)

            for order_num in michekyelStockDict:
                code = self.michekyelStockDict[order_num]["종목코드"]
                meme_price = self.michekyelStockDict[order_num]['주문가격']
                not_quantity = self.michekyelStockDict[order_num]['미체결수량']
                order_gubun = self.michekyelStockDict[order_num]['주문구분']

                #매수하려난 가격이 (최우선)매도호가보다 더 크면 절대 주문체결이 안되니까
                if order_gubun == "매수" and not_quantity > 0 and e > meme_price:
                    orderSuccessQ = self.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        ["매수취소",
                        self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                        self.moeuiAccount_num,
                        3,
                        code,
                        0,
                        0,
                        self.realType.SENDTYPE['거래구분']['지정가'],
                        order_num]
                    )

                    if orderSuccessQ == 0:
                        print("미체결 매수취소 전달 성공")
                    else:
                        print("미체결 매수취소 전달 실패")

                elif not_quantity == 0:
                    del self.michekyelStockDict[order_num]

    #OnReceiveChejan에 대한 서버로 부터 리시브받은 데이터 홀용하는 슬롯
    def chejan_slot(self, sGubun, nItenCnt, sFidList):
        sGubun = int(sGubun)

        if sGubun == 0: #주문체결
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            stockName = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            stockName = stockName.strip()

            #원주문번호
            orOrderNo = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['원주문번호'])  # 출력 : defaluse : "000000"
            orderNo = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문번호'])  # 출럭: 0115061 마지막 주문번호
            orderStat = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태'])  # 출력: 접수, 확인, 체결
            orderQunat = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량'])  # 출력 : 3
            orderQunat = int(orderQunat)
            orderPrice = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격'])  # 출력: 21000
            orderPrice = int(orderPrice)
            michekyelQuant = self.dynamicCall("GetChejanData(int)",
                                              self.realType.REALTYPE['주문체결']['미체결수량'])  # 출력: 15, default: 0
            michekyelQuant = int(michekyelQuant)
            orderGubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])  # 출력: -매도, +매수
            orderGubun = orderGubun.strip().lstrip('+').lstrip('-')
            chekyelTime = self.dynamicCall("GetChejanData(int)",
                                           self.realType.REALTYPE['주문체결']['주문/체결시간'])  # 출력: '151028'
            chekyelPrice = self.dynamicCall("GetChejanData(int)",
                                            self.realType.REALTYPE['주문체결']['체결가'])  # 출력: 2110 default : ''

            if chekyelPrice == '':  # 아직 체결이 안된 상태
                chekyelPrice = 0
            else:
                chekyelPrice = int(chekyelPrice)
            chekyelQunat = self.dynamicCall("GetChejanData(int)",
                                            self.realType.REALTYPE['주문체결'['체결량']])  # 출력: 5 default: ''
            if chekyelQunat == '':
                chekyelQunat = 0
            else:
                chekyelQunat = int(chekyelQunat)

            currentPrice = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결'['현재가']])  # 출력: -6000
            currentPrice = abs(int(currentPrice))

            firstSellPrice = self.dynamicCall("GetChejanData(int)",
                                              self.realType.REALTYPE['주문체결'['(최우선)매도호가']])  # 출력: -6010
            firstSellPrice = abs(int(firstSellPrice))

            firstBuyPrice = self.dynamicCall("GetChejanData(int)",
                                             self.realType.REALTYPE['주문체결']['(최우선)매수호가'])  # 출력: -6000
            firstBuyPrice = abs(int(firstBuyPrice))

            # 주문이 되자마자 바로 구매되는 것이 아니라 확인 체결 작업을 거치기에 일단은 미체결상태로 존재하게 된다다
            if orderNo not in self.outstanding_stock_dict.keys():
                self.outstanding_stock_dict.update({orderNo: {}})

                self.outstanding_stock_dict[orderNo].update({"종목코드": sCode,
                                                             "주문번호": orderNo,
                                                             "종목명": stockName,
                                                             "주문상태": orderStat,
                                                             "주문수량": orderQunat,
                                                             "주문가격": orderPrice,
                                                             "미체결수량": michekyelQuant,
                                                             "원주문번호": orOrderNo,
                                                             "주문구분": orderGubun,
                                                             '주문/체결시간': chekyelTime,
                                                             "체결가": chekyelPrice,
                                                             "체결량": chekyelQunat,
                                                             "현재가": currentPrice,
                                                             "(최우선)매도호가": firstSellPrice,
                                                             "(최우선)매수호가": firstBuyPrice}
                                                            )
            print("주문체결 후 미체결종목리스트")
            print(self.outstanding_stock_dict)

        elif sGubun == 1:
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목코드'])[1:]

            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))

            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)

            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])
            buy_price = abs(int(buy_price))

            total_buy_price = self.dynamicCall("GetChejanData(int)",
                                               self.realType.REALTYPE['잔고']['총매입가'])  # 계좌에 있는 종목의 총매입가
            total_buy_price = int(total_buy_price)

            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도매수구분'])
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))

            if sCode not in self.todayJangoDict.keys():
                self.todayJangoDict.update({sCode: {}})

            self.todayJangoDict[sCode].update({"현재가": current_price})
            self.todayJangoDict[sCode].update({"종목코드": sCode})
            self.todayJangoDict[sCode].update({"종목명": stock_name})
            self.todayJangoDict[sCode].update({"보유수량": stock_quan})
            self.todayJangoDict[sCode].update({"주문가능수량": like_quan})
            self.todayJangoDict[sCode].update({"매입단가": buy_price})
            self.todayJangoDict[sCode].update({"총매입가": total_buy_price})
            self.todayJangoDict[sCode].update({"매도매수구분": meme_gubun})
            self.todayJangoDict[sCode].update({"(최우선)매도호가": first_sell_price})
            self.todayJangoDict[sCode].update({"(최우선)매수호가": first_buy_price})

            #체결이 된 후 잔고에서 빠져나간종ㅁ고으로 todayJangoDict에서 지운고 스크린번호도 지운다
            if stock_quan == 0:
                del self.todayJangoDict[sCode]
                self.dynamicCall("SetRealRemove(String, String)", self.portfolioStockDict[sCode]['스크린번호', sCode])
        else:
            print("특이신호")


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
        '''
        모의투자 계좌번호를 가져오는 함수
        :return:
        '''
        account_list = self.dynamicCall("GetLoginInfo(String)", 'ACCNO')
        serverGubun = self.dynamicCall("GetLoginInfo(String)", "GetServerGubun")

        print("가져온 raw 계좌번호 목록", account_list)

        if serverGubun == "1":
            print("접속서버는 모의투자")
        else:
            print("실거래서버 접속했으니 다시 접속합시다")
            sys.exit(0)

        self.moeuiAccount_num = int(account_list.split(';')[1])
        # print('나의 보유 계좌번호(모의투자계좌) %s 해당 계좌번호를 클래스 변수에 저장' % self.moeuiAccount_num)  # 8022731111

    def detail_account_info(self):
        print("detail_account_info 예수금을 요청하는 함수 진입")

        # 여기선 tr데이터를 받을 때 서버로 어떤 입력값을 보낼지 결정하는 부분 tr데이터는 다 SetInputValue를 사용
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.moeuiAccount_num)
        self.dynamicCall("SetInputValue(String, String", "비밀번호", 0000)
        self.dynamicCall("SetInputValue(String, String", "비밀번호입력매체구분", 00)
        self.dynamicCall("SetInputValue(String, String", "조회구분", 2)

        # 여긴 입력된 값으로 무슨 요청을 할지 여긴 예수금 상세현황 요청을 하는 것이고
        # 내가정한 tr함수의 이름, tr번호, preNext, 화면번호
        self.dynamicCall("CommRqData(String, String, Int, String)", "예수금상세현황요청", "opw00001", 0, self.generalScreenNo)

        # 화면번호
        # 내가 원하는 화면번호를 만들고 거기의 요청의 묶음을 정할 수 있다 한 화면에 100개의 요청 묶음이 가능
        # 단 화면은 200개까지 만들 수 있고
        # ("DisconnectRealData(QString)", "2000")하면 화면 번호 내 데이터가 다 날라가고
        #  ("SetRealRemove(Qstring, QString)", "2000", "예수금상세현황요청") 하면 화면에 한 요청만 날라가고

        # 이벤트루프를 이용해 키움서버로부터 받은 테이터가 비동기적인 것을 동기화시켜서 코드 진행시키기
        self.detail_account_info_loop.exec_()

    def detail_account_myStock(self, sPrevNext="0"):
        print("detail_account_myStock 계좌평가잔고내역을 요청하는 함수 진입")

        # 여기선 tr데이터를 받을 때 서버로 어떤 입력값을 보낼지 결정하는 부분 tr데이터는 다 SetInputValue를 사용
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.moeuiAccount_num)
        self.dynamicCall("SetInputValue(String, String", "비밀번호", 0000)
        self.dynamicCall("SetInputValue(String, String", "비밀번호입력매체구분", 00)
        self.dynamicCall("SetInputValue(String, String", "조회구분", 2)

        # 여긴 입력된 값으로 무슨 요청을 할지
        # 내가정한 tr함수의 이름, tr번호, preNext, 화면번호
        self.dynamicCall("CommRqData(String, String, Int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.generalScreenNo)

        # 이벤트루프를 이용해 키움서버로부터 받은 테이터가 비동기적인 것을 동기화시켜서 코드 진행시키기
        if sPrevNext == "0":
            self.detail_account_info_loop.exec_()

    def outstandingStock(self, sPrevNext="0"):
        '''
        미체결 종목을 받아오기 위해 요청을 보내는 함수
        :param sPrevNext: 굳이 필요없으나 통일성을 위해 넣우둠
        :return:
        '''
        print("outstandingStock 미체결종목을 요청하는 함수에 진입")

        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.moeuiAccount_num)
        self.dynamicCall("SetInputValue(String, String", "매매구분", 0)
        self.dynamicCall("SetInputValue(String, String", "체결구분", 1)
        self.dynamicCall("SetInputValue(String, String", "종목코드", "")

        self.dynamicCall("CommRqData(String, String, Int, String)", "미체결요청", "opt10075", sPrevNext, self.generalScreenNo)

        self.detail_account_info_loop.exec_()

    # 일봉 데이터를 받아와 언제 사야할지를 얘측하는 지표로 쓰려는 거지
    def day_kiwoom_db(self, code=None, date=None, sPrevNext='0'):

        QTest.qWait(3600)

        self.dynamicCall("SetInputValue(String, String)", "종목코드", code)
        self.dynamicCall("SetInputValue(String, String)", "수정주가구분", "1")

        if date != None:
            self.dynamicCall("SetInputValue(String, String)", "기준일자", date)

        self.dynamicCall("CommRqData(String, String, int, String)", "주식일봉차트조회요청", "opt10081", sPrevNext, self.screen_calculation_stock)

        if sPrevNext == "0":
            self.calculator_event_loop.exec_()

    # 근데 현재 코스탁에 어떠한 종목들이 있는지 알지 못하니 이를 가져와야 할텐데 다행이 기타함수에서 종목가져올 수 있다.
    def get_code_list_from_market(self, sMakret):
        '''
        종목 코드들 반한
        :param market_code: 0은 코스피 10은 코스닥 50 konex 등
        :return: 해당 시장의 종목리스트
        '''

        code_list = self.dynamicCall("GetCodeListByMarket(String)", sMakret)
        code_list = code_list.split(";")[:-1]

        return code_list

    def calculator_func(self):
        '''
        종목분석을 진행하는 함수
        :return:
        '''

        kospiList = self.get_code_list_from_market(0) # 0을 넣주면 코스피 종목들만 리턴해준다
        listLen = len(kospiList)
        print("코스피 개수", listLen)

        for idx, kospiCode in enumerate(kospiList):
            self.dynamicCall("DisconnectRealData(String)", self.screen_calculation_stock)  # 꼭 끝어주는 것은 아니나 필요함

            print("%s / %s: KOSPI STOCK CODE: %s is updating..." % (idx+1, listLen, kospiCode))
            self.currentCalcCode = kospiCode
            self.day_kiwoom_db(code=kospiCode)
    # tr요청 3.6초보다 빨리 가져오면 프로그램이 튕기는 문제가 발생한다>

    def readCode(self):
        if os.path.exists("files/condition_stock.txt"):
            f = open("files/condtion_stock.txt", "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")

                    code = ls[0]
                    codeName = ls[1]
                    codePrice = int(ls[2][:-2])  # 8450\n이렇게 되어 있을 것이므로

                    self.portfolioStockDict.update({code: {"종목명": codeName, "현재가": codePrice}})

            f.close()

    # 미체결종목 portfolio에 있는 것들 종목 전체를 하나의 리스트에 넣어
    def screenNumSetting(self):

        screenOverwrite = []

        # 계좌평가잔고내역에 있는 종목
        for code in self.account_stock_dict.keys():
            if code not in screenOverwrite:
                screenOverwrite.append(code)

        # 미체결에 있는 종목
        for orderNum in self.outstanding_stock_dict.keys():
            code = self.outstanding_stock_dict[orderNum]["종목코드"]

            if code not in screenOverwrite:
                screenOverwrite.appned(code)

        # 포트폴리오에 있는 종목
        for code in self.portfolioStockDict.keys():
            if code not in screenOverwrite:
                screenOverwrite.append(code)


        # 스크린번호 할당
        cnt = 0
        for code in screenOverwrite:
            tempScreen = int(self.screenRealTimeStock)
            memeScreen = int(self.screenMemeStock)

            if (cnt % 50) == 0:
                tempScreen += 1
                self.screenRealTimeStock = str(tempScreen)

            if (cnt % 50) == 0:
                memeScreen += 1
                self.screenMemeStock = str(memeScreen)

            if code in self.portfolioStockDict.keys():
                self.portfolioStockDict[code].update({"스크린번호": self.screenRealTimeStock,
                                                      "주문용스크린번호": self.screenMemeStock})

            else:
                self.portfolioStockDict.update({code: {"스크린번호": self.screenMemeStock,
                                                       "주문용스크린번호": self.screenMemeStock}})

            cnt += 1
        print("포트폴리오 딕션어리에 전부 업뎃햇습니다.")
        print(self.portfolioStockDict)

    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        '''
        메시지 송수신하는 이벤트를 받는 슬롯
        :param sScrNo:
        :param sRQName:
        :param sTrCode:
        :param msg:
        :return:
        '''
        print("스크린: ", sScrNo, "요청이름:", sRQName, "tr코드: ", sTrCode, "메시지: ", msg)

    def fileDelete(self):
        if os.path.isfile("files/condition_stock.txt"):
            os.remove("files/condition_stock.txt")