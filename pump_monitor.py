#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
from time import sleep
import datetime
import signal

import logging

import lgpio
import spidev

import csv

from pump_util import *
from pump_variables import MODE_AI, MODE_PLC
from pump_thread import CommThread

#==============================================================================
# Device Properties
#==============================================================================

# /boot/firmware/config.txt
# Free CE0(8), CE1(7), and then control them as GPIO-7 & GPIO-8 
# GPIO 24 & 25 are held by SPI driver. So they cannot be used for other purposes.  
#   dtoverlay=spi0-2cs,cs0_pin=24,cs1_pin=25   
CE_R = 7  # CE1
CE_T = 8  # CE0

M0 = 2
M1 = 3
M2 = 4

CSW0 = 26
CSW1 = 19
CSW2 = 13

RUN_MODE = 17

def motor_state(chip, m):
  if m==0:
    return lgpio.gpio_read(chip, M0)
  elif m==1:
    return lgpio.gpio_read(chip, M1)
  else:
    return lgpio.gpio_read(chip, M2)

def writeDAC(chip, v, spi):
  msb = (v >> 8) & 0x0F
  msb = msb | 0x30
  lsb = v & 0xFF
  
  lgpio.gpio_write(chip, CE_T, 0)
  spi.xfer2([msb, lsb])
  lgpio.gpio_write(chip, CE_T, 1)
  logging.debug("set_DAC({})".format(v))

def water_level_rate(pv, wl=None):
  if wl==None:
    wl = pv.water_level

  rate = 0.0
  if wl >= pv.setting_20ma_ref:
    rate = 100.0
  elif wl < pv.setting_4ma_ref:
    rate = 0.0
  else:
    rate = ((wl-pv.setting_4ma_ref) / (pv.setting_20ma_ref-pv.setting_4ma_ref))*100.0

  return rate

def check_water_level(chip, spi):
  return readADC_MSB(chip, spi)

def readADC_MSB(chip,spi):
  """
  Reads 2 bytes (byte_0 and 1) and converts the output code from the MSB-mode:
  byte_0 holds two ?? bits, the null bit, and the 5 MSB bits (B11-B07),
  byte_1 holds the remaning 7 MBS bits (B06-B00) and B01 from the LSB-mode, 
  which has to be removed.
  """
  lgpio.gpio_write(chip, CE_R, 0)
  bytes_received = spi.xfer2([0x00, 0x00])
  lgpio.gpio_write(chip, CE_R, 1)

  #logging.debug("Read:0x{0:2X} 0x{1:2X}".format(bytes_received[0], bytes_received[1]) )
  #logging.debug("Read:0b{0:b} 0b{1:b}".format(bytes_received[0], bytes_received[1]) )

  MSB_1 = bytes_received[1]
  #logging.debug(f"MSB_1:0b{MSB_1:0b}")
  MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode
  #logging.debug(f"MSB_1:0b{MSB_1:0b}")
  MSB_0 = bytes_received[0] & 0b00011111  # mask the 2 unknown bits and the null bit
  #logging.debug(f"MSB_0:0b{bytes_received[0]:0b}")
  #logging.debug(f"MSB_0:0b{MSB_0:0b}")
  MSB_0 = MSB_0 << 7  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)
  #logging.debug(f"MSB_0<<7:0b{MSB_0:0b}")
  logging.debug(f"MSB_0+MSB_1:0b{MSB_0+MSB_1:0b} 0x{MSB_0+MSB_1:2X} {MSB_0+MSB_1}")
  return MSB_0 + MSB_1

def convert_to_voltage(adc_output, VREF=3.3):
  """
  Calculates analogue voltage from the digital output code (ranging from 0-4095)
  VREF could be adjusted here (standard uses the 3V3 rail from the Rpi)
  """
  return adc_output * (VREF / (2 ** 12 - 1))

CFLOW_PASS = 0
CFLOW_CPU = 1
def set_current_flow(chip, cflow=CFLOW_PASS):
  if cflow==CFLOW_PASS:
    lgpio.gpio_write(chip, CSW0, 0)
    lgpio.gpio_write(chip, CSW1, 0)
    lgpio.gpio_write(chip, CSW2, 0)
  else:
    lgpio.gpio_write(chip, CSW0, 1)
    lgpio.gpio_write(chip, CSW1, 1)
    lgpio.gpio_write(chip, CSW2, 1)

def tank_monitor(**kwargs):
  n0 = datetime.datetime.now()
  chip=kwargs['chip']
  spi=kwargs['spi']
  sm=kwargs['sm']
  pv=kwargs['pv']

  level = check_water_level(chip, spi)
  time_now = datetime.datetime.now()
  logging.debug("monitor at {}".format(time_now.ctime()))

  if level<100:
    if pv.time_no_input==None:
      pv.time_no_input = time_now

    td = time_now - pv.time_no_input
    if td.seconds > pv.setting_tolerance_to_ai:
      if pv.mode==MODE_PLC:
        pv.mode = MODE_AI
        set_current_flow(chip=chip, cflow=CFLOW_CPU)
      # get prediction from ML model
      pv.water_level = pv.last_valid_level  # 임시
    else:
      pv.water_level = pv.last_valid_level  # 마지막 유효 입력
# ADC_TEST
  else:
#    if pv.mode==MODE_AI:
#      pv.mode = MODE_PLC
#      set_current_flow(chip=chip, cflow=CFLOW_PASS)

    pv.time_no_input = None
    pv.water_level = pv.filter_data(level)
    pv.last_valid_level = pv.water_level

  logging.debug("level:{} filtered:{}".format(level, pv.water_level))
  pv.append_data([
      time_now.strftime("%Y-%m-%d %H:%M:%S"), 
      pv.water_level, 
      motor_state(chip, 0),
      motor_state(chip, 1),
      motor_state(chip, 2),
      pv.mode])

# ADC_TEST
  logging.debug("writeDAC(level:{}, filtered:{})".format(level, pv.water_level))
  writeDAC(chip, level, spi)
  writeDAC(chip, pv.water_level, spi)
  sm.update_idle()

def init_spi_rw(chip, pv, speed=4800):
# ADC_TEST
  #set_current_flow(chip=chip, cflow=CFLOW_PASS)
  set_current_flow(chip=chip, cflow=CFLOW_CPU)

  lgpio.gpio_claim_output(chip,CE_T,1)
  lgpio.gpio_claim_output(chip,CE_R,1)
  time.sleep(0.1)

  spi = spidev.SpiDev()
  spi.open(bus=0, device=0)
  spi.max_speed_hz = speed
  spi.mode = 0
  spi.no_cs = True

  return spi

def main():
  from pump_variables import PV, pv
  try:
    pv.instance = PV()  # pump variables

    chip = lgpio.gpiochip_open(0)
    set_current_flow(chip=chip, cflow=CFLOW_PASS)
    pv().mode = MODE_PLC

    lgpio.gpio_claim_output(chip,CE_T,1)
    lgpio.gpio_claim_output(chip,CE_R,1)
    time.sleep(0.1)

    spi = spidev.SpiDev()
    spi.open(bus=0, device=0)
    spi.max_speed_hz = 4800
    spi.mode = 0
    spi.no_cs = True

    conn = Client(('localhost', 5999))

    while not is_shutdown:
      ADC_output_code = readADC_MSB(chip, spi)
      logging.debug("MCP3201 output code (MSB-mode): {}".foramt(ADC_output_code))
      ADC_voltage = convert_to_voltage(ADC_output_code)
      logging.debug("MCP3201 voltage: {%0.2f}V".format(ADC_voltage))
      conn.send(ADC_voltage)
      
      sleep(0.1)  # wait minimum of 100 ms between ADC measurements
  
      #writeDAC(chip=chip, v=ADC_voltage*100, spi=spi) 
      #writeDAC(4020) # 4020 -> 1111 1011 0100
      sleep(2)
  except KeyboardInterrupt:
    time.sleep(0.1)
  finally:
    lgpio.gpiochip_close(chip)
    conn.close()

if __name__ == '__main__':
  is_shutdown = False

#==============================================================================
# systemd 
#==============================================================================
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

  main()


'''
4mA -> 726 -> 0.59v
       741 -> 0.6v
19.95mA -> 3900 -> 3.15v

32 -> 1.4
4.1 -> 0.7

SimonX
29 -> 5.8mA
0 -> 4.8mA
'''