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

M1_LEVEL_SENSOR = 1 #현재 수위 
M2_LEVEL_AI = 2     #예측 수위
M3_SOURCE = 3       #수위조절 모드(현재/예측)
M4_PUMP1_STATE = 4  #pump1 상태(on/off)
M5_PUMP2_STATE = 5  #pump2 상태(on/off)
M6_PUMP3_STATE = 6  #pump3 상태(on/off)
M7_MODBUS_ID = 7    #Modbus ID

M8_SPARE = 8 

M9_AUTO_HH = 9
M10_AUTO_LL = 10
M11_AUTO_H = 11     #수위 상한
M12_AUTO_L = 12     #수위 하한
M13_SPARE = 13   #Not used
M14_PUMP1_ON = 14   #pump1 on/off
M15_PUMP2_ON = 15   #pump2 on/off
M16_PUMP3_ON = 16   #pump3 on/off

M17_SPARE = 17

M18_PUMP_MODE_1 = 18  #pump1 제어모드 수동/자동
M19_PUMP_MODE_2 = 19  #pump2 제어모드 수동/자동
M20_PUMP_MODE_3 = 20  #pump3 제어모드 수동/자동

M21_SPARE = 21
M22_SPARE = 22
M23_SPARE = 23
M24_SPARE = 24

M25_MQTT_ON = 25 
M26_MQTT_TOPIC_AI = 26 
M27_MQTT_TIMEOUT = 27
M28_MQTT_PORT = 28
M29_MQTT_BROKER_IP_A = 29
M30_MQTT_BROKER_IP_B = 30
M31_MQTT_BROKER_IP_C = 31
M32_MQTT_BROKER_IP_D = 32
M33_DEVICE_ROLE = 33
M_END = 34

modbus_address_list = [
    M1_LEVEL_SENSOR, M2_LEVEL_AI, M3_SOURCE, M4_PUMP1_STATE,
    M5_PUMP2_STATE, M6_PUMP3_STATE, M7_MODBUS_ID, M8_SPARE, M9_AUTO_HH, M10_AUTO_LL,
    M11_AUTO_H, M12_AUTO_L, M13_SPARE, M14_PUMP1_ON,
    M15_PUMP2_ON, M16_PUMP3_ON, M17_SPARE, M18_PUMP_MODE_1, 
    M19_PUMP_MODE_2, M20_PUMP_MODE_3, M21_SPARE, M22_SPARE, M23_SPARE, M24_SPARE, 
    M25_MQTT_ON, M26_MQTT_TOPIC_AI, M27_MQTT_TIMEOUT, M28_MQTT_PORT, 
    M29_MQTT_BROKER_IP_A, M30_MQTT_BROKER_IP_B, 
    M31_MQTT_BROKER_IP_C, M32_MQTT_BROKER_IP_D, 
    M33_DEVICE_ROLE, M_END
]
