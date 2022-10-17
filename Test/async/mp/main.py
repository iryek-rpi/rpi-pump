import sys
import time
import datetime
import multiprocessing as mp
import threading
from random import random as r
from pprint import pp

import numpy as np
import pandas as pd

import threads
import train

low = 25
high = 65
use = -5
pump1 = 0
pump2 = 0
gcount = 0
req_sent = 0


def gen_level(pv, s1, s2):
  global gcount

  gcount += gcount + 1

  if s1 > gcount or s2 < gcount:
    ru = r() * 2.
    pv.water_level += (use - ru + pump1 + pump2)
  else:
    pv.water_level = 0


def pump_ctl(pv):
  global pump1
  global pump2
  global low
  global use
  global high

  if pv.water_level > high:
    pump1 = 0
    pump2 = 0
  elif pv.water_level < low:
    pump1 = abs(use) * 2
    pump2 = abs(use) * 2


class PV():

  def __init__(self):
    self.data = []
    self.train = []
    self.flevel = [] #future level
    self.lock = threading.Lock()
    self.water_level = 50.
    self.forcast = None
    self._setting_max_train = 518400  # 3600*24*30 (1초 샘플링일 경우 30일)

  @property
  def setting_max_train(self):
    return self._setting_max_train

  def append_data(self, ld):
    self.lock.acquire()
    self.data.append(ld)
    if len(self.train) >= self.setting_max_train:
      n = self.setting_max_train // 3
      self.train = self.train[n:]  # 오래된 순으로 1/3 버림
    self.train.append(ld)
    self.lock.release()

  def find_data(self, stime):
    self.lock.acquire()
    for i, l in enumerate(self.data):
      if l[0] == stime:
        break
    self.lock.release()
    return i

  def dump_data(self):
    self.lock.acquire()
    new_list = self.data.copy()
    self.data = []
    self.lock.release()
    return new_list


def monitor_func(**kwargs):
  global pump1, pump2, gcount

  pv: PV = kwargs['pv']
  ns = kwargs['ns']
  ev = kwargs['ev']
  s1 = kwargs['stop1']
  s2 = kwargs['stop2']

  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%H:%M:%S") #("%Y-%m-%d %H:%M:%S")

  pump_ctl(pv)
  gen_level(pv, s1, s2, gcount)

  if not pv.water_level:
    fl = pv.get_future(time_str):

    if not fl:
      print("No water level")
      if not req_sent:
        ns.value = pv.data
        ev.set()
        req_sent = 1
        print("Request Training")
      elif ev.is_set():
        pv.flevel = ns.value
        fl = pv.get_future(time_str)
        print("Got Result")
        pp(fl)
      else:
        print("Training not finished")
    else:
      print(f"Got future leve:{fl}")
    
    pv.water_level = fl

  (m0, m1) = pump1, pump2

  pv.append_data([time_str, pv.water_level, m0, m1])

  pp(f"\n---monitor")
  pp(pv.data)


def main(stop1, stop2):
  pv = PV()

  mgr = mp.Manager()
  ns = mgr.Namespace()
  ev = mp.Event()

  monitor = threads.RepeatThread(interval=3,
                                 execute=monitor_func,
                                 kwargs={
                                     "pv": pv,
                                     "ns": ns,
                                     "ev": ev,
                                     "stop1": stop1,
                                     "stop2": stop2
                                 })
  monitor.start()

  p_req = pv
  train_proc = mp.Process(name="Train Proc",
                          target=train.train_proc,
                          kwargs={
                              'pv': pv,
                              "ns": ns,
                              "ev": ev,
                              'pipe_request': p_req
                          })
  train_proc.start()

  print(f"@@@@@@@ train_proc: {train_proc.pid}")


if __name__ == '__main__':
  stop1 = 0
  stop2 = 0
  if len(sys.argv) > 2:
    stop1 = int(sys.argv[1])
    stop2 = int(sys.argv[2])

  pp(sys.argv)
  main(stop1=stop1, stop2=stop2)


def producer(ns, event):
  global df
  ns.value = df
  event.set()
  time.sleep(2)
  print("producer waiting")
  event.wait()
  print("producer got the event")
  dff = ns.value
  print(dff)


def consumer(ns, event):
  try:
    print('Before event: {}'.format(ns.value))
  except Exception as err:
    print('Before event, error:', str(err))
  event.wait()
  print('After event:', ns.value)
  dff = ns.value
  dff[0][0] = 123
  ns.value = dff
  print("consumer set event")
  event.set()


temp = '''  
  p_respond, p_req = mp.Pipe()
  responder = threads.RespondThread(execute=train.train_func,
                    kwargs={
                        'pipe': p_respond,
                        'pv': pv
                    })
  responder.start()
'''
