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
import motor
import ADC


logger = logging.getLogger(util.MAIN_LOGGER_NAME)

def tank_monitor(**kwargs):
  """수위 모니터링 스레드
  RepeatThread에서 주기적으로 호출되어 수위 입력을 처리함
  """
  chip = kwargs['chip']
  spi = kwargs['spi']
  sm = kwargs['sm']
  pv: PV = kwargs['pv']

  time_now = datetime.datetime.now()
  adc_level = ADC.check_water_level(chip, spi)
  if adc_level<pv.adc_invalid_rate:
    adc_level = 0

  level_rate = pv.water_level_rate(adc_level)
  orig_level_rate = pv.water_level

  #if pv.previous_adc == 0 or (abs(pv.previous_adc-adc_level)>30) or (not pv.no_input_starttime):
  if pv.previous_adc == 0  or (not pv.no_input_starttime):
    pv.previous_adc = adc_level
    pv.no_input_starttime = time_now

  logger.info("")
  logger.info(f"ADC:{adc_level} previous_adc:{pv.previous_adc} level_rate:{level_rate} orig_level_rate:{orig_level_rate}")# invalid rate:{invalid_rate}")

  (c,b,a) = motor.get_all_motors(chip)
  pv.motor1 = a
  pv.motor2 = b
  pv.motor3 = c

  logger.debug("get_all_motors:(%d, %d, %d)", a,b,c)

  # 수위 입력이 없음
  if abs(adc_level-pv.previous_adc)<30:  
    td = time_now - pv.no_input_starttime
    logger.info(f"td.seconds:{td.seconds} Tolerance:{pv.setting_tolerance_to_ai}")
    if (td.seconds >= pv.setting_tolerance_to_ai):  # 일정 시간 입력이 없으면
      logger.info(f"RUN_MODE:{pv.source} SOURCE_AI:{pump_variables.SOURCE_AI} SOURCE_SENSOR:{pump_variables.SOURCE_SENSOR}")
      if pv.source == pump_variables.SOURCE_SENSOR:
        pv.source = pump_variables.SOURCE_AI
        set_run_mode(chip, 1)
      #temp= ml.get_future_level(time_now)
      #if (not pv.water_level) and ml.train(pv=pv):
      if 1: #ml.train(pv=pv):
        pv.water_level = 100 #ml.get_future_level(pv=pv, t=time_now)
        logger.info(f"predicted level: {pv.water_level}")
      else:
        logger.info("Training failed.")
        pv.water_level = orig_level_rate

      # get prediction from ML model
      # 예측 모델 적용할 때까지 임시
      if is_motor_running(chip):
        logger.debug("is_motor_running() true")
        pv.water_level += 2
      else:
        if pv.water_level > 0:
          pv.water_level -=2 
    else:
      pv.water_level = orig_level_rate  # 일시적인 현상으로 간주하고 level 값 버림
  else:  # 수위 입력이 있음
    # 예측모드에서 수위계모드로 변경
    logger.info(f"RUN_MODE:{pv.source} SOURCE_AI:{pump_variables.SOURCE_AI} SOURCE_SENSOR:{pump_variables.SOURCE_SENSOR}")
    if pv.source == pump_variables.SOURCE_AI:
      pv.source = pump_variables.SOURCE_SENSOR
      set_run_mode(chip, 0)

    pv.previous_adc = adc_level
    pv.no_input_starttime = time_now
    pv.water_level = pv.filter_data(level_rate)

  determine_motor_state(pv, chip)

  pv.append_data([
      time_now.strftime("%Y-%m-%d %H:%M:%S"), pv.water_level,
      motor.get_motor_state(chip, 0),
      motor.get_motor_state(chip, 1), get_motor_state(chip, 2), pv.source
  ])

  logger.debug(f"writeDAC(level_rate:{level_rate}, filtered:{pv.water_level})")

  ADC.writeDAC(chip, int(ADC.waterlevel_rate2ADC(pv, level_rate)), spi)
  sm.update_idle()

def determin_motor_state(pv, chip):
  logger.info(f"op_mode:{pv.op_mode} pv.water_level:{pv.water_level}, H:{pv.setting_high} L:{pv.setting_low} previous:{pv.previous_state}, index:{pv.motor_index}")
  if pv.op_mode == pump_variables.OP_AUTO:  # 설정값(LL,L,H,HH)에 따라 룰 기반으로 자동 운전
    logger.info("1")
    if pv.water_level >= pv.setting_high and pv.previous_state!=2:
      logger.info("2")
      if pv.motor1_mode > 0:
        motor.set_motor_state(chip, 0, 0)
      if pv.motor2_mode > 0:
        motor.set_motor_state(chip, 1, 0)
      if pv.motor_count>2 and pv.motor3_mode>0:
        motor.set_motor_state(chip, 2, 0)
      pv.previous_state = 2
    elif pv.water_level <= pv.setting_low and pv.previous_state!=0:
      logger.info("3")
      logger.info(f"motor1:{pv.motor1_mode} index:{pv.motor_index}")
      if pv.motor_index==0:
        if pv.motor1_mode>0:
          logger.info("3.1")
          motor.set_motor_state(chip, 0, 1)
          pv.motor_index = 1
        elif pv.motor2_mode>0:
          logger.info("3.2")
          motor.set_motor_state(chip, 1, 1)
          pv.motor_index=2
        elif pv.motor_count>2 and pv.motor3_mode>0:
          logger.info("3.3")
          motor.set_motor_state(chip, 2, 1)
          pv.motor_index=3
        if pv.motor_count>0:
          pv.motor_index = pv.motor_index % pv.motor_count
        else:
          pv.motor_index = 0
      elif pv.motor_index==1:
        logger.info("4")
        if pv.motor2_mode>0:
          motor.set_motor_state(chip, 1, 1)
          pv.motor_index=2
        elif pv.motor_count>2 and pv.motor3_mode>0:
          motor.set_motor_state(chip, 2, 1)
          pv.motor_index=3
        elif pv.motor1_mode>0:
          motor.set_motor_state(chip, 0, 1)
          pv.motor_index=1
        if pv.motor_count>0:
          pv.motor_index = pv.motor_index % pv.motor_count
        else:
          pv.motor_index = 0
      elif pv.motor_count>2 and pv.motor_index==2:
        if pv.motor3_mode>0:
          motor.set_motor_state(chip, 2, 1)
          pv.motor_index=3
        elif pv.motor1_mode>0:
          motor.set_motor_state(chip, 0, 1)
          pv.motor_index=1
        elif pv.motor2_mode>0:
          motor.set_motor_state(chip, 1, 1)
          pv.motor_index=2
        if pv.motor_count>0:
          pv.motor_index = pv.motor_index % pv.motor_count
        else:
          pv.motor_index = 0

      pv.previous_state = 0

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

  adc_level = ADC.check_water_level(chip, spi)
  time_now = datetime.datetime.now()
  logger.debug("monitor at {} : Water Level from ADC:{}".format(time_now.ctime(), adc_level))
  level_rate = pv.water_level_rate(adc_level)

  logger.debug("level_rate:%d", level_rate)
  logger.debug("pv.setting_adc_invalid:%d", pv.setting_adc_invalid)

  # 수위 입력이 없음
  if level_rate < pv.water_level_rate(pv.setting_adc_invalid):  #100
    if pv.no_input_starttime is None:
      pv.no_input_starttime = time_now

    pv.no_input_starttime = None
    pv.water_level = pv.filter_data(level_rate)

  pv.append_data([
      time_now.strftime("%Y-%m-%d %H:%M:%S"), water_level_rate(pv, pv.water_level),
  ])

  logger.debug(f"writeDAC(level_rate:{level_rate}, filtered:{pv.water_level})")

  ADC.writeDAC(chip, int(ADC.waterlevel_rate2ADC(pv, level_rate)), spi)
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
    set_run_mode(c, 0)

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