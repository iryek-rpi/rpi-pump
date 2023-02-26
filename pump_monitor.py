#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
from time import sleep
import datetime
import random

#import picologging as logging
import logging

import lgpio
import spidev

import constant
import pump_util as util
from pump_util import *
from pump_variables import PV
import motor
import ADC

logger = logging.getLogger(util.MAIN_LOGGER_NAME)

PUMP_INCREASE = 0.1  # pump 1개가 on 되어 있을 때 1초에 증가되는 수위 %

adc0_start = None  # for simulation
adc0_duration = 0  # for simulation

def percent(_pv,adc):
  rate = 0.0
  if adc >= _pv.setting_20ma_ref:
    rate = 100.0
  elif adc < _pv.setting_4ma_ref:
    rate = 0.0
  else:
    rate = ((adc - _pv.setting_4ma_ref) /
            (_pv.setting_20ma_ref - _pv.setting_4ma_ref)) * 100.0
  return rate

def simulate_no_input(_adc_level, _pc_start, _adc0_start, _adc0_duration):
    '''adc 입력이 없는 경우를 시뮬레이션
    프로그램 시작 후 3~16분 이내에 시뮬레이션 시작
    시뮬레이션 시작 후 6~18분 동안 adc 입력이 없는 것으로 간주
    시뮬레이션 종료 후 다시 3~16분 이내에 시뮬레이션 시작

    pc_start = 실제 adc 입력 받은 지속 시간
    _adc0_start = 시뮬레이션 시작 시간
    _adc0_duration = adc 입력이 없는 것으로 유지할 시간

    return: _adc_level, _pc_start _adc0_start, _adc0_duration
    '''
    if (not _adc0_start):
      if (int(time.perf_counter() - _pc_start)//60 > random.randint(3,16)):
        _adc0_duration = random.randint(6,18)
        return 0, _pc_start, time.perf_counter(), random.randint(6,18)  #시뮬레이션 시작
      else:
        return _adc_level, _pc_start, _adc0_start, _adc0_duration  # 시뮬레이션 없음
    else:
      if int((time.perf_counter()-_adc0_start))//60 > _adc0_duration:
        return _adc_level, time.perf_counter(), None, 0  # 시뮬레이션 종료
      else:
        return 0, _pc_start, _adc0_start, _adc0_duration  # 시뮬레이션 유지

MONITOR_TIME_PREV = 0
MONITOR_TIME_NOW = 0

PREDICT_RATE = 5/420 # 420초(7분)에 5% 증감
PREDICT_ADC_DIFF = None

def tank_monitor(**kwargs):
  """수위 모니터링 스레드
  RepeatThread에서 주기적으로 호출되어 수위 입력을 처리함
  """
  global MONITOR_TIME_PREV
  global MONITOR_TIME_NOW
  global PREDICT_ADC_DIFF
  global adc0_start
  global adc0_duration

  chip = kwargs['chip']
  spi = kwargs['spi']
  sm = kwargs['sm']
  pv: PV = kwargs['pv']

  logger.info("\n<<< Entering pump_monitor() ===========================")

  if PREDICT_ADC_DIFF==None:
    # 450초에 5% 증감
    PREDICT_ADC_DIFF = ((pv.setting_20ma_ref - pv.setting_4ma_ref) * 0.05) / 450  

  MONITOR_TIME_NOW = time.perf_counter()
  if not MONITOR_TIME_PREV:
    MONITOR_TIME_PREV = MONITOR_TIME_NOW - 1.5
  time_diff = MONITOR_TIME_NOW - MONITOR_TIME_PREV

  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
  adc_level = ADC.check_water_level(chip, spi)
  logger.info(
      f"ADC:{adc_level} level_rate:{percent(pv, adc_level):.1f} time_diff:{time_diff:.1f}" 
  )  
  if adc_level < 300:  
    adc_level = 0

  if pv.simulation:
    logger.info(f'simulate: adc_level:{adc_level} adc_start_time:{pv.adc_start_time} adc0_start:{adc0_start} adc0_duration:{adc0_duration}')
    adc_level, pv.adc_start_time, adc0_start, adc0_duration = simulate_no_input(adc_level, pv.adc_start_time, adc0_start, adc0_duration)
    logger.info(f'simulate: adc_level:{adc_level} adc_start_time:{pv.adc_start_time} adc0_start:{adc0_start} adc0_duration:{adc0_duration}')

  level_rate = percent(pv, adc_level)
  pv.sensor_level = level_rate  # modbus에서 읽어가는 값
  _last_stored_level = pv.return_last_or_v(v=level_rate)

  # previous_adc : 수위 입력이 있을 때, 없을 때 모두 갱신됨
  # no_input_starttime : 수위입력이 있을 때만 갱신됨
  if not pv.no_input_starttime:  # 초기화가 필요한 경우
    logger.info(
        f"INIT: previous_adc:{pv.previous_adc} no_input:{pv.no_input_starttime}"
    )
    pv.previous_adc = adc_level
    pv.no_input_starttime = time_now

  logger.info(
      f"previous_adc:{pv.previous_adc} previous_rate:{percent(pv, pv.previous_adc):.1f}" 
  )
  logger.info(f"no_input_starttime:{pv.no_input_starttime}")

  (a, b, c) = motor.get_all_motors(chip, pv)
  logger.info("get_all_motors:(%d, %d, %d)", a, b, c)

  if not adc_level: # 수위 입력이 없는 경우
    logger.info(f"no input: adc: {adc_level} previous_adc:{pv.previous_adc}")
    logger.info(f"pv.water_level:{pv.water_level:.3f}")
    logger.info(f"PREDICT_ADC_DIFF:{PREDICT_ADC_DIFF:.3f} time_diff:{time_diff:.1f}")
    pv.source = constant.SOURCE_AI
    _adc_level_diff = time_diff*PREDICT_ADC_DIFF
    if not pv.busy_motors:
      _adc_level_diff *= -1
    pv.previous_adc += int(_adc_level_diff)
    pv.water_level = percent(pv, pv.previous_adc)
    logger.info(f"calculated: _water_level_diff:{_adc_level_diff:.3f}")
    logger.info(f"previous_adc:{pv.previous_adc} water_level:{pv.water_level:.3f}")
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

  ADC.writeDAC(chip, int(ADC.waterlevel_rate2ADC(pv, pv.water_level)), spi)

  MONITOR_TIME_PREV = MONITOR_TIME_NOW

  sm.update_idle()


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