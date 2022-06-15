import logging

import modbus_address as ma
import pump_variables

# 번지	  Description	         R/W	    기타
# 40001	  현재 수위	            읽기	%단위(0~100)
# 40002	  예측 수위	            읽기	%단위(0~100)
# 40003 	수위 모드	            읽기	0:현재 수위로 운전
#                                  1:예측 수위로 운전"
# 40004 	펌프1 상태	          읽기	0:펌프1 정지 1:펌프1 가동
# 40005 	펌프2 상태	          읽기	0:펌프2 정지 1:펌프2 가동
# 40006 	펌프3 상태	          읽기	0:펌프3 정지 1:펌프3 가동
# 40007 	spare	              읽기	
# 40008 	spare	              읽기	
# 40009 	spare	              읽기	
# 40010 	spare	              읽기	
# 40011 	수위H값(정지수위)       쓰기   %단위(0~100)
# 40012 	수위L값(가동수위)       쓰기	 %단위(0~100)
# 40013 	펌프운전모드	          쓰기	 0: 수동운전(펌프 제어값에 의한 운전)
#                                    1: 자동운전(수위 설정값에 의한 운전)
# 40014 	펌프1제어	            쓰기	  0:정지, 1:가동
# 40015 	펌프2제어	            쓰기	  0:정지, 1:가동
# 40016 	펌프3제어	            쓰기	  0:정지, 1:가동
# 40017 	펌프가동댓수(자동운전시)  쓰기	 1:1대, 2:2대, 3:3대

def respond(**kwargs):
    """Main 프로세스의 RespondThread에서 실행되는 Modbus 요청에 대한 응답 루틴
    """
    p_respond=kwargs['pipe']
    pv:pump_variables.PV = kwargs['pv']

    logging.info(f"Starting respond thread({kwargs})")
    while 1:
        logging.info(f"Receiving from Pipe:{p_respond}.......")
        msg = p_respond.recv()
        logging.info(f"Received from Pipe:{msg}")
        address, values = msg

        if address==ma.MBR_LEVEL_SENSOR:    #40001 현재 수위
          values = [pv.water_level]
        elif address==ma.MBR_LEVEL_AI:      #40002 예측 수위
          values = [pv.water_level]
        elif address==ma.MBR_AI_MODE:       #40003 수위 모드(0:현재수위, 1:예측수위)
          values = [pv.mode]
        elif address==ma.MBR_PUMP1_STATE:   #40004 펌프1 상태
          values = [pv.motor1]
        elif address==ma.MBR_PUMP2_STATE:   #40005 펌프2 상태
          values = [pv.motor2]
        elif address==ma.MBR_PUMP3_STATE:   #40006 펌프3 상태
          values = [pv.motor3]
        elif address==ma.MBW_RULE_UPPER:    #40011 수위 H값%(정지수위)
          values = [1]
        elif address==ma.MBW_RULE_LOWER:    #40012 수위 L값%(가동수위)
          values = [1]
        elif address==ma.MBW_PUMP_MODE:     #40013 펌프 운전 모드(0:수동운전, 1:자동운전)
          values = [1]
        elif address==ma.MBW_PUMP1_ON:      #40014 펌프1 ON=1, OFF=0
          values = [1]
        elif address==ma.MBW_PUMP2_ON:      #40015 펌프2 ON=1, OFF=0
          values = [1]
        elif address==ma.MBW_PUMP3_ON:      #40016 펌프3 ON=1, OFF=0
          values = [1]
        elif address==ma.MBW_PUMP_COUNT:    #40017 펌트가동대수(자동운전시)
          values = [1]
        else:
          values = []

        msg = (address, values)
        p_respond.send(msg)
        logging.info(f"sent: {msg}")