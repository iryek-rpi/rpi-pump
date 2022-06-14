#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://raspberrytips.nl/lcd-scherm-20x4-i2c-raspberry-pi/
# https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load?answertab=votes#tab-top
# https://github.com/adafruit/Adafruit_Python_SSD1306

import logging
from pathlib import Path
from datetime import timedelta
import multiprocessing as mp

import lgpio
import signal
import time
import datetime

from pump_util import *
from pump_lcd import Lcd, lcd
from pump_btn import PumpButtons, buttons
from pump_variables import PV, pv, save_data
from pump_state import LCDStateMachine
from pump_state_set_level import SetLevelStateMachine
from pump_state_set_time import SetTimeStateMachine
from pump_monitor import init_spi_rw, tank_monitor
import pump_thread

import modbus_server_serial
import modbus_respond

#==============================================================================
# 디버그용 로그 설정
#==============================================================================
logging.basicConfig(format='%(asctime)s %(levelname)s:%(filename)s:%(message)s'
  , level=logging.DEBUG
  , datefmt='%Y-%m-%d %H:%M:%S'
  )

#==============================================================================
# 디바이스 구성 요소 초기화
#==============================================================================

# 펌프 3개 GPIO
M0 = 2
M1 = 3
M2 = 4

# 팬 GPIO
FAN = 12

# 동작 모드 확인용 GPIO
RUN_MODE = 17

# I2C 주소
I2C_BUS = 10      # PCB 보드의 I2C (라즈베리파이 IO 보드는 1)
I2C_RTC  = 0x51   # Real Time Clock 디바이스 I2C 주소
I2C_LCD  = 0x27   # 1602 LCD 디바이스 I2C 주소

#==============================================================================
# systemd 
#==============================================================================
is_shutdown = False

def stop(sig, frame):
  logging.info(f"SIGTERM at {datetime.datetime.now()}")
  global is_shutdown
  is_shutdown = True

def ignore(sig, frame):
  logging.info(f"SIGHUP at {datetime.datetime.now()}")

signal.signal(signal.SIGTERM, stop)
#signal.signal(signal.SIGHUP, stop)

logging.info(f"=================================================")
logging.info(f"START at {datetime.datetime.now()}")
logging.info(f"=================================================")

#==============================================================================
# main 
#==============================================================================
def main():
  try:
    i2c_bus = 1   # 라즈베리파이 개발용 IO 보드에서는 1
    lcd_instance = Lcd(addr=0x27, bus=i2c_bus)
    time.sleep(0.1)
  except:
    i2c_bus = 10  # SM Tech 수위조절기 보드에서는 10
    lcd_instance = Lcd(addr=0x27, bus=i2c_bus)
    time.sleep(0.1)
  finally:
    logging.info("BUS:{:02d} LCD ADDR:{:02X}".format(i2c_bus, I2C_LCD))

  #i2c_rtc = lgpio.i2c_open(10, I2C_RTC) # 10 for RTC bus both on pump & CM4IO board

  try:
    lcd.instance = lcd_instance

    pv(PV())  # 전역변수를 PV라는 한개의 구조체로 관리한다. 

    chip = lgpio.gpiochip_open(0)              # get GPIO chip handle
    spi = init_spi_rw(chip, pv(), speed=9600)  # get SPI device handle

    # state machine 초기화
    sm_lcd = LCDStateMachine(name='LCDStateMachine', pv=pv())
    sm_level = SetLevelStateMachine(name='SetLevelStateMachine', pv=pv())
    sm_time = SetTimeStateMachine(name='SetTimeStateMachine', pv=pv())
    # a list of three machines
    sm_list = [sm_lcd, sm_level, sm_time]

    # state machine 객체를 지정하여 버튼 객체 초기화
    buttons(PumpButtons(sm_list))

    # 수위 모니터링을 위한 스레드
    monitor = pump_thread.RepeatThread(interval=pv().setting_interval_monitor, execute=tank_monitor, 
                    kwargs={'chip':chip, 'spi':spi, 'sm':sm_lcd, 'pv':pv()})
    monitor.start()

    # 수위 저장을 위한 스레드
    logging.info("datapath: {}".format(pv().data_path))
    Path(pv().data_path).mkdir(parents=True, exist_ok=True)
    saver = pump_thread.RepeatThread(interval=pv().setting_interval_save, 
              execute=save_data, kwargs={'pv':pv()})
    saver.start()

    # Modbus 요청 처리를 위한 스레드
    p_respond, p_req = mp.Pipe()
    responder = pump_thread.RespondThread(execute=modbus_respond.respond, 
                    kwargs={'pipe':p_respond, 'pv':pv()})
    responder.start()

    comm_proc = mp.Process(name="Modbus Server", target=modbus_server_serial.rtu_server_proc, args={p_req})
    comm_proc.start()

    while not is_shutdown:
      pass

    # 스레드와 프로세스 정리
    monitor.stop()
    responder.stop()
    saver.stop()
    comm_proc.join()

    save_data(pv=pv())
    lcd().clear()

  except KeyboardInterrupt:
    pass
  #finally:

if __name__ == '__main__':
    main()


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
