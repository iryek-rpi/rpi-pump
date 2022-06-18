"""MODBUS 주소 정의
"""
# 번지	  Description	         R/W	    기타
# 40001	  현재 수위	            읽기	%단위(0~100)
# 40002	  예측 수위	            읽기	%단위(0~100)
# 40003 	수위 모드	            읽기	0:수위계 수위로 운전
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

# 40018 	유효한 모터           쓰기	 100, 10, 1, 110, 11, 101, 111 (자리 수의 모터가 유효)

MBR_LEVEL_SENSOR = 40001
MBR_LEVEL_AI = 40002
MBR_SOURCE = 40003
MBR_PUMP1_STATE = 40004
MBR_PUMP2_STATE = 40005
MBR_PUMP3_STATE = 40006
MBW_AUTO_UPPER = 40011
MBW_AUTO_LOWER = 40012
MBW_PUMP_OP_MODE = 40013
MBW_PUMP1_ON = 40014
MBW_PUMP2_ON = 40015
MBW_PUMP3_ON = 40016
MBW_PUMP_COUNT = 40017
MBW_PUMP_VALID = 40018

modbus_address_list = [
    MBR_LEVEL_SENSOR, MBR_LEVEL_AI, MBR_SOURCE, MBR_PUMP1_STATE,
    MBR_PUMP2_STATE, MBR_PUMP3_STATE, MBW_AUTO_UPPER, MBW_AUTO_LOWER,
    MBW_PUMP_OP_MODE, MBW_PUMP1_ON, MBW_PUMP2_ON, MBW_PUMP3_ON, MBW_PUMP_COUNT,
    MBW_PUMP_VALID
]
