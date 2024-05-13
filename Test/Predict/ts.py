import sys
from itertools import product
from pprint import pp

import pandas as pd
import numpy as np

# create a data fram with a date time column and two value columns
# the date time column is in hourly intervals and the values are all 0
df = pd.DataFrame({'date': pd.date_range('2018-01-01', '2018-01-02', freq='H'), 'mp': 0, 'mn': 0})

m = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
w = [1, 2, 3, 4]
h = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]

df2 = pd.DataFrame(
  product(m, w, h, [0.0], [0.0]), 
  columns=['m', 'w', 'h', 'mp', 'mn'],)

def w4(d):
  _w = ((d-1)//7) + 1
  if _w>4:
    _w = 4
  return _w

def mean_n1(m_old, m_size, v_new):
  ''' calculate new average by including a new value
  m_old = old average
  m_size = number of values in old average
  v_new = new value
  '''
  return m_old + (v_new-m_old)/(m_size+1)
