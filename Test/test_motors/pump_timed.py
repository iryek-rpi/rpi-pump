#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from subprocess import check_output     
from datetime import timedelta

import lgpio
import signal
import time
import datetime

from pump_util import *
from pump_variables import PV, pv

is_shutdown = False

#==============================================================================
# systemd 
#==============================================================================
def stop(sig, frame):
  print(f"SIGTERM at {datetime.datetime.now()}")
  global is_shutdown
  is_shutdown = True

def ignore(sig, frame):
  print(f"SIGHUP at {datetime.datetime.now()}")

#==============================================================================
# Scheduling
#==============================================================================
WAIT_TIME_SECONDS = 1

class ProgramKilled(Exception):
  pass

def foo():
  print time.ctime()
    
def signal_handler(signum, frame):
  raise ProgramKilled
    
class Job(threading.Thread):
  def __init__(self, interval, execute, *args, **kwargs):
    threading.Thread.__init__(self)
    self.daemon = False
    self.stopped = threading.Event()
    self.interval = interval
    self.execute = execute
    self.args = args
    self.kwargs = kwargs
      
  def stop(self):
    self.stopped.set()
    self.join()
  def run(self):
    while not self.stopped.wait(self.interval.total_seconds()):
      self.execute(*self.args, **self.kwargs)

#==============================================================================
# Device Properties
#==============================================================================

def main():
  try:
    i2c_bus = 1   # 1 for i2c bus for LCD on CM4IO board
    lcd_instance = Lcd(addr=0x27, bus=i2c_bus)
    time.sleep(0.1)
  except:
    i2c_bus = 10  # 10 for i2c bus for LCD & RTC on Pump board
    lcd_instance = Lcd(addr=0x27, bus=i2c_bus)
    time.sleep(0.1)
  finally:
    print("BUS:{:02d} LCD ADDR:{:02X}".format(i2c_bus, I2C_LCD))

  #i2c_rtc = lgpio.i2c_open(10, I2C_RTC) # 10 for RTC bus both on pump & CM4IO board

  lcd.instance = lcd_instance

  pv.instance = PV()  # pump variables
  lcd_sm = LCDStateMachine(name='LCDStateMachine', pv=pv())
  buttons(PumpButtons(lcd_sm))

  while not is_shutdown:
    pass

if __name__ == '__main__':
  try:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGHUP, stop)

    print(f"\n=================================================")
    print(f"\nSTART at {datetime.datetime.now()}")
    print(f"\n=================================================")

    main()
  except KeyboardInterrupt:
    pass
  finally:
    lcd().clear()

