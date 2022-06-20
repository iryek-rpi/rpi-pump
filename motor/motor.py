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
M0_IN = 4  #24v
M1_IN = 17  #5v

def get_motor_state(chip, m):
  if m == 0:
    return lgpio.gpio_read(chip, M0_IN)
  elif m == 1:
    return lgpio.gpio_read(chip, M1_IN)
  else:
    return -1


def is_motor_running(chip):
  return get_motor_state(chip, M0_IN) or get_motor_state(chip, M1_IN)


def get_all_motors(chip):
  """2대의 모터 상태를 [x,x]로 리턴
  """
  #ms = [0, 0, 0]
  ms = [0, 0]
  if lgpio.gpio_read(chip, M0_IN):
    ms[0] = True
  if lgpio.gpio_read(chip, M1_IN):
    ms[1] = True
  #if lgpio.gpio_read(chip, M2):
  #  ms[2] = True
  return ms


def set_motor_state(chip, m, on_off):
  if m == 0:
    lgpio.gpio_write(chip, M0_OUT, on_off)
  elif m == 1:
    lgpio.gpio_write(chip, M1_OUT, on_off)

  logging.info("SET MOTOR{%d} = {%d}", m + 1, on_off)

#==============================================================================
# main
#==============================================================================
def main():
    chip = lgpio.gpiochip_open(0)  # get GPIO chip handle


if __name__ == '__main__':
  main()