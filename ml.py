import os
from multiprocessing.synchronize import Event
from pprint import pp

import pandas as pd
import csv
#import picologging as logging
import logging
import darts
from darts import TimeSeries
from darts.models import NaiveSeasonal

import constant
import pump_util as util

#from prophet import Prophet
#from prophet.serialize import model_to_json, model_from_json

#from pump_variables import PV

#def get_future_level(t):
#    return 70
    #if pv.forecast:
    #    return pv.forecast.loc[forecast['ds']==t.strftime("%Y-%m-%d %H:%M:%S")]['yhat-s']
    
model = None

def train_proc(**kwargs):
  global model 

  logger = util.make_logger(name=util.TRAIN_LOGGER_NAME, filename=util.TRAIN_LOGFILE_NAME, level=logging.INFO)
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
    df = df.drop(df.columns[[2, 3, 4, 5]], axis=1)
    df['time'] = pd.to_datetime(df['time'])
    df = df.resample('1S', on='time').mean()
    # limit_direction을 forward로 지정해야만 interpolate()가 제대로 동작한다.
    df = df.interpolate(method='linear', limit_direction='forward')
    #logger.info(df)

    ts = util.get_time_str()
    fname = os.path.join('./logs/', ts + '_data.csv')
    try:
      df.to_csv(fname)
    except:
      logger.info("Error save water level data")

    st = TimeSeries.from_dataframe(df=df, 
      #time_col='time', 
      value_cols=['level'], 
      fill_missing_dates=True, 
      freq='1S')
    #logger.info("TimeSeries of Training data ================")
    #logger.info(st)

    fname = os.path.join('./logs/', ts + '_timeseries.csv')
    try:
      st.pd_dataframe().to_csv(fname)
    except:
      logger.info("Error save Time Series data")

    logger.info("model.fit()")
    model.fit(st)
    len_data = len(data)
    if len_data > constant.MAX_PREDICT_SAMPLES // 2: 
      len_data = constant.MAX_PREDICT_SAMPLES 
    else:
      len_data = len_data * 2
    logger.info(f"Start training for future {len_data} samples")
    forecast = model.predict(len_data)
    #logger.info("\nBefore shift forecast ==========================")
    #logger.info(forecast)
    #logger.info("\nAfter shift forecast ==========================")
    #logger.info(forecast)

    #logger.info("\nBefore filling forecast ==========================")
    #logger.info(forecast)
    forecast = darts.utils.missing_values.fill_missing_values(forecast, fill='auto')#, **interpolate_kwargs)
    forecast = forecast.shift(30)
    #logger.info("\nAfter filling forecast ==========================")
    #logger.info(forecast)
    logger.info(f"Predicted:{len(forecast)} samples")
    df = forecast.pd_dataframe()
    #logger.info(df)

    fname = os.path.join('./logs/', ts + '_predict.csv')
    try:
      df.to_csv(fname)
    except:
      logger.info("Error save predict data")

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
    
    forecast = model.predict(future)
    #forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    forecast['yhat-s']=forecast['yhat']
    forecast['yhat-s']=((forecast['yhat-s']-forecast['yhat'].mean())*5)+forecast['yhat'].mean()

    forecast = forecast[['ds','yhat-s']].copy()
    forecast = forecast.resample(rule='1sec', on='ds').mean()
    pv.forecast = forecast

def save_model(model_name:str, model):
    with open(f'./model/{model_name}', 'w') as fout:
        fout.write(model_to_json(model))  # Save model

def read_model(model_name:str):
    m = None
    with open(f'./model/{model_name}', 'r') as fin:
        m = model_from_json(fin.read())  # Load model

    return m
'''