import sys
import time
import datetime
import multiprocessing as mp
from multiprocessing import Event
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
  ev:Event = kwargs['ev']

  for ev.wait():
    data = ns.value
    df = pd.DataFrame(data)
    print("### Training data received")
    pp(df)
    
  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
  (m0, m1, m2) = 1, 2, 3

