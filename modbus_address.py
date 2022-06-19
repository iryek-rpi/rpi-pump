"""MODBUS 주소 정의
"""
# 번지	  Description	         R/W	    기타
# 40001	  현재 수위	            읽기	(0~1000)
# 40002	  예측 수위	            읽기	(0~1000)
# 40003 	수위 종류	            읽기	0:수위계 수위로 운전
#                                  1:예측 수위로 운전"
# 40004 	펌프1 상태	          읽기	0:펌프1 정지 1:펌프1 가동
# 40005 	펌프2 상태	          읽기	0:펌프2 정지 1:펌프2 가동
# 40006 	펌프3 상태	          읽기	0:펌프3 정지 1:펌프3 가동
# 40007 	spare	              읽기
# ...     spare               읽기
# 40020   Modbus 국번          쓰기    (1~100)
# 40021 	수위H값(정지수위)      쓰기   (0~1000)
# 40022   수위HH값(정지수위)     쓰기   (0~1000)
# 40023 	수위L값(가동수위)      쓰기	  (0~1000)
# 40024   수위LL값(가동수위)     쓰기   (0~1000)
# 40025   작동 모드             쓰기   0: PLC 모드
#                                   1: 단독 모드
# 40026 	펌프운전모드	         쓰기	 0: 수동운전(펌프 제어값에 의한 운전)
#                                  1: 자동운전(수위 설정값에 의한 운전)
# 40027 	펌프가용댓수(자동운전시) 쓰기	   1:1대, 2:2대, 3:3대
# 40028 	펌프1제어	            쓰기	  0:정지, 1:가동
# 40029 	펌프2제어	            쓰기	  0:정지, 1:가동
# 40030 	펌프3제어	            쓰기	  0:정지, 1:가동
#

MBR_LEVEL_SENSOR = 40001
MBR_LEVEL_AI = 40002
MBR_SOURCE = 40003
MBR_PUMP1_STATE = 40004
MBR_PUMP2_STATE = 40005
MBR_PUMP3_STATE = 40006
MBW_MODBUS_ID = 40020
MBW_AUTO_H = 40021
MBW_AUTO_HH = 40022
MBW_AUTO_L = 40023
MBW_AUTO_LL = 40024
MBW_SOLO_MODE = 40025
MBW_PUMP_OP_MODE = 40026
MBW_PUMP1_ON = 40027
MBW_PUMP2_ON = 40028
MBW_PUMP3_ON = 40029
MBW_PUMP_COUNT = 40030

modbus_address_list = [
    MBR_LEVEL_SENSOR, MBR_LEVEL_AI, MBR_SOURCE, MBR_PUMP1_STATE,
    MBR_PUMP2_STATE, MBR_PUMP3_STATE, MBW_MODBUS_ID, MBW_AUTO_H, MBW_AUTO_HH,
    MBW_AUTO_L, MBW_AUTO_LL, MBW_SOLO_MODE, MBW_PUMP_OP_MODE, MBW_PUMP1_ON,
    MBW_PUMP2_ON, MBW_PUMP3_ON, MBW_PUMP_COUNT
]
