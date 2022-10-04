#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
from time import sleep
import datetime
import signal
import threading

import picologging as logging

import lgpio
import spidev
import mqtt_pub

import csv

import pump_util as util
from pump_util import *
import pump_variables
from pump_variables import PV, pv
import config
import ml

logger = logging.getLogger(util.MAIN_LOGGER_NAME)

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

RUN_MODE_OUT = 17  #24v

M0_IN = 26  #cur_sw0
M1_IN = 19  #cur_sw1
M2_IN = 13  #cur_sw2

def set_run_mode(chip, v):
  '''
  아래 2개 중 어떤 모드를 출력해야 하나?
  (1) 수동/자동 모드
  (2) 수위계/AI
  '''
  lgpio.gpio_write(chip, RUN_MODE_OUT, v)


def get_motor_state(chip, m):
  '''m=0,1,2'''
  if m == 0:
    return lgpio.gpio_read(chip, M0_IN)
  elif m == 1:
    return lgpio.gpio_read(chip, M1_IN)
  elif m == 2:
    return lgpio.gpio_read(chip, M2_IN)
  #else:       
  #  return -1


def is_motor_running(chip):
  '''안쓰는 모터는 접점을 열어둬서 모터가 구동 안되는 것으로 인식하도록 해야 함'''
  return get_motor_state(chip, 0) or get_motor_state(
      chip, 1) or get_motor_state(chip, 2)


def get_all_motors(chip):
  """3대의 모터 상태를 (M2,M1,M0)로 리턴
  """
  #ms = [0, 0, 0]
  ms0 = lgpio.gpio_read(chip, M0_IN)
  ms1 = lgpio.gpio_read(chip, M1_IN)
  ms2 = lgpio.gpio_read(chip, M2_IN)

  logger.info("(MS0, MS1, MS2): (%d, %d, %d)", ms0, ms1, ms2)
  return (ms0, ms1, ms2)

def set_motor_state(chip, m, on_off):
  if m == 0:
    lgpio.gpio_write(chip, M0_OUT, on_off)
  elif m == 1:
    lgpio.gpio_write(chip, M1_OUT, on_off)
  elif m == 2:
    lgpio.gpio_write(chip, M2_OUT, on_off)

  logger.info("SET MOTOR#{%d}/(1,2,3) = {%d}", m + 1, on_off)


def set_all_motors(chip, m, pv):
  '''(M0, M1, M2)'''
  a, b, c = m
  lgpio.gpio_write(chip, M0_OUT, a)
  lgpio.gpio_write(chip, M1_OUT, b)
  lgpio.gpio_write(chip, M2_OUT, c)
  #pv.motor1 = c
  #pv.motor2 = b
  #pv.motor3 = a



def writeDAC(chip, v, spi):
  msb = (v >> 8) & 0x0F
  msb = msb | 0x30
  lsb = v & 0xFF

  lgpio.gpio_write(chip, CE_T, 0)
  spi.xfer2([msb, lsb])
  lgpio.gpio_write(chip, CE_T, 1)
  logger.debug("set_DAC({})".format(v))

def water_level_ADC(pv, rate):
  if rate<=0:
    v = pv.setting_4ma_ref
  elif rate>=100:
    v = pv.setting_20ma_ref
  else:
    v = pv.setting_4ma_ref + (rate/100) * (pv.setting_20ma_ref-pv.setting_4ma_ref)
  
  return v

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

def save_motor_state(chip):
  (m0,m1,m2) = get_all_motors(chip)
  config.save_motors((m0,m1,m2))

def get_temp():
    with open('/sys/devices/virtual/thermal/thermal_zone0/temp') as f:
        temp_str = f.read()

    try:
        return int(temp_str) / 1000
    except (IndexError, ValueError,) as e:
        raise RuntimeError('Could not parse temperature output.') from e

def tank_monitor(**kwargs):
  """수위 모니터링 스레드
  RepeatThread에서 주기적으로 호출되어 수위 입력을 처리함
  """

  chip = kwargs['chip']
  spi = kwargs['spi']
  sm = kwargs['sm']
  pv: PV = kwargs['pv']

  adc_level = check_water_level(chip, spi)
  time_now = datetime.datetime.now()
  logger.debug("monitor at {} : Water Level from ADC:{}".format(time_now.ctime(), adc_level))
  level = water_level_rate(pv, adc_level)

  last_level = pv.water_level

  logger.debug("level:%d", level)
  logger.debug("pv.setting_adc_invalid:%d", pv.setting_adc_invalid)
  (c,b,a) = get_all_motors(chip)
  pv.motor1 = a
  pv.motor2 = b
  pv.motor3 = c

  logger.debug("get_all_motors:(%d, %d, %d)", c,b,a)

  # 수위 입력이 없음
  logger.info(f"level:{level} rate:{water_level_rate(pv,pv.setting_adc_invalid)}")
  if level <= water_level_rate(pv, pv.setting_adc_invalid):  #100
    if pv.no_input_starttime is None:
      pv.no_input_starttime = time_now

    td = time_now - pv.no_input_starttime
    logger.info(f"Tolerance:{pv.setting_tolerance_to_ai}")
    logger.info(f"td.seconds:{td.seconds}")
    if td.seconds > pv.setting_tolerance_to_ai:  # 일정 시간 입력이 없으면
      logger.info(f"RUN_MODE:{pv.source} SOURCE_AI:{pump_variables.SOURCE_AI} SOURCE_SENSOR:{pump_variables.SOURCE_SENSOR}")
      if pv.source == pump_variables.SOURCE_SENSOR:
        pv.source = pump_variables.SOURCE_AI
        set_run_mode(chip, 1)
        #현재 회로 구성에서는 CFLOW_PASS를 사용 못하므로 항상 CFLOW_CPU 로 설정되어 있음
        #set_current_flow(chip=chip, cflow=CFLOW_CPU)

      #pv.water_level 
      temp= ml.get_future_level(time_now)
      if (not pv.water_level) and ml.train(pv=pv):
        pv.water_level = ml.get_future_level(pv=pv, t=time_now)
      else:
        logger.info("Training failed.")
        pv.water_level = last_level

      # get prediction from ML model
      # 예측 모델 적용할 때까지 임시
      if is_motor_running(chip):
        logger.debug("is_motor_running() true")
        pv.water_level += 2
      else:
        if pv.water_level > 0:
          pv.water_level -=2 
    else:
      pv.water_level = last_level  # 일시적인 현상으로 간주하고 level 값 버림
  else:  # 수위 입력이 있음
    # 예측모드에서 수위계모드로 변경
    logger.info(f"RUN_MODE:{pv.source} SOURCE_AI:{pump_variables.SOURCE_AI} SOURCE_SENSOR:{pump_variables.SOURCE_SENSOR}")
    if pv.source == pump_variables.SOURCE_AI:
      pv.source = pump_variables.SOURCE_SENSOR
      set_run_mode(chip, 0)

    pv.no_input_starttime = None
    pv.water_level = pv.filter_data(level)

  logger.info(f"op_mode:{pv.op_mode} level:{pv.water_level}, H:{pv.setting_high} L:{pv.setting_low} previous:{pv.previous_state}, index:{pv.motor_index}")
  if pv.op_mode == pump_variables.OP_AUTO:  # 설정값(LL,L,H,HH)에 따라 룰 기반으로 자동 운전
    logger.info("1")
    if pv.water_level >= pv.setting_high and pv.previous_state!=2:
      logger.info("2")
      if pv.motor1_mode > 0:
        set_motor_state(chip, 0, 0)
      if pv.motor2_mode > 0:
        set_motor_state(chip, 1, 0)
      if pv.motor_count>2 and pv.motor3_mode>0:
        set_motor_state(chip, 2, 0)
      pv.previous_state = 2
    elif pv.water_level <= pv.setting_low and pv.previous_state!=0:
      logger.info("3")
      logger.info(f"motor1:{pv.motor1_mode} index:{pv.motor_index}")
      if pv.motor_index==0:
        if pv.motor1_mode>0:
          logger.info("3.1")
          set_motor_state(chip, 0, 1)
          pv.motor_index = 1
        elif pv.motor2_mode>0:
          logger.info("3.2")
          set_motor_state(chip, 1, 1)
          pv.motor_index=2
        elif pv.motor_count>2 and pv.motor3_mode>0:
          logger.info("3.3")
          set_motor_state(chip, 2, 1)
          pv.motor_index=3
        if pv.motor_count>0:
          pv.motor_index = pv.motor_index % pv.motor_count
        else:
          pv.motor_index = 0
      elif pv.motor_index==1:
        logger.info("4")
        if pv.motor2_mode>0:
          set_motor_state(chip, 1, 1)
          pv.motor_index=2
        elif pv.motor_count>2 and pv.motor3_mode>0:
          set_motor_state(chip, 2, 1)
          pv.motor_index=3
        elif pv.motor1_mode>0:
          set_motor_state(chip, 0, 1)
          pv.motor_index=1
        if pv.motor_count>0:
          pv.motor_index = pv.motor_index % pv.motor_count
        else:
          pv.motor_index = 0
      elif pv.motor_count>2 and pv.motor_index==2:
        if pv.motor3_mode>0:
          set_motor_state(chip, 2, 1)
          pv.motor_index=3
        elif pv.motor1_mode>0:
          set_motor_state(chip, 0, 1)
          pv.motor_index=1
        elif pv.motor2_mode>0:
          set_motor_state(chip, 1, 1)
          pv.motor_index=2
        if pv.motor_count>0:
          pv.motor_index = pv.motor_index % pv.motor_count
        else:
          pv.motor_index = 0

      pv.previous_state = 0

  #mqtt_pub.mqtt_publish(topic=pv.mqtt_topic, level=str(pv.water_level), client=pv.mqtt_client)

  pv.append_data([
      time_now.strftime("%Y-%m-%d %H:%M:%S"), water_level_rate(pv, pv.water_level),
      get_motor_state(chip, 0),
      get_motor_state(chip, 1), get_motor_state(chip, 2), pv.source
  ])

  logger.debug(f"writeDAC(level:{level}, filtered:{pv.water_level})")
  #writeDAC(chip, level, spi)

  #writeDAC(chip, water_level_ADC(pv, pv.water_level), spi)
  writeDAC(chip, int(water_level_ADC(pv, level)), spi)
  sm.update_idle()

def water_sensor_monitor(**kwargs):
  """수위계 출력을 수위조절기에 전달
  * 성능검사를 위해 수위계 출력을 그래프 출력하기 위해 모니터링하며 mqtt로 전송
  """

  chip = kwargs['chip']
  spi = kwargs['spi']
  sm = kwargs['sm']
  pv: PV = kwargs['pv']

  if pv.source == pump_variables.SOURCE_AI:
    pv.source = pump_variables.SOURCE_SENSOR

  adc_level = check_water_level(chip, spi)
  time_now = datetime.datetime.now()
  logger.debug("monitor at {} : Water Level from ADC:{}".format(time_now.ctime(), adc_level))
  level = water_level_rate(pv, adc_level)

  #last_level = pv.water_level

  logger.debug("level:%d", level)
  logger.debug("pv.setting_adc_invalid:%d", pv.setting_adc_invalid)

  # 수위 입력이 없음
  if level < water_level_rate(pv, pv.setting_adc_invalid):  #100
    if pv.no_input_starttime is None:
      pv.no_input_starttime = time_now

    pv.no_input_starttime = None
    pv.water_level = pv.filter_data(level)

  pv.append_data([
      time_now.strftime("%Y-%m-%d %H:%M:%S"), water_level_rate(pv, pv.water_level),
  ])

  logger.debug(f"writeDAC(level:{level}, filtered:{pv.water_level})")

  writeDAC(chip, int(water_level_ADC(pv, level)), spi)
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

def init_motors(c):
    lgpio.gpio_claim_input(c, M0_IN, lFlags=lgpio.SET_PULL_UP)
    lgpio.gpio_claim_input(c, M1_IN, lFlags=lgpio.SET_PULL_UP)
    lgpio.gpio_claim_input(c, M2_IN, lFlags=lgpio.SET_PULL_UP)

def main():
  from pump_variables import PV, pv
  try:
    pv.instance = PV()  # pump variables

    chip = lgpio.gpiochip_open(0)
    #set_current_flow(chip=chip, cflow=CFLOW_CPU)
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
      logger.debug(
          "MCP3201 output code (MSB-mode): {}".foramt(ADC_output_code))
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