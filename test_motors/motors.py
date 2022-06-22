import logging
import lgpio

M0_OUT = 2  #24v
M1_OUT = 3  #24v
M2_OUT = 4  #24v

RUN_MODE_OUT = 17  #5v

M0_IN = 26  #cur_sw0
M1_IN = 19  #cur_sw1
M2_IN = 13  #cur_sw2


def set_run_mode(chip, v):
  lgpio.gpio_write(chip, RUN_MODE_OUT, v)


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
  """3대의 모터 상태를 (x,x,x)로 리턴
  """
  #ms = [0, 0, 0]
  ms0 = lgpio.gpio_read(chip, M0_IN)
  ms1 = lgpio.gpio_read(chip, M1_IN)
  ms2 = lgpio.gpio_read(chip, M2_IN)

  return (ms2, ms1, ms0)


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
  lgpio.gpio_write(chip, M0_OUT, c)
  lgpio.gpio_write(chip, M1_OUT, b)
  lgpio.gpio_write(chip, M2_OUT, a)

  logging.info(f"SET MOTORS{(M2_OUT, M1_OUT, M0_OUT)} = {(a,b,c)}")


#==============================================================================
# main
#==============================================================================
def main():
  chip = lgpio.gpiochip_open(0)  # get GPIO chip handle


if __name__ == '__main__':
  main()