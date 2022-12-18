#!/usr/bin/env python

import time
import serial

port = '/dev/serial1'

ser = serial.Serial(port,
                    baudrate=9600,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=0.1)

while 1:
  x=ser.readline()
  print(x)
  time.sleep(0.1)
