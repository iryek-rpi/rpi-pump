import picologging as logging

import modbus_address as ma
import pump_variables
import pump_monitor
import config

import pump_util as util

logger = logging.getLogger(util.MODBUS_LOGGER_NAME)

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

logger = logging.getLogger(name=util.MODBUS_LOGGER_NAME)

def respond(**kwargs):
  """Main 프로세스의 RespondThread에서 실행되는 Modbus 요청에 대한 응답 루틴
    """
  p_respond = kwargs['pipe']
  pv: pump_variables.PV = kwargs['pv']
  chip = kwargs['chip']

  logger.info(f"Starting respond thread({kwargs})")
  while 1:
    logger.info(f"Receiving from Pipe:{p_respond}.......")
    msg = p_respond.recv()
    logger.info(f"Received from Pipe:{msg}")
    wr, address, count, values = msg

    if not wr:
      values = pv.get_modbus_sequence(address=address, count=count)
      logger.info(f"get modbus block: {values} at: {address}")
    else:
      pv.set_modbus_sequence(address=address, values=values)
      logger.info(f"set modbus block at {address}")

    msg = (address, values)
    p_respond.send(msg)
    logger.info(f"sent: {msg}")


def respond_old(**kwargs):
  """Main 프로세스의 RespondThread에서 실행되는 Modbus 요청에 대한 응답 루틴
    """
  p_respond = kwargs['pipe']
  pv: pump_variables.PV = kwargs['pv']
  chip = kwargs['chip']

  logger.info(f"Starting respond thread({kwargs})")
  while 1:
    logger.info(f"Receiving from Pipe:{p_respond}.......")
    msg = p_respond.recv()
    logger.info(f"Received from Pipe:{msg}")
    wr, address, count, values = msg
    address += 40000

    if address == ma.MBR_LEVEL_SENSOR:  # 현재 수위
      values = [pv.water_level]
    elif address == ma.MBR_LEVEL_AI:  # 예측 수위
      values = [pv.water_level]
    elif address == ma.MBR_SOURCE:  # 수위 모드(0:수위계:w, 1:예측수위)
      values = [pv.source]
    elif address == ma.MBR_PUMP1_STATE:  # 펌프1 상태
      #values = [pv.motor1]
      values = [pump_monitor.get_motor_state(pv.chip, 0)]
    elif address == ma.MBR_PUMP2_STATE:  # 펌프2 상태
      #values = [pv.motor2]
      values = [pump_monitor.get_motor_state(pv.chip, 1)]
    elif address == ma.MBR_PUMP3_STATE:  # 펌프3 상태
      #values = [pv.motor3]
      values = [pump_monitor.get_motor_state(pv.chip, 2)]
    elif address == ma.MBW_MODBUS_ID:  # MODBUS ID
      if not wr:
        values = [pv.modbus_id]
      else:
        pv.modbus_id = values[0]
        config.update_config('CONTROLLER', 'MODBUS_ID', pv.modbus_id)
    elif address == ma.MBW_AUTO_H:  # 수위 H값%(정지수위)
      if not wr:
        values = [pv.setting_high]
      else:
        pv.setting_high = values[0]
        config.update_config('CONTROLLER', 'AUTO_H', pv.setting_high)
    elif address == ma.MBW_AUTO_HH:  # 수위 H값%(정지수위)
      if not wr:
        values = [pv.setting_hh]
      else:
        pv.setting_hh = values[0]
        config.update_config('CONTROLLER', 'AUTO_HH', pv.setting_hh)
    elif address == ma.MBW_AUTO_L:  # 수위 L값%(가동수위)
      if not wr:
        values = [pv.setting_low]
      else:
        pv.setting_low = values[0]
        config.update_config('CONTROLLER', 'AUTO_L', pv.setting_low)
    elif address == ma.MBW_AUTO_LL:  # 수위 L값%(가동수위)
      if not wr:
        values = [pv.setting_ll]
      else:
        pv.setting_ll = values[0]
        config.update_config('CONTROLLER', 'AUTO_LL', pv.setting_ll)
    elif address == ma.MBW_SOLO_MODE:  # 작동 모드 (0:PLC운전 1:단독운전)
      if not wr:
        values = [pv.solo_mode]
      else:
        pv.solo_mode = values[0]
        config.update_config('CONTROLLER', 'SOLO_MODE', pv.solo_mode)
    elif address == ma.MBW_PUMP_OP_MODE:  # 펌프 운전 모드(0:수동운전, 1:자동운전)
      if not wr:
        values = [pv.op_mode]
      else:
        pv.op_mode = values[0]
        config.update_config('CONTROLLER', 'OP_MODE', pv.op_mode)
    elif address == ma.MBW_PUMP1_ON:  # 펌프1 ON=1, OFF=0
      if not wr:
        values = [pv.motor1]
      else:
        pump_monitor.set_motor_state(chip, 0, values[0], pv)
    elif address == ma.MBW_PUMP2_ON:  # 펌프2 ON=1, OFF=0
      if not wr:
        values = [pv.motor2]
      else:
        pump_monitor.set_motor_state(chip, 1, values[0], pv)
    elif address == ma.MBW_PUMP3_ON:  # 펌프3 ON=1, OFF=0
      if not wr:
        values = [pv.motor3]
      else:
        pump_monitor.set_motor_state(chip, 2, values[0], pv)
#    elif address == ma.MBW_PUMP_COUNT:  # 펌트 가용 대수(자동운전시)
#      if not wr:
#        values = [pv.motor_count]
#      else:
#        pv.motor_count = values[0]
#        config.update_config('CONTROLLER', 'MOTOR_COUNT', pv.motor_count)
    #elif address == ma.MBW_PUMP_VALID:  # 유효한 모터(101 => motor#1 & motor#3)
    #  v = values[0]
    #  pv.motor_valid = []
    #  if v // 100:
    #    pv.motor_valid.append(1)
    #  if (v // 10) % 10:
    #    pv.motor_valid.append(2)
    #  if v % 10:
    #    pv.motor_valid.append(3)
    #
    #  if not len(pv.motor_valid):
    #    pv.motor_valid = [1]
    else:
      values = []

    msg = (address, values)
    p_respond.send(msg)
    logger.info(f"sent: {msg}")
