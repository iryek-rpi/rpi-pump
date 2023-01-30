import threading
import queue
import datetime
import os
import pandas as pd
import csv

#import picologging as logging
import logging

import constant
import pump_util as util
import modbus_address as ma
import motor

import config

logger = logging.getLogger(util.MAIN_LOGGER_NAME)


def pv(inst=None):
  if inst != None:
    pv.instance = inst
  return pv.instance


pv.instance = None

# 수위 기록 주기
interval = {
    "1s": 1,
    "10s": 10,
    "30s": 30,
    "1min": 60,
    "3min": 180,
    "5min": 300,
    "10min": 600,
    "1hr": 3600
}

# AI 전환
no_input_tol = {
    "5min": 300,
    "10min": 600,
    "30min": 1800,
    "1hr": 3600,
    "2hr": 7200
}


class PV():

  def __init__(self):
    self.chip = -1

    self._mbl = [0 for _ in range(ma.M_END)]

    self.solo_mode = constant.MODE_PLC

    self.motor_index = 0
    self.previous_state = 1  # 0:low, 1:mid  3:high

    self.temperature = 0
    self.valid_motors = [] #cofig
    self.motor_valid = [0]  # 사용할 수 있는 모터 번호 리스트(0~2)
    self.motor_lead_time = 10
    self.idle_motors = []
    self.busy_motors = []

    self.req_sent = False  # training request flag
    self.no_input_starttime = None  # 입력이 안들어오기 시각한 시간
    self.previous_adc = None  # 이전 ADC reading 값
    self.data = []
    self.train = []
    self.future_level = None
    self.forecast = None
    self.lock = threading.Lock()

    # setting_monitor_interval 초기화 될 때 함께 초기화 됨)
    self._setting_max_train = constant.MAX_TRAIN_SAMPLES
    #3600 * 24 * 7 # 7일 # 3600*24*30 (1초 샘플링일 경우 30일)

    self.setting_4ma_ref = 700  # 4mA ADC 출력
    self.setting_20ma_ref = 4000  # 4000  # 20mA ADC 출력
    self.setting_4ma = 0.0  # 4mA 수위(수위계 캘리브레이션)
    self.setting_20ma = 100.0  # 20mA 수위(수위계 캘리브레이션)
    self._setting_adc_invalid = 100  # ADC 값이 이 값 이하이면 입력이 없는 것으로 간주함
    self.adc_invalid_rate = self.water_level_rate(
        self._setting_adc_invalid)  # %

    # 수위 기록 인터벌 1, 10, 30, 60(1min), 180(3min), 300(5min), 600(10min), 3600(1hr)
    # setting.ini에서 읽어와서 초기화 됨
    self._setting_monitor_interval = 5  # 수위 모니터링 주기(초)

    self.setting_save_interval = 60 * 60 * 24  # 저장 주기(초)
    self.setting_tolerance_to_ai = 10  #600  # AI 모드로 전환하기 위한 입력 없는 time(sec)
    self.setting_tolerance_to_sensor = 10  #600  # 수위계 입력 모드로 전환하기 위한 입력 유지 time(sec)
    self.setting_input_rate = 0.8  # tolerance 내 입력 비율
    self.setting_adc_ignore_spike = 100  # 이 값 이상의 급격한 입력 변동은 일시적인 것으로 간주하고 무시함
    
    self.setting_adc_avg_interval = 10  # 평균을 계산할 adc 입력 기간(sec)
    self.adc_avg_count = self.setting_adc_avg_interval // self._setting_monitor_interval
    if self.adc_avg_count < 1:
      self.adc_avg_count = 1

    self.q_level = queue.Queue(self.adc_avg_count)

    # ADC에는 adc_avg_count 개 수의 수위값이 입력되어 있어야 함(튀는 값을 상쇄하기 위해 평균을 내기 위한 데이터)
    # 초기에는 0으로 넣어둠
    self.lock.acquire()
    for _ in range(self.adc_avg_count):
      #self.q_level.put(self.setting_20ma_ref, block=False)
      self.q_level.put(0, block=False)
    self.lock.release()

    self.password = "rudakwkd"
    self.user_id = "hwan"
    self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                  'data')

  def water_level_rate(self, adc):
    rate = 0.0
    if adc >= self.setting_20ma_ref:
      rate = 100.0
    elif adc < self.setting_4ma_ref:
      rate = 0.0
    else:
      rate = ((adc - self.setting_4ma_ref) /
              (self.setting_20ma_ref - self.setting_4ma_ref)) * 100.0
    return rate

  @property
  def water_level(self):
    return self._mbl[ma.M2_LEVEL_AI] / 10.

  @water_level.setter
  def water_level(self, level):
    self._mbl[ma.M2_LEVEL_AI] = int(level * 10)

  @property
  def sensor_level(self):
    return self._mbl[ma.M1_LEVEL_SENSOR] / 10.

  @water_level.setter
  def sensor_level(self, level):
    self._mbl[ma.M1_LEVEL_SENSOR] = int(level * 10)

  @property
  def setting_monitor_interval(self):
    return self._setting_monitor_interval

  @setting_monitor_interval.setter
  def setting_monitor_interval(self, monitor_interval):
    self._seting_max_train = (60 * 60 * 24 * 30) // monitor_interval  #1개월
    self._setting_monitor_interval = monitor_interval

  @property
  def setting_max_train(self):
    return self._setting_max_train

  @property
  def setting_adc_invalid(self):
    return self._setting_adc_invalid

  @setting_adc_invalid.setter
  def setting_adc_invalid(self, v):
    self._setting_adc_invalid = v
    self.adc_invalid_rate = self.water_level_rate(v)

  @property
  def water_level_ai(self):
    return self._mbl[ma.M2_LEVEL_AI] / 10.

  @water_level_ai.setter
  def water_level_ai(self, level):
    self._mbl[ma.M2_LEVEL_AI] = int(level * 10)

  @property
  def source(self):
    return self._mbl[ma.M3_SOURCE]

  @source.setter
  def source(self, s):
    self._mbl[ma.M3_SOURCE] = s

  def change_motor_list(self, m, v):
    '''m = 0, 1, 2 (motor)
       v = 0,1 (current motor state)
    '''
    if not v:
      while True:
        if m in self.busy_motors:
          del self.busy_motors[self.busy_motors.index(m)]
        else:
          break

      if not m in self.idle_motors:
        self.idle_motors.append(m)
    else:
      while True:
        if m in self.idle_motors:
          del self.idle_motors[self.idle_motors.index(m)]
        else:
          break

      if not m in self.busy_motors:
        self.busy_motors.append(m)

  @property
  def motor1_state(self):
    return motor.get_motor_state(self.chip, 0, self)

  @property
  def motor2_state(self):
    return motor.get_motor_state(self.chip, 1, self)

  @property
  def motor3_state(self):
    return motor.get_motor_state(self.chip, 2, self)

  @property
  def modbus_id(self):
    return self._mbl[ma.M7_MODBUS_ID]

  @modbus_id.setter
  def modbus_id(self, v):
    self._mbl[ma.M7_MODBUS_ID] = v

  @property
  def setting_hh(self):
    return self._mbl[ma.M9_AUTO_HH]

  @setting_hh.setter
  def setting_hh(self, level):
    self._mbl[ma.M9_AUTO_HH] = level

  @property
  def setting_ll(self):
    return self._mbl[ma.M10_AUTO_LL]

  @setting_ll.setter
  def setting_ll(self, level):
    self._mbl[ma.M10_AUTO_LL] = level

  @property
  def setting_high(self):
    return self._mbl[ma.M11_AUTO_H] / 10.

  @setting_high.setter
  def setting_high(self, level):
    self._mbl[ma.M11_AUTO_H] = level

  @property
  def setting_low(self):
    return self._mbl[ma.M12_AUTO_L] / 10.

  @setting_low.setter
  def setting_low(self, level):
    self._mbl[ma.M12_AUTO_L] = level

  @property
  def pump_state_plc(self):
    return self._mbl[ma.M13_PUMP_STATE_PLC]

  @property
  def pump1_config(self):
    return self._mbl[ma.M14_PUMP1_CONFIG]

  @pump1_config.setter
  def pump1_config(self, s):
    self._mbl[ma.M14_PUMP1_CONFIG] = s
    if self.pump1_mode == constant.PUMP_MODE_MANUAL:
      motor.set_motor_state(self.chip, 0, s)

  @property
  def pump2_config(self):
    return self._mbl[ma.M15_PUMP2_CONFIG]

  @pump2_config.setter
  def pump2_config(self, s):
    self._mbl[ma.M15_PUMP2_CONFIG] = s
    if self.pump2_mode == constant.PUMP_MODE_MANUAL:
      motor.set_motor_state(self.chip, 1, s)

  @property
  def pump3_config(self):
    return self._mbl[ma.M16_PUMP3_CONFIG]

  def set_pump_config(self, pump, value):
    '''
    direct access to pv._mbl
    pump : 0,1,2
    value: 0,1
    '''
    self._mbl[ma.M14_PUMP1_CONFIG+pump] = value

  @pump3_config.setter
  def pump3_config(self, s):
    self._mbl[ma.M16_PUMP3_CONFIG] = s
    if self.pump3_mode == constant.PUMP_MODE_MANUAL:
      motor.set_motor_state(self.chip, 2, s)

  def _pump_change_mode(self, pump, mode):
    '''
    pump의 manual/auto mode를 변경 (40018, 40019, 40020)
    pump=0,1,2
    mode=0,1
    '''
    self._mbl[ma.M18_PUMP_MODE_1+pump] = mode
    _pump_state = motor.get_motor_state(self.chip, pump, self)

    if mode == constant.PUMP_MODE_MANUAL:
      _pump_config = self.pump1_config
      if pump==1:
        _pump_config = self.pump2_config
      elif pump==2:
        _pump_config = self.pump3_config

      if _pump_config and not _pump_state:
        motor.set_motor_state(self.chip, pump, 1)
      elif not _pump_config and _pump_state:
        motor.set_motor_state(self.chip, pump, 0)

      if pump in self.busy_motors:
        del self.busy_motors[self.busy_motors.index(pump)]
      if pump in self.idle_motors:
        del self.idle_motors[self.idle_motors.index(pump)]
    else:
      self.change_motor_list(m=pump, v=_pump_state)

  @property
  def pump1_mode(self):
    return self._mbl[ma.M18_PUMP_MODE_1]

  @pump1_mode.setter
  def pump1_mode(self, n):
    self._pump_change_mode(pump=0, mode=n)

  @property
  def pump2_mode(self):
    return self._mbl[ma.M19_PUMP_MODE_2]

  @pump2_mode.setter
  def pump2_mode(self, n):
    self._pump_change_mode(pump=1, mode=n)

  @property
  def pump3_mode(self):
    return self._mbl[ma.M20_PUMP_MODE_3]

  @pump3_mode.setter
  def pump3_mode(self, n):
    self._pump_change_mode(pump=2, mode=n)

  @property
  def mqtt_on(self):
    return self._mbl[ma.M25_MQTT_ON]

  @mqtt_on.setter
  def mqtt_on(self, n):
    self._mbl[ma.M25_MQTT_ON] = n

  @property
  def mqtt_topic(self):
    return self._mbl[ma.M26_MQTT_TOPIC]

  @mqtt_topic.setter
  def mqtt_topic(self, n):
    self._mbl[ma.M26_MQTT_TOPIC] = n

  @property
  def mqtt_timeout(self):
    return self._mbl[ma.M27_MQTT_TIMEOUT]

  @mqtt_timeout.setter
  def mqtt_timeout(self, n):
    self._mbl[ma.M27_MQTT_TIMEOUT] = n

  @property
  def mqtt_port(self):
    return self._mbl[ma.M28_MQTT_PORT]

  @mqtt_port.setter
  def mqtt_port(self, n):
    self._mbl[ma.M28_MQTT_PORT] = n

  @property
  def mqtt_broker(self):
    return self._mqtt_broker

  @mqtt_broker.setter
  def mqtt_broker(self, broker):
    self._mqtt_broker = broker

  @property
  def device_role(self):
    return self._mbl[ma.M33_DEVICE_ROLE]

  @device_role.setter
  def device_role(self, role):
    self._mbl[ma.M33_DEVICE_ROLE] = role
    #config.update_config(section='MANAGE', key='DEVICE_ROLE', value=role)

  def get_modbus_sequence(self, address, count):
    if address < 0:
      address = 0
    if address >= ma.M_END:
      address = ma.M_END - 1

    if (address + count) > ma.M_END:
      count = 0
    if (address + count) <= 0:
      count = 0

    for i in range(count):
      if address + i == ma.M4_PUMP1_STATE:
        self._mbl[address + i] = self.motor1_state
      elif address + i == ma.M5_PUMP2_STATE:
        self._mbl[address + i] = self.motor2_state
      elif address + i == ma.M6_PUMP3_STATE:
        self._mbl[address + i] = self.motor3_state

    return self._mbl[address:address + count].copy()

  def set_modbus_sequence(self, address, values):
    if address < 0:
      address = 0
    if address >= ma.M_END:
      address = ma.M_END - 1

    count = len(values)
    if (address + count) > ma.M_END:
      count = 0
    if (address + count) <= 0:
      count = 0

    #logger.info(f"@ address:{address} values:{str(values)} pump1_mode:{self.pump1_mode}")
    for i in range(count):
      if address + i == ma.M11_AUTO_H:
        self._mbl[address + i] = values[i]
        config.update_config(section='CONTROLLER',
                             key='AUTO_H',
                             value=values[i])
      elif address + i == ma.M12_AUTO_L:
        self._mbl[address + i] = values[i]
        config.update_config(section='CONTROLLER',
                             key='AUTO_L',
                             value=values[i])
      elif address + i == ma.M13_PUMP_STATE_PLC:
        self._mbl[address + i] = values[i]
      elif address + i == ma.M14_PUMP1_CONFIG:
        self.pump1_config = values[i]
        config.update_config(section='MOTOR',
                             key='PUMP1_CONFIG',
                             value=values[i])
      elif address + i == ma.M15_PUMP2_CONFIG:
        self.pump2_config = values[i]
        config.update_config(section='MOTOR',
                             key='PUMP2_CONFIG',
                             value=values[i])
      elif address + i == ma.M16_PUMP3_CONFIG:
        self.pump3_config = values[i]
        config.update_config(section='MOTOR',
                             key='PUMP3_CONFIG',
                             value=values[i])
      elif address + i == ma.M18_PUMP_MODE_1:
        self.pump1_mode = values[i]
        config.update_config(section='MOTOR', key='PUMP1_MODE', value=values[i])
      elif address + i == ma.M19_PUMP_MODE_2:
        self.pump2_mode = values[i]
        config.update_config(section='MOTOR', key='PUMP2_MODE', value=values[i])
      elif address + i == ma.M20_PUMP_MODE_3:
        self.pump3_mode = values[i]
        config.update_config(section='MOTOR', key='PUMP3_MODE', value=values[i])
      elif address + i == ma.M33_DEVICE_ROLE:
        self.device_role = values[i]
        config.update_config(section='MANAGE',
                             key='DEVICE_ROLE',
                             value=values[i])
      else:
        self._mbl[address + i] = values[i]


#  def update(self):
#    self.source = SOURCE_SENSOR  # 수위값 출처
#    self.water_level = 0  # 현재 수위
#    self.motor1 = 0  # 펌프1
#    self.motor2 = 0  # 펌프2
#    self.motor3 = 0  # 펌프3

  def put_water_level(self, level):
    """수위 값을 q_level에 넣는다.
    q_level에는 항상 평균을 내기 위해 필요한 수의 데이터를 유지한다
    """
    self.lock.acquire()
    self.q_level.get(block=False)
    self.q_level.put(level, block=False)
    self.lock.release()

  def filter_data(self, level):
    logger.debug(
        f"# filtering: level:{level:.1f} q_level:{self.q_level.queue:.1f}".
        format(level))

    self.lock.acquire()

    #입력값과 queue의 첫번째 값 차이가 setting_adc_spike 이상이면 queue의 값을 모두 비우고 입력값으로 채움
    #(1) 처음 ADC에서 정상적인 수위가 들어올 때, 임시로 채워둔 값을 비우고 정상 수위값으로 채움
    #(2) 갑자기 adc의 튀는 값 수준이 아닌 큰 폭의 입력 변화가 있을 때는 queue를 새 값으로 채움
    #    이 경우는 갑자기 수위 입력이 중단되었을 때에 대한 대응임
    first_q_value = self.q_level.queue[len(self.q_level.queue) - 1]
    if abs(first_q_value - level) > self.setting_adc_ignore_spike:
      self.q_level.queue.clear()
      for _ in range(self.adc_avg_count):
        self.q_level.put(level, block=False)
    else:
      self.q_level.get(block=False)
      self.q_level.put(level, block=False)

    #일상적인 adc 튀는 값을 상쇄하기 위하여 평균 값 계산
    avg = sum(self.q_level.queue) // self.adc_avg_count

    self.lock.release()

    logger.debug(f"# filtering: return average from Q: {avg:.1f}")
    return avg

  def return_last_or_v(self, v=0):
    if self.data:
      _last_value = self.data[-1][1]
      logger.info(f"Returning previous level self.data[-1][1]:{_last_value}")
      return _last_value
    else:
      logger.info(f"No available data. Returning v:{v}")
      return v

  def append_data(self, ld):
    self.lock.acquire()
    self.data.append(ld)
    if len(self.train) >= self.setting_max_train:
      n = self.setting_max_train // 3
      self.train = self.train[n:]  # 오래된 순으로 1/3 버림
    self.train.append(ld)
    self.lock.release()

  def get_future_level(self, stime):
    self.lock.acquire()
    if self.future_level:
      for _, l in enumerate(self.future_level):
        if l[0] == stime:
          self.lock.release()
          if not util.repr_int(l[1]):
            l[1] = self.return_last_or_v()
          return l[1]
    logger.info(f"No entry:  get_future_level({stime})")
    self.lock.release()
    return -1

  def find_data(self, stime):
    self.lock.acquire()
    idx = -1
    for i, l in enumerate(self.data):
      if l[0] == stime:
        idx = i
        break
    self.lock.release()
    return idx

  def dump_data(self):
    self.lock.acquire()
    new_list = self.data.copy()
    self.data = []
    self.lock.release()
    return new_list
