import time
#import picologging as logging
import logging

import lgpio
import spidev

import pump_util as util

logger = logging.getLogger(util.MAIN_LOGGER_NAME)

# /boot/firmware/config.txt
# Free CE0(8), CE1(7), and then control them as GPIO-7 & GPIO-8
# GPIO 24 & 25 are held by SPI driver. So they cannot be used for other purposes.
#   dtoverlay=spi0-2cs,cs0_pin=24,cs1_pin=25
CE_R = 7  # CE1
CE_T = 8  # CE0

def init_spi_rw(chip, pv, speed=4800):
  #현재 회로 구성에서는 CFLOW_PASS를 사용 못함
  #set_current_flow(chip=chip, cflow=CFLOW_PASS)
  #set_current_flow(chip=chip, cflow=CFLOW_CPU)

  lgpio.gpio_claim_output(chip, CE_T, 1)
  lgpio.gpio_claim_output(chip, CE_R, 1)
  time.sleep(0.1)

  spi = spidev.SpiDev()
  spi.open(bus=0, device=0)
  spi.max_speed_hz = speed
  spi.mode = 0
  spi.no_cs = True

  return spi

def writeDAC(chip, v, spi):
  msb = (v >> 8) & 0x0F
  msb = msb | 0x30
  lsb = v & 0xFF

  lgpio.gpio_write(chip, CE_T, 0)
  spi.xfer2([msb, lsb])
  lgpio.gpio_write(chip, CE_T, 1)
  logger.debug("set_DAC({})".format(v))

def waterlevel_rate2ADC(pv, rate):
  if rate<=0:
    v = pv.setting_4ma_ref
  elif rate>=100:
    v = pv.setting_20ma_ref
  else:
    v = pv.setting_4ma_ref + (rate/100) * (pv.setting_20ma_ref-pv.setting_4ma_ref)
  
  return v


def check_water_level(chip, spi):
  return readADC_MSB(chip, spi)


def readADC_MSB(chip, spi):
  """
  Reads 2 bytes (byte_0 and 1) and converts the output code from the MSB-mode:
  byte_0 holds two ?? bits, the null bit, and the 5 MSB bits (B11-B07),
  byte_1 holds the remaning 7 MBS bits (B06-B00) and B01 from the LSB-mode, 
  which has to be removed.
  """
  lgpio.gpio_write(chip, CE_R, 0)
  bytes_received = spi.xfer2([0x00, 0x00])
  lgpio.gpio_write(chip, CE_R, 1)

  #logger.debug("Read:0x{0:2X} 0x{1:2X}".format(bytes_received[0], bytes_received[1]) )
  #logger.debug("Read:0b{0:b} 0b{1:b}".format(bytes_received[0], bytes_received[1]) )

  MSB_1 = bytes_received[1]
  #logger.debug(f"MSB_1:0b{MSB_1:0b}")
  MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode
  #logger.debug(f"MSB_1:0b{MSB_1:0b}")
  MSB_0 = bytes_received[
      0] & 0b00011111  # mask the 2 unknown bits and the null bit
  #logger.debug(f"MSB_0:0b{bytes_received[0]:0b}")
  #logger.debug(f"MSB_0:0b{MSB_0:0b}")
  MSB_0 = MSB_0 << 7  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)
  #logger.debug(f"MSB_0<<7:0b{MSB_0:0b}")
  logger.debug(
      f"MSB_0+MSB_1:0b{MSB_0+MSB_1:0b} 0x{MSB_0+MSB_1:2X} {MSB_0+MSB_1}")
  return MSB_0 + MSB_1


def convert_to_voltage(adc_output, VREF=3.3):
  """
  Calculates analogue voltage from the digital output code (ranging from 0-4095)
  VREF could be adjusted here (standard uses the 3V3 rail from the Rpi)
  """
  return adc_output * (VREF / (2**12 - 1))

