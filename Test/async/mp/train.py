import sys
import time
import datetime
import multiprocessing as mp
from multiprocessing.synchronize import Event
import threading
from pprint import pp

import pandas as pd

import threads


def train_func(**kwargs):
  pv = kwargs['pv']

  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
  (m0, m1, m2) = 1, 2, 3

  pv.append_data([time_str, pv.water_level, m0, m1, m2])

  p_respond, p_req = mp.Pipe()
  responder = threads.RespondThread(execute=train_func,
                                    kwargs={
                                        'pipe': p_respond,
                                        'pv': pv
                                    })
  responder.start()


def train_proc(**kwargs):
  pv = kwargs['pv']
  ns = kwargs['ns']
  ev_req: Event = kwargs['ev_req']
  ev_ret: Event = kwargs['ev_ret']

  while ev_req.wait():
    ev_req.clear()
    print("\n### Event set in train process")
    data = ns.value
    df = pd.DataFrame(data)
    print("### Training data received")
    pp(df)
    print("Start training")
    for i in range(10):
      print(f"training {i}/10")
      time.sleep(1)
    print("Train finished: set event")
    ev_ret.set()
