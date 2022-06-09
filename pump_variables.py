from threading import Lock
from queue import Queue
import datetime
import os
import pandas as pd
import csv

import logging

MODE_PLC = 0
MODE_AI = 1 

def pv(inst=None):
  if inst!=None:
    pv.instance=inst
  return pv.instance
pv.instance = None

# 수위 기록 주기
interval = { 
  "1s":1
  , "10s":10
  , "30s":30
  , "1min":60
  , "3min":180
  , "5min":300
  , "10min":600 
  , "1hr":3600 
}

# AI 전환   
no_input_tol = {
  "5min":300
  , "10min":600 
  , "30min":1800 
  , "1hr":3600 
  , "2hr":7200 
}

class PV():
  def __init__(self):
    self.mode = MODE_PLC      # 운전모드
    self.water_level = 0.0    # 현재 수위
    self.motor1 = 0           # 펌프1
    self.motor2 = 0           # 펌프2
    self.motor3 = 0           # 펌프3
    self.time_no_input = None # 입력이 없는 시간 
    self.last_valid_level = 0
    self.data = []
    self.lock = Lock()


    self.setting_tank_full = 2000 # 수조 최고 수위
    self.setting_4ma_ref = 700    # 4mA ADC 출력
    self.setting_20ma_ref = 2000  # 4000  # 20mA ADC 출력
    self.setting_4ma = 0.0        # 4mA 수위(수위계 캘리브레이션)
    self.setting_20ma = 100.0     # 20mA 수위(수위계 캘리브레이션)
    self.setting_low = 20         # 저수위(%)
    self.setting_high = 80        # 고수위(%)
    self.setting_adc_empty = 100  # ADC 값이 이 값 이하이면 입력이 없는 것으로 간주함

    # 수위 기록 인터벌 1, 10, 30, 60(1min), 180(3min), 300(5min), 600(10min), 3600(1hr) 
    self.setting_interval_monitor = 5       # 수위 모니터링 주기(초)
    self.setting_interval_save = 60*60*24   # 저장 주기(초) 
    self.setting_tolerance_to_ai = 60 #600  # AI 모드로 전환하기 위한 입력 없는 time(sec)
    self.setting_tolerance_to_plc= 60 #600  # PLC 모드로 전환하기 위한 입력 유지 time(sec)  
    self.setting_input_rate = 0.8 # tolerance 내 입력 비율 
    self.setting_adc_drop = 100   # 이 값 이상의 급격한 입력 변동 일시적인 것으로 간주하고 무시함 

    self.setting_adc_avg_sec = 10   # 평균을 계산할 adc 입력 period(sec)
    self.adc_avg_count = self.setting_adc_avg_sec // self.setting_interval_monitor
    if self.adc_avg_count < 1:
      self.adc_avg_count = 1

    self.q_level = Queue(self.adc_avg_count)
    for _ in range(self.adc_avg_count):
      self.q_level.put(self.setting_20ma_ref, block=False)

    self.password = "rudakwkd"
    self.id = "hwan"
    self.data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')

  def update(self):
    self.mode = MODE_PLC  # 운전모드
    self.water_level = 0  # 현재 수위
    self.motor1 = 0     # 펌프1
    self.motor2 = 0     # 펌프2
    self.motor3 = 0     # 펌프3

  def put_water_level(self, level):
    self.lock.acquire()
    self.q_level.get(block=False)
    self.q_level.put(level, block=False)
    self.lock.release()

  def filter_data(self, level):
    self.lock.acquire()
    logging.debug("level: {}".format(level))
    logging.debug("q_level: {}".format(self.q_level.queue))

    if abs(self.q_level.queue[len(self.q_level.queue)-1]-level)>self.setting_adc_drop:
      self.q_level.queue.clear()
      for _ in range(self.adc_avg_count):
        self.q_level.put(level, block=False)
    else:
      self.q_level.get(block=False)
      self.q_level.put(level, block=False)
    avg = sum(self.q_level.queue)//self.adc_avg_count

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

  @property
  def mode(self):
    # update mode
    return self._mode

  @mode.setter
  def mode(self, mode):
    self._mode = mode


def save_data(**kwargs):
  pv=kwargs['pv']
  n = datetime.datetime.now()

  data = pv.dump_data()
  if len(data)>0:
    fname = os.path.join( pv.data_path, n.strftime("%Y-%m-%d-%H-%M-%S.csv"))
    logging.debug(f"save file name:{fname}")
    try: 
      with open(fname, 'w') as f:
        w = csv.writer(f)
        w.writerows(data)
    except:
      logging.debug("Error save data")
    