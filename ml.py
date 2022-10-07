import pandas as pd
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json

from pump_variables import PV

def get_future_level(t):
    return 70
    #if pv.forcast:
    #    return pv.forcast.loc[forcast['ds']==t.strftime("%Y-%m-%d %H:%M:%S")]['yhat-s']
    
def train(pv:PV):
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
