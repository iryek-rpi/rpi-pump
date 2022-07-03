import logging
import lgpio
import datetime

#==============================================================================
# 디버그용 로그 설정
#==============================================================================
FORMAT = ("%(asctime)-15s %(threadName)-15s"
          " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s")
logging.basicConfig(
    #format='%(asctime)s %(threadName) %(levelname)s:%(filename)s:%(message)s',
    format=FORMAT,
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info(f"=================================================")
logging.info(f"START at {datetime.datetime.now()}")
logging.info(f"=================================================")

M0_OUT = 2  #24v
M1_OUT = 3  #24v
M2_OUT = 4  #24v

RUN_MODE_OUT = 17  #

M0_IN = 26  #cur_sw0
M1_IN = 19  #cur_sw1
M2_IN = 13  #cur_sw2


def get_motor_state(chip, m):
  if m == 0:
    return lgpio.gpio_read(chip, M0_OUT)
  elif m == 1:
    return lgpio.gpio_read(chip, M1_OUT)
  elif m == 2:
    return lgpio.gpio_read(chip, M2_OUT)
  else:
    return -1


def is_motor_running(chip):
  return get_motor_state(chip, M0_OUT) or get_motor_state(
      chip, M1_OUT) or get_motor_state(chip, M2_OUT)


def get_all_motors(chip):
  """2대의 모터 상태를 [x,x]로 리턴
  """
  #ms = [0, 0, 0]
  ms = [0, 0, 0]
  if lgpio.gpio_read(chip, M0_OUT):
    ms[0] = True
  if lgpio.gpio_read(chip, M1_OUT):
    ms[1] = True
  if lgpio.gpio_read(chip, M2_OUT):
    ms[2] = True
  return ms


def set_motor_state(chip, m, on_off):
  if m == 0:
    lgpio.gpio_write(chip, M0_OUT, on_off)
  elif m == 1:
    lgpio.gpio_write(chip, M1_OUT, on_off)
  elif m == 2:
    lgpio.gpio_write(chip, M2_OUT, on_off)

  logging.info("SET MOTOR{%d} = {%d}", m + 1, on_off)


def set_all_motors(chip, m):
  a, b, c = m
  lgpio.gpio_write(chip, M0_OUT, a)
  lgpio.gpio_write(chip, M1_OUT, b)
  lgpio.gpio_write(chip, M2_OUT, c)

  logging.info(f"SET MOTORS{(M0_OUT, M1_OUT, M2_OUT)} = {(a,b,c)}")


#==============================================================================
# main
#==============================================================================
def main():
  chip = lgpio.gpiochip_open(0)  # get GPIO chip handle


if __name__ == '__main__':
  main()