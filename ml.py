import pandas as pd
from prophet import Prophet

from prophet.serialize import model_to_json, model_from_json

def save_model(model_name:str, model):
    with open(f'./model/{model_name}', 'w') as fout:
        fout.write(model_to_json(model))  # Save model

def read_model(model_name:str):
    m = None
    with open(f'./model/{model_name}', 'r') as fin:
        m = model_from_json(fin.read())  # Load model

    return m