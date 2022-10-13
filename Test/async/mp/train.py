import sys
import time
import datetime
import multiprocessing as mp
import threading

import threads


def train_func(**kwargs):
  pv = kwargs['pv']

  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
  (m0, m1, m2) = 1, 2, 3

  pv.append_data([time_str, pv.water_level, m0, m1, m2])


def train_proc(**kwargs):
  pv = kwargs['pv']

  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
  (m0, m1, m2) = 1, 2, 3

  pv.append_data([time_str, pv.water_level, m0, m1, m2])
