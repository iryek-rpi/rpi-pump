import threading
import queue
import datetime
import os
import pandas as pd
import csv

import logging

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

    self.modbus_id = 1
    self.source = SOURCE_SENSOR  # PLC/AI 운전모드
    self.solo_mode = MODE_PLC
    self.op_mode = OP_AUTO  # MANUAL/AUTO 운전모드
    self.water_level = 0  # 현재 수위
    self.motor1 = 0  # 펌프1
    self.motor2 = 0  # 펌프2
    self.motor3 = 0  # 펌프3
    self.motor_count = 1
    self.motor_valid = [1]  # 사용할 수 있는 모터 번호 리스트(1~3)
    self.no_input_starttime = None  # 입력이 안들어오기 시각한 시간
    self.data = []
    self.lock = threading.Lock()

    self.setting_4ma_ref = 700  # 4mA ADC 출력
    self.setting_20ma_ref = 4000  # 4000  # 20mA ADC 출력
    self.setting_4ma = 0.0  # 4mA 수위(수위계 캘리브레이션)
    self.setting_20ma = 100.0  # 20mA 수위(수위계 캘리브레이션)
    self.setting_high = 80  # 고수위(%)
    self.setting_hh = 80  # 고수위(%)
    self.setting_low = 20  # 저수위(%)
    self.setting_ll = 20  # 저수위(%)
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

  def update(self):
    self.source = SOURCE_SENSOR  # 수위값 출처
    self.water_level = 0  # 현재 수위
    self.motor1 = 0  # 펌프1
    self.motor2 = 0  # 펌프2
    self.motor3 = 0  # 펌프3

  def put_water_level(self, level):
    """수위 값을 q_level에 넣는다.
    q_level에는 항상 평균을 내기 위해 필요한 수의 데이터를 유지한다
    """
    self.lock.acquire()
    self.q_level.get(block=False)
    self.q_level.put(level, block=False)
    self.lock.release()

  def filter_data(self, level):
    logging.debug("level: {}".format(level))
    logging.debug("q_level: {}".format(self.q_level.queue))

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
    return avg

  def append_data(self, ld):
    self.lock.acquire()
    self.data.append(ld)
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
    logging.debug(f"save file name:{fname}")
    try:
      with open(fname, 'w') as f:
        w = csv.writer(f)
        w.writerows(data)
    except:
      logging.debug("Error save data")
