#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://raspberrytips.nl/lcd-scherm-20x4-i2c-raspberry-pi/
# https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load?answertab=votes#tab-top
# https://github.com/adafruit/Adafruit_Python_SSD1306

import sys
import pathlib
from pathlib import Path
from datetime import timedelta
import datetime
import time
import multiprocessing as mp
import signal

import picologging as logging
import lgpio


import ml

# logger 생성하기 위해 가장 먼저 import 해야 함
import pump_util as util
from pump_util import *

from pump_variables import pv
import pump_variables
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

import modbus_server_serial
import modbus_respond

import fan_control

import config
import mqtt_pub

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

logger.info(f"=================================================")
logger.info(f"START at {datetime.datetime.now()}")
logger.info(f"=================================================")


#==============================================================================
# main
#==============================================================================
def main():
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
    lcd.instance = lcd_instance

    from pump_variables import PV
    pv(PV())  # 전역변수를 PV라는 한개의 구조체로 관리한다.
    config.init_setting(pv())
    if not pv().device_role:
      pv().device_role = 'controller'

    pv().mqtt_timeout = config.read_config('MQTT', 'TIMEOUT')
    pv().mqtt_port = config.read_config('MQTT', 'PORT')
    pv().mqtt_broker = config.read_config('MQTT', 'BROKER')
    pv().mqtt_topic = config.read_config('MQTT', 'TOPIC')
    pv().mqtt_client_name = config.read_config('MQTT', 'CLIENT_NAME')

    #client = mqtt_pub.mqtt_init(client_name=pv().mqtt_client_name, broker=pv().mqtt_broker, port=pv().mqtt_port)
    #pv().mqtt_client = client

    chip = lgpio.gpiochip_open(0)  # get GPIO chip handle
    pv().chip = chip
    spi = ADC.init_spi_rw(chip, pv(),
                                   speed=9600)  # get SPI device handle
    motor.init_motors(chip)
    pump_screen.scr_init_msg(pv())

    #lgpio.gpio_claim_output(chip, FAN, 1)

    #import ml
    #if Path("./model/pump_model.json").exists():
    #  pv().model = ml.read_model("pump_model.json")

    # state machine 초기화
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

    # 수위 모니터링을 위한 스레드
    monitor_func = pump_monitor.tank_monitor
    if pv().device_role == "water-sensor":
      monitor_func = pump_monitor.water_sensor_monitor

    mgr = mp.Manager()
    ns = mgr.Namespace()
    ev_req = mp.Event()
    ev_ret = mp.Event()

    train_proc = mp.Process(name="Train Proc",
                          target=ml.train_proc,
                          kwargs={
                              "ns": ns,
                              "ev_req": ev_req,
                              "ev_ret": ev_ret
                          })
    train_proc.start()

    print(f"@@@@@@@ train_proc: {train_proc.pid}")

    monitor = pump_thread.RepeatThread(interval=pv().setting_monitor_interval,
                                       execute=monitor_func,
                                       kwargs={
                                           'chip': chip,
                                           'spi': spi,
                                           'sm': sm_lcd,
                                           'pv': pv(),
                                           'ns': ns,
                                           'ev_req': ev_req,
                                           'ev_ret': ev_ret
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
                                              'chip': chip,
                                              'pipe': p_respond,
                                              'pv': pv()
                                          })
    responder.start()

    logger.info("modbus_id:%d", pv().modbus_id)
    # Modbus 통신을 위한 프로세스
    comm_proc = mp.Process(name="Modbus Server",
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
                          execute=mqtt_pub.mqtt_thread_func,
                          kwargs={
                              'pipe': pipe_mqtt_sensor,
                              'pv': pv()
                          })
    mqtt_thread.start()

    mqtt_pub_proc = mp.Process(name="MQTT PUBLISHER",
                               target=mqtt_pub.mqtt_pub_proc,
                               kwargs={
                                   'pipe_pub': pipe_mqtt_pub,
                                   'mqtt_broker': "ubuntu1t.local",
                                   'mqtt_port': 3881,
                                   'mqtt_client_name': "client1",
                                   'mqtt_topic': "topic1"
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


  except KeyboardInterrupt:
    pass
  #finally:


if __name__ == '__main__':
  main()

'''
if __name__ == '__main__':
  role = "controller"
  for i, arg in enumerate(sys.argv):
    if not i:
      continue
    arg = sys.argv[i]
    l = arg.split('=')
    if len(l)>1 and l[1]=="water-sensor":
      role = l[1]
  
  main(role=role)
'''


'''
#==============================================================================
# Communication
#==============================================================================
PORT = 5999
def comm():
  address = ('localhost', port)     # family is deduced to be 'AF_INET'
  listener = Listener(address)
  conn = listener.accept()
  print('connection accepted from', listener.last_accepted)
  while True:
    msg = conn.recv()
    print("msg:",msg)
    if msg == 'close':
      conn.close()
      break
  listener.close()
'''
