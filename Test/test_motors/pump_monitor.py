#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
from time import sleep
import datetime
import signal
import random

import picologging as logging

import lgpio
import spidev

import csv

from pump_util import *
import pump_variables
from pump_variables import PV

FORMAT = ("%(asctime)-15s %(threadName)-15s"
          " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s")
logging.basicConfig(
    #format='%(asctime)s %(threadName) %(levelname)s:%(filename)s:%(message)s',
    format=FORMAT,
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()

#==============================================================================
# Device Properties
#==============================================================================

# /boot/firmware/config.txt
# Free CE0(8), CE1(7), and then control them as GPIO-7 & GPIO-8
# GPIO 24 & 25 are held by SPI driver. So they cannot be used for other purposes.
#   dtoverlay=spi0-2cs,cs0_pin=24,cs1_pin=25
CE_R = 7  # CE1
CE_T = 8  # CE0

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
    return lgpio.gpio_read(chip, M0_IN)
  elif m == 1:
    return lgpio.gpio_read(chip, M1_IN)
  elif m == 2:
    return lgpio.gpio_read(chip, M2_IN)
  else:
    return -1


def is_motor_running(chip):
  return get_motor_state(chip, M0_IN) or get_motor_state(
      chip, M1_IN) or get_motor_state(chip, M2_IN)


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

  logger.info("SET MOTOR{%d} = {%d}", m + 1, on_off)


def set_all_motors(chip, m):
  a, b, c = m
  lgpio.gpio_write(chip, M0_OUT, c)
  lgpio.gpio_write(chip, M1_OUT, b)
  lgpio.gpio_write(chip, M2_OUT, a)

  logger.info(f"SET MOTORS{(M2_OUT, M1_OUT, M0_OUT)} = {(a,b,c)}")


def writeDAC(chip, v, spi):
  msb = (v >> 8) & 0x0F
  msb = msb | 0x30
  lsb = v & 0xFF

  lgpio.gpio_write(chip, CE_T, 0)
  spi.xfer2([msb, lsb])
  lgpio.gpio_write(chip, CE_T, 1)
  logger.debug("set_DAC({})".format(v))


def water_level_rate(pv, wl=None):
  if wl == None:
    wl = pv.water_level

  rate = 0.0
  if wl >= pv.setting_20ma_ref:
    rate = 100.0
  elif wl < pv.setting_4ma_ref:
    rate = 0.0
  else:
    rate = ((wl - pv.setting_4ma_ref) /
            (pv.setting_20ma_ref - pv.setting_4ma_ref)) * 100.0

  return rate


def check_water_level(chip, spi):
  return readADC_MSB(chip, spi)


def readADC_MSB(chip, spi):
  """
  Reads 2 bytes (byte_0 and 1) and converts the output code from the MSB-mode:
  byte_0 holds two ?? bits, the null bit, and the 5 MSB bits (B11-B07),
  byte_1 holds the remaning 7 MBS bits (B06-B00) and B01 from the LSB-mode, 
  which has to be removed.
  """
  lgpio.gpio_write(chip, CE_R, 0)
  bytes_received = spi.xfer2([0x00, 0x00])
  lgpio.gpio_write(chip, CE_R, 1)

  #logger.debug("Read:0x{0:2X} 0x{1:2X}".format(bytes_received[0], bytes_received[1]) )
  #logger.debug("Read:0b{0:b} 0b{1:b}".format(bytes_received[0], bytes_received[1]) )

  MSB_1 = bytes_received[1]
  #logger.debug(f"MSB_1:0b{MSB_1:0b}")
  MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode
  #logger.debug(f"MSB_1:0b{MSB_1:0b}")
  MSB_0 = bytes_received[
      0] & 0b00011111  # mask the 2 unknown bits and the null bit
  #logger.debug(f"MSB_0:0b{bytes_received[0]:0b}")
  #logger.debug(f"MSB_0:0b{MSB_0:0b}")
  MSB_0 = MSB_0 << 7  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)
  #logger.debug(f"MSB_0<<7:0b{MSB_0:0b}")
  logger.debug(
      f"MSB_0+MSB_1:0b{MSB_0+MSB_1:0b} 0x{MSB_0+MSB_1:2X} {MSB_0+MSB_1}")
  return MSB_0 + MSB_1


def convert_to_voltage(adc_output, VREF=3.3):
  """
  Calculates analogue voltage from the digital output code (ranging from 0-4095)
  VREF could be adjusted here (standard uses the 3V3 rail from the Rpi)
  """
  return adc_output * (VREF / (2**12 - 1))


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


def tank_monitor(**kwargs):
  """수위 모니터링 스레드
  RepeatThread에서 주기적으로 호출되어 수위 입력을 처리함
  """

  chip = kwargs['chip']
  spi = kwargs['spi']
  sm = kwargs['sm']
  pv: PV = kwargs['pv']

  level = check_water_level(chip, spi)
  time_now = datetime.datetime.now()
  logger.debug("monitor at {}".format(time_now.ctime()))

  last_level = pv.water_level

  # 수위 입력이 없음
  if level < pv.setting_adc_invalid:  #100
    if pv.no_input_starttime is None:
      pv.no_input_starttime = time_now

    td = time_now - pv.no_input_starttime
    if td.seconds > pv.setting_tolerance_to_ai:  # 일정 시간 입력이 없으면
      if pv.source == pump_variables.SOURCE_SENSOR:
        pv.source = pump_variables.SOURCE_AI
        #현재 회로 구성에서는 CFLOW_PASS를 사용 못하므로 항상 CFLOW_CPU 로 설정되어 있음
        #set_current_flow(chip=chip, cflow=CFLOW_CPU)

      # get prediction from ML model
      # 예측 모델 적용할 때까지 임시
      if is_motor_running(chip):
        pv.water_level += 1
      else:
        pv.water_level -= 1
    else:
      pv.water_level = last_level  # 일시적인 현상으로 간주하고 level 값 버림
  else:
    #수위 입력이 있으면 예측모드에서 수위계모드로 변경
    if pv.source == pump_variables.SOURCE_AI:
      pv.source = pump_variables.SOURCE_SENSOR
      #현재 회로 구성에서는 CFLOW_PASS를 사용 못함
      #set_current_flow(chip=chip, cflow=CFLOW_PASS)

    pv.no_input_starttime = None
    pv.water_level = pv.filter_data(level)

  pv.append_data([
      time_now.strftime("%Y-%m-%d %H:%M:%S"), pv.water_level,
      get_motor_state(chip, 0),
      get_motor_state(chip, 1), 0, pv.source
  ])

  logger.debug(f"writeDAC(level:{level}, filtered:{pv.water_level})")
  #writeDAC(chip, level, spi)
  writeDAC(chip, pv.water_level, spi)
  sm.update_idle()


def init_spi_rw(chip, pv, speed=4800):
  #현재 회로 구성에서는 CFLOW_PASS를 사용 못함
  #set_current_flow(chip=chip, cflow=CFLOW_PASS)
  #set_current_flow(chip=chip, cflow=CFLOW_CPU)

  lgpio.gpio_claim_output(chip, CE_T, 1)
  lgpio.gpio_claim_output(chip, CE_R, 1)
  time.sleep(0.1)

  spi = spidev.SpiDev()
  spi.open(bus=0, device=0)
  spi.max_speed_hz = speed
  spi.mode = 0
  spi.no_cs = True

  return spi


def main():
  from pump_variables import PV, pv
  try:
    pv.instance = PV()  # pump variables

    chip = lgpio.gpiochip_open(0)
    #    set_current_flow(chip=chip, cflow=CFLOW_CPU)
    pv().source = SOURCE_SENSOR

    lgpio.gpio_claim_output(chip, CE_T, 1)
    lgpio.gpio_claim_output(chip, CE_R, 1)
    time.sleep(0.1)

    spi = spidev.SpiDev()
    spi.open(bus=0, device=0)
    spi.max_speed_hz = 4800
    spi.mode = 0
    spi.no_cs = True

    conn = Client(('localhost', 5999))

    while not is_shutdown:
      ADC_output_code = readADC_MSB(chip, spi)
      logger.debug("MCP3201 output code (MSB-mode): {}".foramt(ADC_output_code))
      ADC_voltage = convert_to_voltage(ADC_output_code)
      logger.debug("MCP3201 voltage: {%0.2f}V".format(ADC_voltage))
      conn.send(ADC_voltage)

      sleep(0.1)  # wait minimum of 100 ms between ADC measurements

      #writeDAC(chip=chip, v=ADC_voltage*100, spi=spi)
      #writeDAC(4020) # 4020 -> 1111 1011 0100
      sleep(2)
  except KeyboardInterrupt:
    time.sleep(0.1)
  finally:
    lgpio.gpiochip_close(chip)
    conn.close()


if __name__ == '__main__':
  is_shutdown = False

  #==============================================================================
  # systemd
  #==============================================================================
  def stop(sig, frame):
    logger.info(f"SIGTERM at {datetime.datetime.now()}")
    global is_shutdown
    is_shutdown = True

  def ignore(sig, frame):
    logger.info(f"SIGHUP at {datetime.datetime.now()}")

  signal.signal(signal.SIGTERM, stop)
  #signal.signal(signal.SIGHUP, stop)

  logger.info(f"=================================================")
  logger.info(f"START at {datetime.datetime.now()}")
  logger.info(f"=================================================")

  main()
'''
4mA -> 726 -> 0.59v
       741 -> 0.6v
19.95mA -> 3900 -> 3.15v

32 -> 1.4
4.1 -> 0.7

SimonX
29 -> 5.8mA
0 -> 4.8mA
'''