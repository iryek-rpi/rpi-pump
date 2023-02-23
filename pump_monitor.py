#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
from time import sleep
import datetime
import signal
import threading

#import picologging as logging
import logging

import lgpio
import spidev
import mqtt_pub

import csv

import constant
import pump_util as util
from pump_util import *
import pump_variables
from pump_variables import PV, pv
import config
import ml
import motor
import ADC

logger = logging.getLogger(util.MAIN_LOGGER_NAME)

PUMP_INCREASE = 0.1  # pump 1개가 on 되어 있을 때 1초에 증가되는 수위 %

def tank_monitor(**kwargs):
  """수위 모니터링 스레드
  RepeatThread에서 주기적으로 호출되어 수위 입력을 처리함
  """
  chip = kwargs['chip']
  spi = kwargs['spi']
  sm = kwargs['sm']
  pv: PV = kwargs['pv']
  ns = kwargs['ns']  # multiprocessing manager namespace
  ev_req = kwargs['ev_req']
  ev_ret = kwargs['ev_ret']

  logger.info("\n<<< Entering pump_monitor() ===========================")

  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
  adc_level = ADC.check_water_level(chip, spi)
  if adc_level < 300:  #pv.adc_invalid_rate:
    adc_level = 0

  level_rate = pv.water_level_rate(adc_level)
  pv.sensor_level = level_rate
  _last_stored_level = pv.return_last_or_v(v=level_rate)

  #if pv.previous_adc == 0 or (abs(pv.previous_adc-adc_level)>30) or (not pv.no_input_starttime):
  #if pv.previous_adc == 0  or (not pv.no_input_starttime):
  # previous_adc : 수위입력이 있을 때만 갱신됨
  # no_input_starttime : 수위입력이 있을 때만 갱신됨
  if not pv.no_input_starttime:  # 초기화가 필요한 경우
    logger.info(
        f"INIT: previous_adc:{pv.previous_adc} no_input:{pv.no_input_starttime}"
    )
    pv.previous_adc = adc_level
    pv.no_input_starttime = time_now

  logger.info(
      f"ADC:{adc_level} level_rate:{level_rate:.1f}" 
  )  # invalid rate:{invalid_rate}")

  logger.info(
      f"previous_adc:{pv.previous_adc} previous_rate:{pv.water_level_rate(pv.previous_adc):.1f}" 
  )  # invalid rate:{invalid_rate}")
  logger.info(f"no_input_starttime:{pv.no_input_starttime}")

  (a, b, c) = motor.get_all_motors(chip, pv)
  logger.info("get_all_motors:(%d, %d, %d)", a, b, c)

  # 수위 입력이 없음
  if (abs(pv.water_level_rate(adc_level) - pv.water_level_rate(pv.previous_adc)) < 0.2) or (not adc_level):
    td = time_now - pv.no_input_starttime
    logger.info(
        f"td.seconds:{td.seconds} time_now:{time_now} no_input_time:{pv.no_input_starttime} Tolerance:{pv.setting_tolerance_to_ai}"
    )
    if (td.seconds >= pv.setting_tolerance_to_ai):  # 일정 시간 입력이 없으면
      logger.info(f"RUN_MODE:{pv.source} Info: AI=={constant.SOURCE_AI}")
      if pv.source == constant.SOURCE_SENSOR:
        logger.info(f"MONITOR: writing to pv.source:{constant.SOURCE_AI}")
        pv.source = constant.SOURCE_AI
        motor.set_run_mode(chip, constant.SOURCE_AI)

      fl = pv.get_future_level(time_str)
      if fl < 0:
        logger.info("No future level")

        if not pv.req_sent:
          # i = 입력이 중단되기 전의 data index
          i = pv.find_data(pv.no_input_starttime.strftime("%Y-%m-%d %H:%M:%S"))
          logger.info(
              f"find_data(no_input_starttime:{pv.no_input_starttime.strftime('%Y-%m-%d %H:%M:%S')})=>{i} time_str:{time_str}"
          )
          ltr = pv.data[:i + 1]  # 학습 데이터
          if len(ltr) < 20:
            logger.info(f"Case#0 : Not enough data: len(ltr):{len(ltr)}, Returning previous level...")
          else:
            ns.value = ltr
            ev_req.set()
            pv.req_sent = True
            logger.info("Case#1 : Request Training. Returning previous level...")
          pv.water_level = _last_stored_level
          logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
        elif ev_ret.is_set():
          ev_ret.clear()
          pv.req_sent = False
          pv.future_level = ns.value
          for i, l in enumerate(pv.future_level):
            if not util.repr_int(l[1]):
              for _, ll in enumerate(pv.future_level[i + 1:]):
                if util.repr_int(ll[1]):
                  l[1] = ll[1]
                  break

          logger.info("Forecast received")
          #logger.info(pv.future_level)
          pv.water_level = pv.get_future_level(time_str)
          logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
          logger.info(f"Got training result! - fl: {pv.water_level}"
                     )  #\nFuture Level: {pv.future_level}")
        else:
          logger.info(
              f'No case: req_sent:{pv.req_sent} ev_ret.is_set()={ev_ret.is_set()}'
          )
          pv.water_level = _last_stored_level
          logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
      else:  # get prediction from ML model
        logger.info(f"Got stored future level: {fl}")
        pv.water_level = fl
        logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
        #pv.water_level = level_rate  #pv.filter_data(level_rate)
    else:
      if level_rate>0:
        pv.water_level = level_rate  #pv.filter_data(level_rate)
      logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
      logger.info(f"less than tolerance: {td.seconds}<{pv.setting_tolerance_to_ai}")
      
    _num_busy_motors = len(pv.busy_motors)
    _diff = pv.water_level - _last_stored_level
    if pv.source == constant.SOURCE_AI:
      if _num_busy_motors:
        if _diff <= 0:
          logger.info(f'water_level:{pv.water_level:.1f} _last_stored_level:{_last_stored_level:.1f} _diff:{_diff:.1f}  _num_busy_motors:{_num_busy_motors}')
          if _diff>1: #너무 큰 값은 배제
            _diff=0
          if _num_busy_motors==1:
            pv.water_level += PUMP_INCREASE + _diff
          elif _num_busy_motors==2:
            pv.water_level += PUMP_INCREASE * 2 + _diff
          elif _num_busy_motors==3:
            pv.water_level += PUMP_INCREASE * 3 + _diff
          logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f} _diff:{_diff:.1f}  _num_busy_motors:{_num_busy_motors}")
      else: # 모터가 동작중이 아님
        if _diff > 0.1 and _diff < 0.5: # 수위가 높아짐
          logger.info(f'water_level:{pv.water_level:.1f} _last_stored_level:{_last_stored_level:.1f} _diff:{_diff:.1f}  _num_busy_motors:{_num_busy_motors}')
          pv.water_level = _last_stored_level # 수위를 이전 수위로 변경
  else:  # 수위 입력이 있음
    # 예측모드에서 수위계모드로 변경
    logger.info(
        f"Valid Input: RUN_MODE:{pv.source} info: SOURCE_AI=={constant.SOURCE_AI}"
    )
    if pv.source == constant.SOURCE_AI:
      logger.info(f"MONITOR: writing to pv.source:{constant.SOURCE_SENSOR}")
      pv.source = constant.SOURCE_SENSOR
      motor.set_run_mode(chip, constant.SOURCE_SENSOR)

    pv.previous_adc = adc_level
    pv.no_input_starttime = time_now
    pv.water_level = level_rate  #pv.filter_data(level_rate)
    logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")

  logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
  determine_motor_state_new(pv, chip)

  (m0, m1, m2) = motor.get_all_motors(chip, pv)

  pv.append_data([time_str, pv.water_level, m0, m1, m2, pv.source])

  logger.debug(
      f"writeDAC(level_rate:{level_rate:.1f}, pv.water_level:{pv.water_level:.1f})"
  )

  #ADC.writeDAC(chip, int(ADC.waterlevel_rate2ADC(pv, level_rate)), spi)
  ADC.writeDAC(chip, int(ADC.waterlevel_rate2ADC(pv, pv.water_level)), spi)
  sm.update_idle()


  #logger.info(" Leaving pump_monitor() ===========================>>>\n")
def determine_motor_state_new(pv, chip):
  logger.info(
      f"pv.water_level:{pv.water_level:.1f}, H:{pv.setting_high} L:{pv.setting_low}"
  )
  logger.info(f">> busy_motors:{pv.busy_motors}")
  logger.info(f">> idle_motors:{pv.idle_motors}")
  logger.info(f'>> previous_state:{pv.previous_state}')
  if pv.water_level > pv.setting_high:# and pv.previous_state != 2:
    for m in pv.busy_motors:  # 모든 모터를 off
      if m == 0 and pv.pump1_mode == constant.PUMP_MODE_AUTO:
        motor.set_motor_state(pv.chip, 0, 0)
      elif m == 1 and pv.pump2_mode == constant.PUMP_MODE_AUTO:
        motor.set_motor_state(pv.chip, 1, 0)
      elif m == 2 and pv.pump3_mode == constant.PUMP_MODE_AUTO:
        motor.set_motor_state(pv.chip, 2, 0)
      pv.change_motor_list(m, 0)
      pv.previous_state = 2
  elif pv.water_level < pv.setting_low and (len(pv.busy_motors)==0):# and pv.previous_state != 0:
    logger.info(f"len(pv.busy_motors:{len(pv.busy_motors)}")
    for m in pv.idle_motors:  # idle list에서 첫번째 모터만 on
      if m == 0 and pv.pump1_mode == constant.PUMP_MODE_AUTO:
        motor.set_motor_state(pv.chip, 0, 1)
        pv.previous_state = 0
        pv.change_motor_list(m, 1)
        break
      elif m == 1 and pv.pump2_mode == constant.PUMP_MODE_AUTO:
        motor.set_motor_state(pv.chip, 1, 1)
        pv.previous_state = 0
        pv.change_motor_list(m, 1)
        break
      elif m == 2 and pv.pump3_mode == constant.PUMP_MODE_AUTO:
        motor.set_motor_state(pv.chip, 2, 1)
        pv.previous_state = 0
        pv.change_motor_list(m, 1)
        break
  elif pv.water_level > pv.setting_low and pv.water_level < pv.setting_high:
    if pv.previous_state == 0:
      # fluctation을 보정할 조건 추가
      pv.previous_state = 1
    elif pv.previous_state==2:
      # fluctation을 보정할 조건 추가
      pv.previous_state = 1

  logger.info(f'<< previous_state:{pv.previous_state}')
  logger.info(f"<< busy_motors:{pv.busy_motors}")
  logger.info(f"<< idle_motors:{pv.idle_motors}")

def water_sensor_monitor(**kwargs):
  """수위계 출력을 수위조절기에 전달
  * 성능검사를 위해 수위계 출력을 그래프 출력하기 위해 모니터링하며 mqtt로 전송
  """

  chip = kwargs['chip']
  spi = kwargs['spi']
  sm = kwargs['sm']
  pv: PV = kwargs['pv']

  if pv.source == constant.SOURCE_AI:
    pv.source = constant.SOURCE_SENSOR

  adc_level = ADC.check_water_level(chip, spi)
  time_now = datetime.datetime.now()
  logger.debug("monitor at {} : Water Level from ADC:{}".format(
      time_now.ctime(), adc_level))
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
      time_now.strftime("%Y-%m-%d %H:%M:%S"),
      water_level_rate(pv, pv.water_level),
  ])

  logger.debug(f"writeDAC(level_rate:{level_rate}, filtered:{pv.water_level})")

  ADC.writeDAC(chip, int(ADC.waterlevel_rate2ADC(pv, level_rate)), spi)
  sm.update_idle()


def main():
  from pump_variables import PV, pv
  try:
    pv.instance = PV()  # pump variables

    chip = lgpio.gpiochip_open(0)
    #set_current_flow(chip=chip, cflow=CFLOW_CPU)
    pv().source = constant.SOURCE_SENSOR

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


trash = '''
4mA -> 726 -> 0.59v
       741 -> 0.6v
19.95mA -> 3900 -> 3.15v

32 -> 1.4
4.1 -> 0.7

SimonX
29 -> 5.8mA
0 -> 4.8mA
'''
#      if len(ltr) > 5:  #ml.train(pv=pv):
#        diff1 = (ltr[-1][1] - ltr[-2][1]) * 1.5
#        diff2 = (ltr[-2][1] - ltr[-3][1]) * 1.2
#        diff3 = (ltr[-3][1] - ltr[-4][1]) * 0.8
#        diff4 = (ltr[-4][1] - ltr[-5][1]) * 0.5
#
#        predicted = level_rate + (diff1 + diff2 + diff3 + diff4
#                                 ) // 4  #ml.get_future_level(pv=pv, t=time_now)
#        pv.water_level = predicted  #pv.filter_data(predicted)
#        logger.info(f"Predicted: {predicted} level:{level_rate} + avg:{(diff1+diff2+diff3+diff4)//4}")
#        logger.info(str(ltr[-5][1]))
#        logger.info(str(ltr[-4][1]))
#        logger.info(str(ltr[-3][1]))
#        logger.info(str(ltr[-2][1]))
#        logger.info(str(ltr[-1][1]))