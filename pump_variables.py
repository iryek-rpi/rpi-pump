import threading
import queue
import datetime
import os
import pandas as pd
import csv

import picologging as logging

import pump_util as util
import modbus_address as ma
import config

logger = logging.getLogger(util.MAIN_LOGGER_NAME)

# 수위계 입력에 의한 수위값인지, 예측에 의한 수위값인지
SOURCE_SENSOR = 0
SOURCE_AI = 1

# 펌프 가동을 자동으로 할 지 여부
OP_MANUAL = 0
OP_AUTO = 1

# PLC와 연동해서 동작할 지, 단독으로 동작할 지
MODE_PLC = 0  # PLC에서 pump control
MODE_SOLO = 1  # 수위조절기에서 pump control


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
    self.model = None

    self._mbl = [0 for _ in range(ma.M_END)]

    #self.water_level = 0  # 현재 수위
    #self.source = SOURCE_SENSOR  # PLC/AI 운전모드
    
    #self.motor1 = 0  # motor 1,2,3의 마지막 구동 상태
    #self.motor2 = 0
    #self.motor3 = 0

    self.modbus_id = 0

    #self.setting_high = 80  # 고수위(%)
    #self.setting_hh = 80  # 고수위(%)
    #self.setting_low = 20  # 저수위(%)
    #self.setting_ll = 20  # 저수위(%)

    self.solo_mode = MODE_PLC
    self.op_mode = OP_AUTO  # MANUAL/AUTO 운전모드


    self.temperature = 0
    # 현재 모터 상태는 항상 MOTOR_INPUT 단자에서 읽어옴
    #self.motor_count = 1
    self.motors = [0,0,0] # 연결된 모터는 1, 연결 안된 모터는 0 
    self.motor_valid = [0]  # 사용할 수 있는 모터 번호 리스트(0~2)
    self.motor_lead_time = 10

    self.no_input_starttime = None  # 입력이 안들어오기 시각한 시간
    self.data = []
    self.train = []
    self.forcast = None
    self.lock = threading.Lock()

    self.setting_max_train = 518400 # 3600*24*30 (30일)
    self.setting_4ma_ref = 700  # 4mA ADC 출력
    self.setting_20ma_ref = 4000  # 4000  # 20mA ADC 출력
    self.setting_4ma = 0.0  # 4mA 수위(수위계 캘리브레이션)
    self.setting_20ma = 100.0  # 20mA 수위(수위계 캘리브레이션)
    self.setting_adc_invalid = 100  # ADC 값이 이 값 이하이면 입력이 없는 것으로 간주함

    # 수위 기록 인터벌 1, 10, 30, 60(1min), 180(3min), 300(5min), 600(10min), 3600(1hr)
    self.setting_monitor_interval = 5  # 수위 모니터링 주기(초)
    self.setting_save_interval = 60 * 60 * 24  # 저장 주기(초)
    self.setting_tolerance_to_ai = 60  #600  # AI 모드로 전환하기 위한 입력 없는 time(sec)
    self.setting_tolerance_to_sensor = 60  #600  # 수위계 입력 모드로 전환하기 위한 입력 유지 time(sec)
    self.setting_input_rate = 0.8  # tolerance 내 입력 비율
    self.setting_adc_ignore_spike = 100  # 이 값 이상의 급격한 입력 변동은 일시적인 것으로 간주하고 무시함

    #
    self.setting_adc_avg_interval = 10  # 평균을 계산할 adc 입력 기간(sec)
    self.adc_avg_count = self.setting_adc_avg_interval // self.setting_monitor_interval
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

  @property
  def water_level(self):
    return self._mbl[ma.M1_LEVEL_SENSOR]

  @water_level.setter
  def water_level(self, level):
    self._mbl[ma.M1_LEVEL_SENSOR] = level 

  @property
  def water_level_ai(self):
    return self._mbl[ma.M2_LEVEL_AI]

  @water_level_ai.setter
  def water_level_ai(self, level):
    self._mbl[ma.M2_LEVEL_AI] = level 

  @property
  def source(self):
    return self._mbl[ma.M3_SOURCE]

  @source.setter
  def source(self, s):
    self._mbl[ma.M3_SOURCE] = s 

  @property
  def motor1(self):
    return self._mbl[ma.M4_PUMP1_STATE]

  @motor1.setter
  def motor1(self, s):
    self._mbl[ma.M4_PUMP1_STATE] = s 

  @property
  def motor2(self):
    return self._mbl[ma.M5_PUMP2_STATE]

  @motor2.setter
  def motor2(self, s):
    self._mbl[ma.M5_PUMP2_STATE] = s 

  @property
  def motor3(self):
    return self._mbl[ma.M6_PUMP3_STATE]

  @motor3.setter
  def motor3(self, s):
    self._mbl[ma.M6_PUMP3_STATE] = s 

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
    return self._mbl[ma.M11_AUTO_H]

  @setting_high.setter
  def setting_high(self, level):
    self._mbl[ma.M11_AUTO_H] = level 

  @property
  def setting_low(self):
    return self._mbl[ma.M12_AUTO_L]

  @setting_low.setter
  def setting_low(self, level):
    self._mbl[ma.M12_AUTO_L] = level 

  #@property
  #def solo_mode(self):
  #  return self._mbl[ma.M13_PUMP_OP_MODE]

  #@solo_mode.setter
  #def solo_mode(self, m):
  #  self._mbl[ma.M13_PUMP_OP_MODE] = m 

  @property
  def op_mode(self):
    return self._mbl[ma.M13_PUMP_OP_MODE]

  @op_mode.setter
  def op_mode(self, m):
    self._mbl[ma.M13_PUMP_OP_MODE] = m 

  @property
  def pump1_on(self):
    return self._mbl[ma.M14_PUMP1_ON]

  @pump1_on.setter
  def pump1_on(self, s):
    self._mbl[ma.M14_PUMP1_ON] = s 

  @property
  def pump2_on(self):
    return self._mbl[ma.M15_PUMP2_ON]

  @pump2_on.setter
  def pump2_on(self, s):
    self._mbl[ma.M15_PUMP2_ON] = s 

  @property
  def pump3_on(self):
    return self._mbl[ma.M16_PUMP3_ON]

  @pump3_on.setter
  def pump3_on(self, s):
    self._mbl[ma.M16_PUMP3_ON] = s 

  @property
  def pump_count(self):
    return self._mbl[ma.M17_PUMP_COUNT]

  @pump_count.setter
  def pump_count(self, n):
    self._mbl[ma.M17_PUMP_COUNT] = n 

  @property
  def mqtt_on(self):
    return self._mbl[ma.M25_MQTT_ON]

  @mqtt_on.setter
  def mqtt_on(self, n):
    self._mbl[ma.M15_PUMP2_ON] = n 


  @property
  def mqtt_topic_ai(self):
    return self._mbl[ma.M26_MQTT_TOPIC_AI]

  @mqtt_topic_ai.setter
  def mqtt_topic_ai(self, n):
    self._mbl[ma.M26_MQTT_TOPIC_AI] = n 


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
    config.update_config(sectin='MANAGE', key='DEVICE_ROLE', value=role)


  def get_modbus_sequence(self, address, count):
    if address < 0:
      address = 0
    if address >= ma.M_END:
      address = ma.M_END -1
    
    if (address+count)>ma.M_END:
      count = 0
    if (address+count)<=0:
      count = 0

    return self._mbl[address:address+count].copy()

  def set_modbus_sequence(self, address, values):
    if address < 0:
      address = 0
    if address >= ma.M_END:
      address = ma.M_END -1
    
    count = len(values)
    if (address+count)>ma.M_END:
      count = 0
    if (address+count)<=0:
      count = 0

    for i in range(count):
      self._mbl[address+i] = values[i]

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
    logger.debug("### filtering: level: {}".format(level))
    logger.debug("### filtering: q_level: {}".format(self.q_level.queue))

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

    logger.debug("### filtering: returning average from Queue: {}".format(avg))
    return avg

  def append_data(self, ld):
    self.lock.acquire()
    self.data.append(ld)
    if len(self.train)>=self.setting_max_train:
      n = self.setting_max_train//3
      self.train = self.train[n:]   # 오래된 순으로 1/3 버림
    self.train.append(ld)
    self.lock.release()

  def dump_data(self):
    self.lock.acquire()
    new_list = self.data.copy()
    self.data = []
    self.lock.release()
    return new_list


def save_data(**kwargs):
  pv = kwargs['pv']
  n = datetime.datetime.now()

  data = pv.dump_data()
  if len(data) > 0:
    fname = os.path.join(pv.data_path, n.strftime("%Y-%m-%d-%H-%M-%S.csv"))
    logger.debug(f"save file name:{fname}")
    try:
      with open(fname, 'w') as f:
        w = csv.writer(f)
        w.writerows(data)
    except:
      logger.debug("Error save data")
