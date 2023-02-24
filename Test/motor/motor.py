import picologging as logging
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

logger = logging.getLogger()

print(f"=================================================")
print(f"START at {datetime.datetime.now()}")
print(f"=================================================")

M0_OUT = 2  #24v
M1_OUT = 3  #24v
M2_OUT = 4  #24v

RUN_MODE_OUT = 17  #

M0_IN = 26  #cur_sw0
M1_IN = 19  #cur_sw1
M2_IN = 13  #cur_sw2


def init():
  c = lgpio.gpiochip_open(0)
  print(f"chip open return:{c}")
  r = lgpio.gpio_claim_input(c, M0_IN, lFlags=lgpio.SET_PULL_UP)
  print(f"return:{r}")
  r = lgpio.gpio_get_mode(c, M0_IN)
  print(f"mode:{r}")

  r = lgpio.gpio_claim_input(c, M1_IN, lFlags=lgpio.SET_PULL_UP)
  print(f"return:{r}")
  r = lgpio.gpio_get_mode(c, M1_IN)
  print(f"mode:{r}")

  r = lgpio.gpio_claim_input(c, M2_IN, lFlags=lgpio.SET_PULL_UP)
  print(f"return:{r}")
  r = lgpio.gpio_get_mode(c, M2_IN)
  print(f"mode:{r}")
  return c


def get_motor_in(chip, m):
  if m == 0:
    return lgpio.gpio_read(chip, M0_IN)
  elif m == 1:
    return lgpio.gpio_read(chip, M1_IN)
  elif m == 2:
    return lgpio.gpio_read(chip, M2_IN)
  else:
    return -1


def get_all_motors_in(chip):
  """2대의 모터 상태를 [x,x]로 리턴
  """
  #ms = [0, 0, 0]
  ms = [0, 0, 0]
  if lgpio.gpio_read(chip, M0_IN):
    ms[0] = True
  if lgpio.gpio_read(chip, M1_IN):
    ms[1] = True
  if lgpio.gpio_read(chip, M2_IN):
    ms[2] = True
  return ms


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

  print(f"SET MOTOR{m} = {on_off}")


def set_all_motors(chip, on_off):
  """모든 모터 상태를 설정
  """
  m = get_all_motors(chip)
  print(f"{m} = get_all_motors(chip={chip})")

  lgpio.gpio_write(chip, M0_OUT, on_off)
  lgpio.gpio_write(chip, M1_OUT, on_off)
  lgpio.gpio_write(chip, M2_OUT, on_off)

  m = get_all_motors(chip)
  print(f"{m} = get_all_motors(chip={chip})")


def set_each_motors(chip, m):
  a, b, c = m
  lgpio.gpio_write(chip, M0_OUT, a)
  lgpio.gpio_write(chip, M1_OUT, b)
  lgpio.gpio_write(chip, M2_OUT, c)

  print(f"SET MOTORS{(M0_OUT, M1_OUT, M2_OUT)} = {(a,b,c)}")


def set_mode(chip, m):
  lgpio.gpio_write(chip, RUN_MODE_OUT, m)
  print(f"set_mode{RUN_MODE_OUT} = {m}")


#==============================================================================
# main
#==============================================================================
def main():
  chip = lgpio.gpiochip_open(0)  # get GPIO chip handle


if __name__ == '__main__':
  main()
