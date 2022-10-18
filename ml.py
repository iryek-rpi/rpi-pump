import sys
import time
import datetime
import multiprocessing as mp
from multiprocessing.synchronize import Event
import threading
from pprint import pp

import pandas as pd
import picologging as logging
import darts
from darts import TimeSeries
from darts.models import NaiveSeasonal

import pump_util as util

#from prophet import Prophet
#from prophet.serialize import model_to_json, model_from_json

#from pump_variables import PV

#def get_future_level(t):
#    return 70
    #if pv.forcast:
    #    return pv.forcast.loc[forcast['ds']==t.strftime("%Y-%m-%d %H:%M:%S")]['yhat-s']
    
model = None

def train_proc(**kwargs):
  global model 

  logger = util.make_logger(name=util.TRAIN_LOGGER_NAME, filename=util.TRAIN_LOGFILE_NAME)
  if not model:
    model = NaiveSeasonal(K=12)

  ns = kwargs['ns']
  ev_req: Event = kwargs['ev_req']
  ev_ret: Event = kwargs['ev_ret']

  while ev_req.wait():
    ev_req.clear()
    logger.info("\n### Event set in train process")
    data = ns.value
    df = pd.DataFrame(data, columns=['time','level','m0','m1','m2','source'])
    df['time'] = pd.to_datetime(df['time'])

    logger.info(f"### Training data received: df[time].dtype:{df['time'].dtype}")
    #logger.info(df)

    st = TimeSeries.from_dataframe(df=df, time_col='time', value_cols=['level'], fill_missing_dates=True, freq='1S')
    logger.info("model.fit()")
    model.fit(st)
    len_data = len(data)
    if len_data > 3600 * 3:
      len_data = 3600 * 3
    logger.info(f"Start training for future {len_data*2} samples")
    forcast = model.predict(len_data*2)
    logger.info(f"Predicted:{len(forcast)} samples")
    df = forcast.pd_dataframe()
    ll=[[i,v[0]] for i, v in zip(df.index.strftime("%Y-%m-%d %H:%M:%S"), df.values)]
    ns.value = ll

    print("Train finished: set event")
    ev_ret.set()


trash = '''
def train(pv):
    tdf = pd.DataFrame(pv.train, columns=['ds','y','a','b','c','d'])
    tdf['ds'] = pd.DatetimeIndex(tdf['ds'])
    tdf = tdf.set_index('ds')
    tdf.drop(columns=['a','b','c','d'],inplace=True)
    tdf = tdf.reset_index()
    tdf = tdf.resample(rule='10min', on='ds').mean()
    tdf = tdf.reset_index()
    tdf.ds.freq = '10min'

    model = Prophet(interval_width=0.95, daily_seasonality=True) # set the uncertainty interval to 95% (the Prophet default is 80%)
    model.fit(tdf)

    # (6 times an hour * 24 hours)
    future_dates = model.make_future_dataframe(periods=6*24, freq='10min') 

    future = future_dates.loc[future_dates['ds']>tdf[-1]]
    
    forcast = model.predict(future)
    #forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    forcast['yhat-s']=forcast['yhat']
    forcast['yhat-s']=((forcast['yhat-s']-forcast['yhat'].mean())*5)+forcast['yhat'].mean()

    forcast = forcast[['ds','yhat-s']].copy()
    forcast = forcast.resample(rule='1sec', on='ds').mean()
    pv.forcast = forcast

def save_model(model_name:str, model):
    with open(f'./model/{model_name}', 'w') as fout:
        fout.write(model_to_json(model))  # Save model

def read_model(model_name:str):
    m = None
    with open(f'./model/{model_name}', 'r') as fin:
        m = model_from_json(fin.read())  # Load model

    return m
'''