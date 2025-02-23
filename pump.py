#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://raspberrytips.nl/lcd-scherm-20x4-i2c-raspberry-pi/
# https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load?answertab=votes#tab-top
# https://github.com/adafruit/Adafruit_Python_SSD1306

from pathlib import Path
import datetime
import time
import multiprocessing as mp
#import signal

#import picologging as logging
import logging
import lgpio

# logger 생성하기 위해 가장 먼저 import 해야 함
import pump_util as util
from pump_util import *

from pump_variables import pv
from pump_lcd import Lcd, lcd
import pump_screen
from pump_btn import PumpButtons, buttons
from pump_state import LCDStateMachine
from pump_state_set_level import SetLevelStateMachine
from pump_state_set_time import SetTimeStateMachine
import pump_monitor
import pump_thread
import motor
import ADC

#import modbus_server_serial_sync
import modbus_server_serial
import modbus_respond

import fan_control

import config
import mqtt_pub
import constant

#==============================================================================
# 디버그용 로그 설정
#==============================================================================
#logging.basicConfig(
#    filename=MAIN_LOGFILE_NAME,
#    filemode="a",
#    #format='%(asctime)s %(threadName) %(levelname)s:%(filename)s:%(message)s',
#    format=FORMAT,
#    level=logging.debug,
#    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(util.MAIN_LOGGER_NAME)

#==============================================================================
# 디바이스 구성 요소 초기화
#==============================================================================

# I2C 주소
I2C_BUS = 10  # PCB 보드의 I2C (라즈베리파이 IO 보드는 1)
I2C_RTC = 0x51  # Real Time Clock 디바이스 I2C 주소
I2C_LCD = 0x27  # 1602 LCD 디바이스 I2C 주소

FAN = 12

#==============================================================================
# systemd
#==============================================================================
is_shutdown = False

def ctrl_c_handler(sig, frame):
  logger.info(f"SIGINT at {datetime.datetime.now()}")
  logger.info('You pressed Ctrl+C!')
  print(f"frame:{frame}")
  global is_shutdown
  is_shutdown=True

def stop(sig, frame):
  logger.info(f"SIGTERM at {datetime.datetime.now()}")
  print(f"frame:{frame}")
  global is_shutdown
  is_shutdown = True

def ignore(sig, frame):
  logger.info(f"SIGHUP at {datetime.datetime.now()}")
  print(f"frame:{frame}")

#signal.signal(signal.SIGTERM, stop)
#signal.signal(signal.SIGINT, ctrl_c_handler)
#signal.signal(signal.SIGHUP, ignore)

def mqtt_thread_func(**kwargs):
  '''logger 사용을 위해 pump.py에 정의'''
  _pipe = kwargs['pipe']
  pv = kwargs['pv']

  logger.debug(f'mqtt_thread:{pv.water_level}')
  if pv.source == constant.SOURCE_SENSOR:
    _pipe.send((pv.sensor_level, -1, pv.setting_low, pv.setting_high))
  else:
    _pipe.send((-1, pv.water_level, pv.setting_low, pv.setting_high))

logger.info(f"=================================================")
logger.info(f"START at {datetime.datetime.now()}")
logger.info(f"=================================================")

def delete_logs():
  '''Delete log files from ./logs directory older than 2 days'''
  now = datetime.datetime.now()
  for f in Path('./logs').glob("*.log"):
    if (now - datetime.datetime.fromtimestamp(f.stat().st_mtime)).days > 2:
      f.unlink()

#==============================================================================
# main
#==============================================================================
def main():
  delete_logs()

  chip = lgpio.gpiochip_open(0)  # get GPIO chip handle
  logger.info("GPIO chip handle: %d", chip)
  logger.info(f"GPIO chip info: {lgpio.gpio_get_chip_info(chip)}")

  from pump_variables import PV
  pv(PV())  # 전역변수를 PV라는 한개의 구조체로 관리한다.
  pv().chip = chip

  motor.init_motors(chip)
  (a, b, c) = motor.get_all_motors(chip, pv())
  print(f"After init: get_all_motors:({a}, {b}, {c})")
  logger.info("After init: get_all_motors:(%d, %d, %d)", a, b, c)
  time.sleep(0.5)
  motor.set_all_motors(chip, (0, 0, 0)) # 모터 구동 중 시작하면 모터 off로 인식하는 문제로 인해 초기화

  try:
    i2c_bus = 1  # 라즈베리파이 개발용 IO 보드에서는 1
    lcd_instance = Lcd(addr=0x27, bus=i2c_bus)
    time.sleep(0.1)
  except:
    i2c_bus = 10  # SM Tech 수위조절기 보드에서는 10
    lcd_instance = Lcd(addr=0x27, bus=i2c_bus)
    time.sleep(0.1)
  finally:
    logger.info("BUS:{:02d} LCD ADDR:{:02X}".format(i2c_bus, I2C_LCD))

  #i2c_rtc = lgpio.i2c_open(10, I2C_RTC) # 10 for RTC bus both on pump & CM4IO board

  try:
#    for c in range(5):
#      try:
#        lgpio.gpiochip_close(c)
#      except:
#        pass


    lcd.instance = lcd_instance


    config.init_setting(pv()) # motor port 초기화한 후에 콜해야함

    if not pv().device_role:
      pv().device_role = 'controller'

    pv().mqtt_on = config.read_config('MQTT', 'MQTT_ON')
    pv().mqtt_timeout = config.read_config('MQTT', 'TIMEOUT')
    pv().mqtt_port = config.read_config('MQTT', 'PORT')
    pv().mqtt_broker = config.read_config('MQTT', 'BROKER')
    pv().mqtt_topic = config.read_config('MQTT', 'TOPIC')
    pv().mqtt_client_name = config.read_config('MQTT', 'CLIENT_NAME')

    #client = mqtt_pub.mqtt_init(client_name=pv().mqtt_client_name, broker=pv().mqtt_broker, port=pv().mqtt_port)
    #pv().mqtt_client = client

    pump_screen.scr_init_msg(pv())

    #lgpio.gpio_claim_output(chip, FAN, 1)

    # state machine 초기화
    logging.getLogger('transitions').setLevel(logging.CRITICAL)

    sm_lcd = LCDStateMachine(name='LCDStateMachine', pv=pv())
    sm_level = SetLevelStateMachine(name='SetLevelStateMachine', pv=pv())
    sm_time = SetTimeStateMachine(name='SetTimeStateMachine', pv=pv())
    # a list of three machines
    sm_list = [sm_lcd, sm_level, sm_time]

    # state machine 객체를 지정하여 버튼 객체 초기화
    buttons(PumpButtons(sm_list))

    #==============================================================================
    # Thread & Process
    #==============================================================================
    # pump_monotor.tank_monitor
    #   * 수위 모니터링 스레드
    #   * kwargs={'chip':chip, 'spi':spi, 'sm':sm_lcd, 'pv':pv()})
    #
    # pump_variables.save_data
    #   * 수위 저장 스레드
    #   * kwargs={'pv':pv()}
    #
    # modbus_respond.respond
    #   * Modbus 요청 응답 대기 스레드
    #   * kwargs={'pipe':p_respond, 'pv':pv()}
    #
    # modbus_server_serial.rtu_server_proc
    #   * Modbus 서버 프로세스
    #   * args={p_req}

    spi = ADC.init_spi_rw(chip, pv(),
                                   speed=9600)  # get SPI device handle

    pv().simulation = False
    if pv().simulation:
      pv().adc_start_time = time.perf_counter()

    # 수위 모니터링을 위한 스레드
    monitor_func = pump_monitor.tank_monitor
    if pv().device_role == "water-sensor":
      monitor_func = pump_monitor.water_sensor_monitor

    monitor = pump_thread.RepeatThread(interval=pv().setting_monitor_interval,
                                       execute=monitor_func,
                                       kwargs={
                                           'chip': chip,
                                           'spi': spi,
                                           'sm': sm_lcd,
                                           'pv': pv()
                                       })
    monitor.start()

    # 수위 저장을 위한 스레드
    logger.info(f"datapath: {pv().data_path}")
    Path(pv().data_path).mkdir(parents=True, exist_ok=True)
    saver = pump_thread.RepeatThread(interval=pv().setting_save_interval,
                                     execute=util.save_data,
                                     kwargs={'pv': pv()})
    saver.start()

    # Modbus 요청 처리를 위한 스레드
    p_respond, p_req = mp.Pipe()
    responder = pump_thread.RespondThread(execute=modbus_respond.respond,
                                          kwargs={
                                              'pipe': p_respond,
                                              'pv': pv()
                                          })
    responder.start()

    logger.info("modbus_id:%d", pv().modbus_id)
    # Modbus 통신을 위한 프로세스
    comm_proc = mp.Process(name="Modbus Server",
                           #target=modbus_server_serial_sync.rtu_server_proc,
                           target=modbus_server_serial.rtu_server_proc,
                           kwargs={
                               'pipe_request': p_req,
                               'modbus_id': pv().modbus_id
                           })
    comm_proc.start()
    logger.info(f"@@@@@@@ comm_proc: {comm_proc.pid}")

    pipe_mqtt_sensor, pipe_mqtt_pub = mp.Pipe()
    mqtt_thread = pump_thread.RepeatThread(
                          interval=5,
                          execute=mqtt_thread_func,
                          kwargs={
                              'pipe': pipe_mqtt_sensor,
                              'pv': pv()
                          })
    mqtt_thread.start()

    mqtt_pub_proc = mp.Process(name="MQTT PUBLISHER",
                               target=mqtt_pub.mqtt_pub_proc,
                               kwargs={
                                   'pipe_pub': pipe_mqtt_pub,
                                   'mqtt_broker': pv().mqtt_broker,
                                   'mqtt_port': int(pv().mqtt_port),
                                   'mqtt_client_name': pv().mqtt_client_name, 
                                   'mqtt_topic': pv().mqtt_topic,
                               })
    mqtt_pub_proc.start()
    logger.info(f"@@@@@@ mqtt_proc: {mqtt_pub_proc.pid}")

    logger.info("Starting fan control")
    # fan control process
    fan_logger = logging.getLogger(name = util.FAN_LOGGER_NAME)
    fan_proc = mp.Process(name="Fan Control",
                           target=fan_control.fan_proc,
                           kwargs = {'logger': fan_logger})
    fan_proc.start()

    logger.info(f"@@@@@@ fan_proc: {fan_proc.pid}")

    while not is_shutdown:
      pass

    logger.info("################### out of main loop ##################")
    logger.info(f"lcd():{lcd()}")
    lcd().clear()

    p_respond.close()
    p_req.close()
    pipe_mqtt_pub.close()
    pipe_mqtt_sensor.close()

    # 스레드와 프로세스 정리
    monitor.stop()
    # 모터 동작 중 종료 후 다시 시작하면 모터가 off 되어 있는 것으로 인식하는 
    # 문제로 인해 종료 시 모터를 off 시킴
    motor.set_all_motors(chip, 0)  

    responder.stop()
    saver.stop()
    
    comm_proc.terminate()
    comm_proc.join()

    mqtt_thread.stop()
    mqtt_pub_proc.terminate()
    mqtt_pub_proc.join()

    fan_proc.terminate()
    fan_proc.join()
    #fan_proc.kill()

    util.save_data(pv=pv())
    lgpio.gpiochip_close(chip)


  except KeyboardInterrupt:
    pass
  #finally:


if __name__ == '__main__':
  main()
