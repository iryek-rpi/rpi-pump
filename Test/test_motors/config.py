import pump_variables
from pump_variables import PV

import configparser
import pathlib

SETTING_DIR = "./setting/"
SETTING_NAME = SETTING_DIR + "setting.ini"


def init_setting(pv: PV):
  co = configparser.ConfigParser()

  if not pathlib.Path(SETTING_NAME).is_file():
    pathlib.Path(SETTING_DIR).mkdir(parents=True, exist_ok=True)
    co['CONTROLLER'] = {
        'MODBUS_ID': '1',
        'SOLO_MODE': 'MODE_PLC',
        'MOTOR_COUNT': '2',
        'AUTO_H': '800',
        'AUTO_HH': '900',
        'AUTO_L': '200',
        'AUTO_LL': '100',
        'LAST_PUMP': '0'
    }
    co['SENSOR'] = {
        '4MA_REF': '700',
        '20MA_REF': '4000',
        'ADC_INVALID': '100',
    }
    co['MONITOR'] = {
        'MONITOR_INTERVAL': '5',
        'SAVE_INTERVAL': '3600',
        'TOLERANCE_TO_AI': '60',
        'TOLERANCE_TO_SENSOR': '60',
        'ADC_IGNORE_SPIKE': '100'
    }
    co['MANAGE'] = {'USER_ID': 'hwan', 'PASSWORD': 'rudakwkd'}

    with open(SETTING_NAME, 'w') as f:
      co.write(f)
      config_to_pv(co, pv)
  else:
    co.read(SETTING_NAME)
    config_to_pv(co, pv)


def update_config(section, key, value, config_name=SETTING_NAME):
  co = configparser.ConfigParser()
  co.read(config_name)
  co[section][key] = str(value)

  with open(SETTING_NAME, 'w') as f:
    co.write(f)


def config_to_pv(co: configparser.ConfigParser, pv: PV):
  if co['CONTROLLER']['MODBUS_ID'].isdigit():
    pv.modbus_id = int(co['CONTROLLER']['MODBUS_ID'])
  else:
    pv.modbus_id = 1

  if co['CONTROLLER']['SOLO_MODE'] == 'MODE_SOLO':
    pv.solo_mode = pump_variables.MODE_SOLO
  else:
    pv.solo_mode = pump_variables.MODE_PLC

  if co['CONTROLLER']['AUTO_H'].isdigit():
    pv.setting_high = int(co['CONTROLLER']['AUTO_H'])
  else:
    pv.setting_high = 800

  if co['CONTROLLER']['AUTO_HH'].isdigit():
    pv.setting_hh = int(co['CONTROLLER']['AUTO_HH'])
  else:
    pv.setting_hh = 900

  if co['CONTROLLER']['AUTO_L'].isdigit():
    pv.setting_high = int(co['CONTROLLER']['AUTO_L'])
  else:
    pv.setting_low = 200

  if co['CONTROLLER']['AUTO_LL'].isdigit():
    pv.setting_ll = int(co['CONTROLLER']['AUTO_LL'])
  else:
    pv.setting_ll = 100

  if co['CONTROLLER']['LAST_PUMP'].isdigit():
    pv.last_pump = int(co['CONTROLLER']['LAST_PUMP'])

  if co['SENSOR']['4MA_REF'].isdigit():
    pv.setting_4ma_ref = int(co['SENSOR']['4MA_REF'])
  else:
    pv.setting_4ma_ref = 700

  if co['SENSOR']['20MA_REF'].isdigit():
    pv.setting_20ma_ref = int(co['SENSOR']['20MA_REF'])
  else:
    pv.setting_20ma_ref = 4000

  if co['SENSOR']['ADC_INVALID'].isdigit():
    pv.setting_adc_invalid = int(co['SENSOR']['ADC_INVALID'])
  else:
    pv.setting_adc_invalid = 100

  if co['MONITOR']['MONITOR_INTERVAL'].isdigit():
    pv.setting_monitor_interval = int(co['MONITOR']['MONITOR_INTERVAL'])
  else:
    pv.setting_monitor_interval = 5

  if co['MONITOR']['SAVE_INTERVAL'].isdigit():
    pv.setting_save_interval = int(co['MONITOR']['SAVE_INTERVAL'])
  else:
    pv.setting_save_interval = 3600

  if co['MONITOR']['TOLERANCE_TO_AI'].isdigit():
    pv.setting_tolerance_to_ai = int(co['MONITOR']['TOLERANCE_TO_AI'])
  else:
    pv.setting_tolerance_to_ai = 60

  if co['MONITOR']['TOLERANCE_TO_SENSOR'].isdigit():
    pv.setting_tolerance_to_sensor = int(co['MONITOR']['TOLERANCE_TO_SENSOR'])
  else:
    pv.setting_tolerance_to_sensor = 60

  if co['MONITOR']['ADC_IGNORE_SPIKE'].isdigit():
    pv.setting_adc_ignore_spike = int(co['MONITOR']['ADC_IGNORE_SPIKE'])
  else:
    pv.setting_adc_ignore_spike = 100

  pv.user_id = co['MANAGE']['USER_ID']
  pv.password = co['MANAGE']['PASSWORD']