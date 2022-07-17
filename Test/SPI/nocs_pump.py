#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
# from https://github.com/flohwie/raspi-MCP3201

import spidev
from time import sleep

import lgpio

CE_R = 7
CE_T = 8

CSW0 = 26
CSW1 = 19
CSW2 = 13

CFLOW_PASS = 0
CFLOW_CPU = 1

#def set_current_flow(chip, cflow):
#  if cflow == CFLOW_PASS:
#    lgpio.gpio_write(chip, CSW0, 0)
#    lgpio.gpio_write(chip, CSW1, 0)
#    lgpio.gpio_write(chip, CSW2, 0)
#  else:
#    lgpio.gpio_write(chip, CSW0, 1)
#    lgpio.gpio_write(chip, CSW1, 1)
#    lgpio.gpio_write(chip, CSW2, 1)


def init_spi_rw(chip, speed=4800):
  #  set_current_flow(chip=chip, cflow=CFLOW_CPU)

  lgpio.gpio_claim_output(chip, CE_T, 1)
  lgpio.gpio_claim_output(chip, CE_R, 1)
  sleep(0.1)

  spi = spidev.SpiDev()
  spi.open(bus=0, device=0)
  spi.max_speed_hz = speed
  spi.mode = 0
  spi.no_cs = True

  return spi


def init():
  chip = lgpio.gpiochip_open(0)

  spi = init_spi_rw(chip=chip, speed=4800)

  return spi, chip


def loop_rw(v1, v2, loop_count, chip, spi):
  for i in range(loop_count):
    print("\nlooping: {}".format(i))
    writeDAC(v1, spi, chip)
    print("--- ADC write v1: {}".format(v1))
    sleep(0.6)
    writeDAC(v2, spi, chip)
    print("--- ADC write v2: {}".format(v2))
    sleep(0.2)
    code = readADC_MSB(spi, chip)
    sleep(0.2)
    print("### ADC read: {}".format(code))


def writeDAC(v, spi, chip):
  msb = (v >> 8) & 0x0F
  msb = msb | 0x30
  lsb = v & 0xFF

  lgpio.gpio_write(chip, CE_T, 0)
  spi.xfer2([msb, lsb])
  lgpio.gpio_write(chip, CE_T, 1)
  print("set_DAC(", v, ")")


def readADC_MSB(spi, chip):
  lgpio.gpio_write(chip, CE_R, 0)
  bytes_received = spi.xfer2([0x00, 0x00])
  lgpio.gpio_write(chip, CE_R, 1)

  print("bytes_received:", bytes_received)
  print("Read:{} {}".format(bytes_received[0], bytes_received[1]))
  print("Read:{0:b} {1:b}".format(bytes_received[0], bytes_received[1]))

  MSB_1 = bytes_received[1]
  MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode
  MSB_0 = bytes_received[
      0] & 0b00011111  # mask the 2 unknown bits and the null bit
  MSB_0 = MSB_0 << 7  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)
  return MSB_0 + MSB_1


def convert_to_voltage(adc_output, VREF=3.3):
  return adc_output * (VREF / (2**12 - 1))


if __name__ == '__main__':

  try:
    spi, spi2, chip = init()
    while True:
      for i in range(9, 43):

        ADC_output_code = readADC_MSB(spi, chip)
        ADC_voltage = convert_to_voltage(ADC_output_code)
        print("MCP3201 output code (MSB-mode): %d" % ADC_output_code)
        print("MCP3201 voltage: %0.2f V" % ADC_voltage)
        print("")
        sleep(1)  # wait minimum of 100 ms between ADC measurements

        writeDAC(i * 100, spi, chip)
        #writeDAC(4020) # 4020 -> 1111 1011 0100
        sleep(1)

  except (KeyboardInterrupt):
    print('\n', "Exit on Ctrl-C: Good bye!")

  except:
    print("Other error or exception occurred!")
    raise

  finally:
    print()
