'''
motor control module
'''
import lgpio
#import picologging as logging
import logging
import pump_util as util
import constant

logger = logging.getLogger(util.MAIN_LOGGER_NAME)

#==============================================================================
# Device Properties
#==============================================================================

M0_OUT = 2  #24v
M1_OUT = 3  #24v
M2_OUT = 4  #24v

RUN_MODE_OUT = 17  #24v

M0_IN = 26  #cur_sw0
M1_IN = 19  #cur_sw1
M2_IN = 13  #cur_sw2


def init_motors(c):
  logger.info(f'init_motors({c})')
  r = lgpio.gpio_claim_input(c, M0_IN, lFlags=lgpio.SET_PULL_UP)
  logger.info(f'gpio_claim_input(M0_IN) return:{r}')
  r = lgpio.gpio_claim_input(c, M1_IN, lFlags=lgpio.SET_PULL_UP)
  logger.info(f'gpio_claim_input(M1_IN) return:{r}')
  lgpio.gpio_claim_input(c, M2_IN, lFlags=lgpio.SET_PULL_UP)
  logger.info(f'gpio_claim_input(M2_IN) return:{r}')

  #set_all_motors(c, (0,0,0))  # 단말 부팅 시 모터 초기화하지 않음
  #set_run_mode(c, 0)


def set_run_mode(chip, v):
  '''
  아래 2개 중 어떤 모드를 출력해야 하나?
  (1) 수동/자동 모드
  (2) 수위계/AI
  '''
  lgpio.gpio_write(chip, RUN_MODE_OUT, v)


def get_all_motors(chip, pv):
  """3대의 모터 상태를 (M2,M1,M0)로 리턴
  """
  #ms = [0, 0, 0]
  #if pv.source==constant.SOURCE_AI:
  #  ms0 = lgpio.gpio_read(chip, M0_IN)
  #  ms1 = lgpio.gpio_read(chip, M1_IN)
  #  ms2 = lgpio.gpio_read(chip, M2_IN)
  #else:
  #  s = pv.pump_state_plc
  #  ms0 = s & 1
  #  ms1 = s & 2
  #  ms2 = s & 4

  ms0 = lgpio.gpio_read(chip, M0_IN)
  ms1 = lgpio.gpio_read(chip, M1_IN)
  ms2 = lgpio.gpio_read(chip, M2_IN)

  return (ms0, ms1, ms2)


def get_motor_state(chip, m, pv):
  '''m=0,1,2'''
  #if pv.source==constant.SOURCE_AI:
  #  if m == 0:
  #    return lgpio.gpio_read(chip, M0_IN)
  #  elif m == 1:
  #    return lgpio.gpio_read(chip, M1_IN)
  #  elif m == 2:
  #    return lgpio.gpio_read(chip, M2_IN)
  #else:
  #  s = pv.pump_state_plc
  #  return s & (2**m)

  if m == 0:
    return lgpio.gpio_read(chip, M0_IN)
  elif m == 1:
    return lgpio.gpio_read(chip, M1_IN)
  elif m == 2:
    return lgpio.gpio_read(chip, M2_IN)

  return None


def is_motor_running(chip, pv):
  '''안쓰는 모터는 접점을 열어둬서 모터가 구동 안되는 것으로 인식하도록 해야 함'''
  return get_motor_state(chip, 0, pv) or get_motor_state(
      chip, 1, pv) or get_motor_state(chip, 2, pv)


def set_motor_state(chip, m, on_off):
  if m == 0:
    lgpio.gpio_write(chip, M0_OUT, on_off)
  elif m == 1:
    lgpio.gpio_write(chip, M1_OUT, on_off)
  elif m == 2:
    lgpio.gpio_write(chip, M2_OUT, on_off)

  logger.info("SET MOTOR#{%d}/(0,1,2) = {%d}", m, on_off)


def set_all_motors(chip, m):
  '''(M0, M1, M2)'''
  a, b, c = m
  lgpio.gpio_write(chip, M0_OUT, a)
  lgpio.gpio_write(chip, M1_OUT, b)
  lgpio.gpio_write(chip, M2_OUT, c)


#CFLOW_PASS = 0
#CFLOW_CPU = 1

#def set_current_flow(chip, cflow):
#  if cflow == CFLOW_PASS:
#    lgpio.gpio_write(chip, CSW0, 0)
#    lgpio.gpio_write(chip, CSW1, 0)
#    lgpio.gpio_write(chip, CSW2, 0)
#  else:
#    lgpio.gpio_write(chip, CSW0, 1)
#    lgpio.gpio_write(chip, CSW1, 1)
#    lgpio.gpio_write(chip, CSW2, 1)


