import sys
import time
import datetime
import multiprocessing as mp
import threading

import threads
import train


class PV():

  def __init__(self):
    self.data = []
    self.lock = threading.Lock()
    self.water_level = 0
    self.train = []
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
  pv: PV = kwargs['pv']

  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
  (m0, m1, m2) = 1, 2, 3

  pv.append_data([time_str, pv.water_level, m0, m1, m2])


def main():
  pv = PV()

  monitor = threads.RepeatThread(interval=3, execute=monitor_func)
  monitor.start()

  p_respond, p_req = mp.Pipe()
  responder = threads.RespondThread(execute=train.train_func,
                                    kwargs={
                                        'pipe': p_respond,
                                        'pv': pv
                                    })
  responder.start()

  train_proc = mp.Process(name="Train Proc",
                          target=train.train_proc,
                          kwargs={
                              'pipe_request': p_req,
                          })
  train_proc.start()
  print(f"@@@@@@@ comm_proc: {train_proc.pid}")


if __name__ == '__main__':
  main()
