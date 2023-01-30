import sys
import time
import datetime
from pprint import pp

import pandas as pd
import logging
import darts
from darts import TimeSeries
from darts.models import NaiveSeasonal


def mk():
  # read a dataframe from a csv file
  df = pd.read_csv('/home/hwan/pump/data/2023-01-28-15-01-07.csv',
                   names=['time', 'level', 'm0', 'm1', 'm2', 'source'])
  df = df.drop(df.columns[[2, 3, 4, 5]], axis=1)
  df['time'] = pd.to_datetime(df['time'])
  df = df.resample('1S', on='time').mean()
  df = df.interpolate(method='linear', limit_direction='forward')

  st = TimeSeries.from_dataframe(
      df=df,
      #time_col='time',
      value_cols=['level'],
      fill_missing_dates=True,
      freq='1S')
  pp(st)
  return df, st

  #st.resample('1S')
  #model.fit(st)
  #len_data = len(data)
  #if len_data > 3600 * 3:
  #  len_data = 3600 * 3
  #logger.info(f"Start training for future {len_data*2} samples")
  #forecast = model.predict(len_data*2)
  #forecast = darts.utils.missing_values.fill_missing_values(forecast, fill='auto')#, **interpolate_kwargs)
  #forecast = forecast.shift(30)
  #logger.info(f"Predicted:{len(forecast)} samples")
  #df = forecast.pd_dataframe()
  #ll=[[i,v[0]] for i, v in zip(df.index.strftime("%Y-%m-%d %H:%M:%S"), df.values)]
