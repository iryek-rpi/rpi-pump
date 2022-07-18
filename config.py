import pump_variables
from pump_variables import PV

import configparser
import pathlib
import logging
import ast

SETTING_DIR = "./setting/"
SETTING_NAME = SETTING_DIR + "setting.ini"


def init_setting(pv: PV):
  co = configparser.ConfigParser()

  if not pathlib.Path(SETTING_NAME).is_file():
    logging.info("No setting file exists. Create one with defaults")
    pathlib.Path(SETTING_DIR).mkdir(parents=True, exist_ok=True)
    co['CONTROLLER'] = {
        'MODBUS_ID': 1,
        'SOLO_MODE': 'MODE_PLC',
        'OP_MODE': 'OP_AUTO',
        'AUTO_H': 800,
        'AUTO_HH': 900,
        'AUTO_L': 200,
        'AUTO_LL': 100,
    }
    co['MOTOR'] = {
        'INSTALLED_MOTORS' : '[1,0,0]', # 모터가 연결된 단자에 1, 연결 안된 단자는 0 
        'MOTOR1' : 0,   # MOTOR1,2,3 마지막 가동 상태. 교번 운전에 반영
        'MOTOR2' : 0,
        'MOTOR3' : 0,
        'LEAD_TIME' : 10, # 모터 가동에 걸리는 시간 (교번운전을 위해 가동된 모터를 확인하여 기록하기 위함)
    }
    co['SENSOR'] = {
        '4MA_REF': 700,
        '20MA_REF': 4000,
        'ADC_INVALID': 100,
    }
    co['MONITOR'] = {
        'MONITOR_INTERVAL': 5, #sec
        'SAVE_INTERVAL': 24,   #hour
        'TOLERANCE_TO_AI': 60,
        'TOLERANCE_TO_SENSOR': 60,
        'ADC_IGNORE_SPIKE': 100
    }
    co['MANAGE'] = {'USER_ID': 'hwan', 'PASSWORD': 'rudakwkd'}

    with open(SETTING_NAME, 'w') as f:
      co.write(f)
      config_to_pv(co, pv)
  else:
    logging.info("Reading setting from setting.ini")
    co.read(SETTING_NAME)
    config_to_pv(co, pv)

def save_motors(tm):
  motors = ['MOTOR1','MOTOR2', 'MOTOR3']
  for i, n in enumerate(tm):
    update_config('MOTOR', motors[i], n)

def update_config(section, key, value, config_name=SETTING_NAME):
  co = configparser.ConfigParser()
  co.read(config_name)
  co[section][key] = str(value)

  with open(SETTING_NAME, 'w') as f:
    co.write(f)

def read_config(section, key, config_name=SETTING_NAME):
  co = configparser.ConfigParser()
  co.read(config_name)
  if (section in co) and (key in co[section]):
    return co[section][key]
  else:
    logging.info("No setting[%s][%s]", section, key)
    return None

def str_to_list(s:str):
  return s.strip('[]').split(',')

def config_to_pv(co: configparser.ConfigParser, pv: PV):
  
  if ('CONTROLLER' in co) and ('MODBUS_ID' in co['CONTROLLER']) and co['CONTROLLER']['MODBUS_ID'].isdigit():
    logging.info("modbus id from setting:%s", co['CONTROLLER']['MODBUS_ID'])
    pv.modbus_id = int(co['CONTROLLER']['MODBUS_ID'])
  else:
    logging.info("invalid modbus id from setting. default id=1")
    pv.modbus_id = 1

  if ('CONTROLLER' in co) and ('SOLO_MODE' in co['CONTROLLER']) and co['CONTROLLER']['SOLO_MODE'] == 'MODE_SOLO':
    pv.solo_mode = pump_variables.MODE_SOLO
  else:
    pv.solo_mode = pump_variables.MODE_PLC

  if ('CONTROLLER' in co) and ('OP_MODE' in co['CONTROLLER']) and co['CONTROLLER']['OP_MODE'] == 'OP_AUTO':
    pv.op_mode = pump_variables.OP_AUTO
  else:
    pv.op_mode = pump_variables.OP_MANUAL

  #if ('CONTROLLER' in co) and ('MOTOR_COUNT' in co['CONTROLLER']) and co['CONTROLLER']['MOTOR_COUNT'].isdigit():
  #  pv.motor_count = int(co['CONTROLLER']['MOTOR_COUNT'])
  #else:
  #  pv.motor_count = 2

  if ('CONTROLLER' in co) and ('AUTO_H' in co['CONTROLLER']) and co['CONTROLLER']['AUTO_H'].isdigit():
    pv.setting_high = int(co['CONTROLLER']['AUTO_H'])
  else:
    pv.setting_high = 800

  if ('CONTROLLER' in co) and ('AUTO_HH' in co['CONTROLLER']) and co['CONTROLLER']['AUTO_HH'].isdigit():
    pv.setting_hh = int(co['CONTROLLER']['AUTO_HH'])
  else:
    pv.setting_hh = 900

  if ('CONTROLLER' in co) and ('AUTO_L' in co['CONTROLLER']) and co['CONTROLLER']['AUTO_L'].isdigit():
    pv.setting_high = int(co['CONTROLLER']['AUTO_L'])
  else:
    pv.setting_low = 200

  if ('CONTROLLER' in co) and ('AUTO_LL' in co['CONTROLLER']) and co['CONTROLLER']['AUTO_LL'].isdigit():
    pv.setting_ll = int(co['CONTROLLER']['AUTO_LL'])
  else:
    pv.setting_ll = 100

  if ('CONTROLLER' in co) and ('LAST_PUMP' in co['CONTROLLER']) and co['CONTROLLER']['LAST_PUMP'].isdigit():
    pv.last_pump = int(co['CONTROLLER']['LAST_PUMP'])

  if ('MOTOR' in co) and ('INSTALLED_MOTORS' in co['MOTOR']):
    installed_motors = ast.literal_eval(co['MOTOR']['INSTALLED_MOTORS'])
    j=0
    for i, _ in enumerate(installed_motors):
      if installed_motors[i]:
        pv.motors[j]=i
      j += 1
    logging.info("installed motors: %s", str(installed_motors))
    logging.info("pv.motors: %s", str(pv.motors))


  # MOTOR1,2,3 마지막 가동 상태. 교번 운전에 반영
  if ('MOTOR' in co) and ('MOTOR1' in co['MOTOR']) and co['MOTOR']['MOTOR1'].isdigit():
    pv.motor1 = int(co['MOTOR']['MOTOR1'])
  else:
    pv.motor1 = 0

  if ('MOTOR' in co) and ('MOTOR2' in co['MOTOR']) and co['MOTOR']['MOTOR2'].isdigit():
    pv.motor2 = int(co['MOTOR']['MOTOR2'])
  else:
    pv.motor2 = 0

  if ('MOTOR' in co) and ('MOTOR3' in co['MOTOR']) and co['MOTOR']['MOTOR3'].isdigit():
    pv.motor3 = int(co['MOTOR']['MOTOR3'])
  else:
    pv.motor3 = 0

  if ('MOTOR' in co) and ('LEAD_TIME' in co['MOTOR']) and co['MOTOR']['LEAD_TIME'].isdigit():
    pv.motor_lead_time = int(co['MOTOR']['LEAD_TIME'])
  else:
    pv.motor_lead_time = 10

  if ('SENSOR' in co) and ('4MA_REF' in co['SENSOR']) and co['SENSOR']['4MA_REF'].isdigit():
    pv.setting_4ma_ref = int(co['SENSOR']['4MA_REF'])
  else:
    pv.setting_4ma_ref = 700

  if ('SENSOR' in co) and ('20MA_REF' in co['SENSOR']) and co['SENSOR']['20MA_REF'].isdigit():
    pv.setting_20ma_ref = int(co['SENSOR']['20MA_REF'])
  else:
    pv.setting_20ma_ref = 4000

  if ('SENSOR' in co) and ('ADC_INVALID' in co['SENSOR']) and co['SENSOR']['ADC_INVALID'].isdigit():
    pv.setting_adc_invalid = int(co['SENSOR']['ADC_INVALID'])
  else:
    pv.setting_adc_invalid = 100

  if ('MONITOR' in co) and ('MONITOR_INTERVAL' in co['MONITOR']) and co['MONITOR']['MONITOR_INTERVAL'].isdigit():
    pv.setting_monitor_interval = int(co['MONITOR']['MONITOR_INTERVAL'])
  else:
    pv.setting_monitor_interval = 5

  if ('MONITOR' in co) and ('SAVE_INTERVAL' in co['MONITOR']) and co['MONITOR']['SAVE_INTERVAL'].isdigit():
    pv.setting_save_interval = int(co['MONITOR']['SAVE_INTERVAL'])*3600
  else:
    pv.setting_save_interval = 24*3600

  if ('MONITOR' in co) and ('TOLERANCE_TO_AI' in co['MONITOR']) and co['MONITOR']['TOLERANCE_TO_AI'].isdigit():
    pv.setting_tolerance_to_ai = int(co['MONITOR']['TOLERANCE_TO_AI'])
  else:
    pv.setting_tolerance_to_ai = 60

  if ('MONITOR' in co) and ('TOLERANCE_TO_SENSOR' in co['MONITOR']) and co['MONITOR']['TOLERANCE_TO_SENSOR'].isdigit():
    pv.setting_tolerance_to_sensor = int(co['MONITOR']['TOLERANCE_TO_SENSOR'])
  else:
    pv.setting_tolerance_to_sensor = 60

  if ('MONITOR' in co) and ('ADC_IGNORE_SPIKE' in co['MONITOR']) and co['MONITOR']['ADC_IGNORE_SPIKE'].isdigit():
    pv.setting_adc_ignore_spike = int(co['MONITOR']['ADC_IGNORE_SPIKE'])
  else:
    pv.setting_adc_ignore_spike = 100

  if ('MANAGE' in co) and ('USER_ID' in co['MANAGE']):
    pv.user_id = co['MANAGE']['USER_ID']
    pv.password = co['MANAGE']['PASSWORD']
