def error_code(err_code):
    err_dic = {
        1: ("CONNECTED", '서버와연결됨 및 정상처리'),
        0: ('OP_ERR_NONE', '정상처리'),
        -10: ('OP_ERR_FAIL', '실패'),
        -11: ('조건번호 없음'),
        -12: ('조건번호와 조건식 불일치'),
        -13: ('조건검색 조회요청 초과'),
        -100: ('OP_ERR_LOGIN', '사용자정보교환실패'),
        -101: ('OP_ERR_CONNECT', '서버접속실패'),
        -102: ('OP_ERR_VERSION', '버전처리실패'),
        -103: ('OP_ERR_FIREWALL', '개인방화벽실패'),
        -104: ('OP_ERR_MEMORY', '메모리보호실패'),
        -105: ('OP_ERR_INPUT', '함수입력값오류'),
        -106: ('OP_ERR_SOCKET_CLOSED', '통신연결종료'),
        -107: ('보안모듈오류'),
        -108: ('공인인증 로그인 필요'),
        -200: ('OP_ERR_SISE_OVERFLOW', '시세조회과부하'),
        -201: ('OP_ERR_RQ_STRUCT_FAIL', '전문작성초기화실패'),
        -202: ('OP_ERR_RQ_STRING_FAIL', '전문작성입력값오류'),
        -203: ('OP_ERR_NO_DATA', '데이터없음'),
        -204: ('OP_ERR_OVER_MAX_DATA', '조회가능한종목수초과'),
        -205: ('OP_ERR_RCV_FAIL', '데이터수신실패'),
        -206: ('OP_ERR_MAX_FID', '조회가능한종목수초과'),
        -207: ('OP_ERR_REAL_CANCEL', '실시간해제오류'),
        -209: ('시세조회제한'),
        -300: ('OP_ERR_ORD_WRONG_INPUT', '입력값오류'),
        -301: ('OP_ERR_ORD_WRONG_ACCOUNT', '계좌비밀번호없음'),
        -302: ('OP_ERR_OTHER_ACC_USE', '타인의계좌사용오류'),
        -303: ('OP_ERR_MIS_2BILL_EXC', '주문가격이20억을초과'),
        -304: ('OP_ERR_MIS_5BILL_EXC', '주문가격이50억을초과'),
        -305: ('OP_ERR_1PER_EXC', '주문수량이총발행주수의1%초과오류'),
        -306: ('OP_ERR_3PER_EXC', '주문수량이총발행주수의3%초과오류'),
        -307: ('OP_ERR_SEND_FAIL', '주문전송실패'),
        -308: ('OP_ERR_ORD_OVERFLOW', '주문전송과부하'),
        -309: ('OP_ERR_MIS_300CNT_EXC', '주문수량300계약초과'),
        -310: ('주문수량500계약초과'),
        -311: ('주문전송제한 과부하'),
        -340: ('OP_ERR_WRONG_ACCTINFO', '계좌정보없음'),
        -500: ('OP_ERR_ORD_SYMCODE_EMPTY', '종목코드없음')

    }

    result = err_dic[err_code]

    return result
