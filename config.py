import configparser
import pathlib
import picologging as logging
import ast

import constant
import pump_util as util
import motor

SETTING_DIR = "./setting/"
SETTING_NAME = SETTING_DIR + "setting.ini"

#import pump_util as util
logger = logging.getLogger(util.MAIN_LOGGER_NAME)


# motor port 초기화한 후에 콜해야함
def init_setting(pv):
  co = configparser.ConfigParser()

  if not pathlib.Path(SETTING_NAME).is_file():
    logger.info("No setting file exists. Create one with defaults")
    pathlib.Path(SETTING_DIR).mkdir(parents=True, exist_ok=True)
    co['CONTROLLER'] = {
        'MODBUS_ID': 1,
        'SOLO_MODE': 'MODE_PLC',
        'AUTO_H': 800,
        'AUTO_HH': 900,
        'AUTO_L': 200,
        'AUTO_LL': 100,
    }
    co['MOTOR'] = {
        'PUMP1_CONFIG': 0,
        'PUMP2_CONFIG': 0,
        'PUMP3_CONFIG': 0,
        # MOTOR1,2,3 마지막 가동 모드, 교번 운전에 반영
        'PUMP1_MODE': constant.PUMP_MODE_AUTO,
        'PUMP2_MODE': constant.PUMP_MODE_AUTO,
        'PUMP3_MODE': constant.PUMP_MODE_MANUAL,
        'LEAD_TIME': 10,  # 모터 가동에 걸리는 시간 (교번운전을 위해 가동된 모터를 확인하여 기록하기 위함)
        # 모터 수는  PUMP MODE로 관리함.
        # INSTALLED_MOTORS는 항상 [1,1,1]로 사용
        'INSTALLED_MOTORS': '[1,1,1]',  # 모터가 연결된 단자에 1, 연결 안된 단자는 0 
    }
    co['SENSOR'] = {
        '4MA_REF': 700,
        '20MA_REF': 4000,
        'ADC_INVALID': 100,
    }
    co['MONITOR'] = {
        'MONITOR_INTERVAL': 1,  #sec
        'SAVE_INTERVAL': 24,  #hour
        'TOLERANCE_TO_AI': 3,
        'TOLERANCE_TO_SENSOR': 3,
        'ADC_IGNORE_SPIKE': 100
    }
    co['MANAGE'] = {
        'USER_ID': 'hwan',
        'PASSWORD': 'rudakwkd',
        'DEVICE_ROLE': 'control'
    }
    co['MQTT'] = {
        'MQTT_ON': 1,  # 0
        'TOPIC': 'ai_value',  # sensor_value
        'CLIENT_NAME': 'AI',  # SENSOR
        'TIMEOUT': 10,
        'PORT': 1883,
        'BROKER': 'X230T.local'
    }

    with open(SETTING_NAME, 'w') as f:
      co.write(f)
      config_to_pv(co, pv)
  else:
    logger.info("Reading setting from setting.ini")
    co.read(SETTING_NAME)
    config_to_pv(co, pv)


def save_motors(tm):
  motors = ['MOTOR1', 'MOTOR2', 'MOTOR3']
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
    logger.info("No setting[%s][%s]", section, key)
    return None


def str_to_list(s: str):
  return s.strip('[]').split(',')


def config_to_pv(co: configparser.ConfigParser, pv):

  if ('CONTROLLER' in co) and ('MODBUS_ID' in co['CONTROLLER']
                              ) and co['CONTROLLER']['MODBUS_ID'].isdigit():
    logger.info("modbus id from setting:%s", co['CONTROLLER']['MODBUS_ID'])
    pv.modbus_id = int(co['CONTROLLER']['MODBUS_ID'])
  else:
    logger.info("invalid modbus id from setting. default id=1")
    pv.modbus_id = 1

  if ('CONTROLLER' in co) and (
      'SOLO_MODE'
      in co['CONTROLLER']) and co['CONTROLLER']['SOLO_MODE'] == 'MODE_SOLO':
    pv.solo_mode = constant.MODE_SOLO
  else:
    pv.solo_mode = constant.MODE_PLC

  if ('CONTROLLER'
      in co) and ('AUTO_H'
                  in co['CONTROLLER']) and co['CONTROLLER']['AUTO_H'].isdigit():
    pv.setting_high = int(co['CONTROLLER']['AUTO_H'])
  else:
    pv.setting_high = 800

  if ('CONTROLLER' in co) and (
      'AUTO_HH' in co['CONTROLLER']) and co['CONTROLLER']['AUTO_HH'].isdigit():
    pv.setting_hh = int(co['CONTROLLER']['AUTO_HH'])
  else:
    pv.setting_hh = 900

  if ('CONTROLLER'
      in co) and ('AUTO_L'
                  in co['CONTROLLER']) and co['CONTROLLER']['AUTO_L'].isdigit():
    pv.setting_low = int(co['CONTROLLER']['AUTO_L'])
  else:
    pv.setting_low = 200

  if ('CONTROLLER' in co) and (
      'AUTO_LL' in co['CONTROLLER']) and co['CONTROLLER']['AUTO_LL'].isdigit():
    pv.setting_ll = int(co['CONTROLLER']['AUTO_LL'])
  else:
    pv.setting_ll = 100

  if ('CONTROLLER' in co) and ('LAST_PUMP' in co['CONTROLLER']
                              ) and co['CONTROLLER']['LAST_PUMP'].isdigit():
    pv.last_pump = int(co['CONTROLLER']['LAST_PUMP'])

  # 다른 모터 관련 설정보다 먼저 초기화해야함
  if ('MOTOR' in co) and ('INSTALLED_MOTORS' in co['MOTOR']):
    installed_motors = ast.literal_eval(co['MOTOR']['INSTALLED_MOTORS'])
    for i, m in enumerate(installed_motors):
      if m:
        pv.valid_motors.append(i)
    logger.info("0 installed motors: %s", str(installed_motors))
    logger.info("0 pv.valid_motors: %s", str(pv.valid_motors))

  logger.info(f'0 idle_motors:{pv.idle_motors}')
  logger.info(f'0 busy_motors:{pv.busy_motors}')

  if 0 in pv.valid_motors:
    if ('MOTOR' in co) \
      and ('PUMP1_CONFIG' in co['MOTOR']) \
      and co['MOTOR']['PUMP1_CONFIG'].isdigit():
      pv.set_pump_config(0, int(co['MOTOR']['PUMP1_CONFIG']))
    else:
      pv.set_pump_config(0, 0)

    if ('MOTOR' in co) \
      and ('PUMP1_MODE' in co['MOTOR']) \
      and co['MOTOR']['PUMP1_MODE'].isdigit():
      pv.pump1_mode = int(co['MOTOR']['PUMP1_MODE'])
    else:
      pv.pump1_mode = 1

  if 1 in pv.valid_motors:
    if ('MOTOR' in co) \
      and ('PUMP2_CONFIG' in co['MOTOR']) \
      and co['MOTOR']['PUMP2_CONFIG'].isdigit():
      pv.set_pump_config(1, int(co['MOTOR']['PUMP2_CONFIG']))
    else:
      pv.set_pump_config(1, 0)

    if ('MOTOR' in co) \
      and ('PUMP2_MODE' in co['MOTOR']) \
      and co['MOTOR']['PUMP2_MODE'].isdigit():
      pv.pump2_mode = int(co['MOTOR']['PUMP2_MODE'])
    else:
      pv.pump2_mode = 1

  if 2 in pv.valid_motors:
    if ('MOTOR' in co) \
      and ('PUMP3_CONFIG' in co['MOTOR']) \
      and co['MOTOR']['PUMP3_CONFIG'].isdigit():
      pv.set_pump_config(2, int(co['MOTOR']['PUMP3_CONFIG']))
    else:
      pv.set_pump_config(2, 0)

    if ('MOTOR' in co) \
      and ('PUMP3_MODE' in co['MOTOR']) \
      and co['MOTOR']['PUMP3_MODE'].isdigit():
      pv.pump3_mode = int(co['MOTOR']['PUMP3_MODE'])
    else:
      pv.pump3_mode = 1

  logger.info(f'1 idle_motors:{pv.idle_motors}')
  logger.info(f'1 busy_motors:{pv.busy_motors}')

  if ('MOTOR'
      in co) and ('LEAD_TIME'
                  in co['MOTOR']) and co['MOTOR']['LEAD_TIME'].isdigit():
    pv.motor_lead_time = int(co['MOTOR']['LEAD_TIME'])
  else:
    pv.motor_lead_time = 10

  if ('SENSOR'
      in co) and ('4MA_REF'
                  in co['SENSOR']) and co['SENSOR']['4MA_REF'].isdigit():
    pv.setting_4ma_ref = int(co['SENSOR']['4MA_REF'])
  else:
    pv.setting_4ma_ref = 700

  if ('SENSOR'
      in co) and ('20MA_REF'
                  in co['SENSOR']) and co['SENSOR']['20MA_REF'].isdigit():
    pv.setting_20ma_ref = int(co['SENSOR']['20MA_REF'])
  else:
    pv.setting_20ma_ref = 4000

  if ('SENSOR'
      in co) and ('ADC_INVALID'
                  in co['SENSOR']) and co['SENSOR']['ADC_INVALID'].isdigit():
    pv.setting_adc_invalid = int(co['SENSOR']['ADC_INVALID'])
  else:
    pv.setting_adc_invalid = 100

  if ('MONITOR' in co) and ('MONITOR_INTERVAL' in co['MONITOR']
                           ) and co['MONITOR']['MONITOR_INTERVAL'].isdigit():
    pv.setting_monitor_interval = int(co['MONITOR']['MONITOR_INTERVAL'])
  else:
    pv.setting_monitor_interval = 1

  if ('MONITOR' in co) and ('SAVE_INTERVAL' in co['MONITOR']
                           ) and co['MONITOR']['SAVE_INTERVAL'].isdigit():
    pv.setting_save_interval = int(co['MONITOR']['SAVE_INTERVAL']) * 3600
  else:
    pv.setting_save_interval = 24 * 3600

  if ('MONITOR' in co) and ('TOLERANCE_TO_AI' in co['MONITOR']
                           ) and co['MONITOR']['TOLERANCE_TO_AI'].isdigit():
    pv.setting_tolerance_to_ai = int(co['MONITOR']['TOLERANCE_TO_AI'])
  else:
    pv.setting_tolerance_to_ai = 3

  if ('MONITOR' in co) and ('TOLERANCE_TO_SENSOR' in co['MONITOR']
                           ) and co['MONITOR']['TOLERANCE_TO_SENSOR'].isdigit():
    pv.setting_tolerance_to_sensor = int(co['MONITOR']['TOLERANCE_TO_SENSOR'])
  else:
    pv.setting_tolerance_to_sensor = 3

  if ('MONITOR' in co) and ('ADC_IGNORE_SPIKE' in co['MONITOR']
                           ) and co['MONITOR']['ADC_IGNORE_SPIKE'].isdigit():
    pv.setting_adc_ignore_spike = int(co['MONITOR']['ADC_IGNORE_SPIKE'])
  else:
    pv.setting_adc_ignore_spike = 100

  if ('MANAGE' in co) and ('USER_ID' in co['MANAGE']):
    pv.user_id = co['MANAGE']['USER_ID']
    pv.password = co['MANAGE']['PASSWORD']

  if ('MANAGE' in co) and ('DEVICE_ROLE' in co['MANAGE']):
    pv.device_role = co['MANAGE']['DEVICE_ROLE']

  logger.info(f'2 valid_motors:{pv.valid_motors}')
  logger.info(f'2 idle_motors:{pv.idle_motors}')
  logger.info(f'2 busy_motors:{pv.busy_motors}')

  #for i, m in enumerate(pv.valid_motors):
  #  ms = motor.get_motor_state(pv.chip, m)
  #  pv.change_motor_list(m, ms)