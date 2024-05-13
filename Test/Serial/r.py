#!/usr/bin/env python

import time
import serial
import sys

if len(sys.argv)>1:
    port = '/dev/'+sys.argv[1]
else:
    port = '/dev/serial2'

ser = serial.Serial(port=port,
                    baudrate=9600,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=1)

while 1:
  x = ser.read(10)
  if len(x)>0:
      print(x)
  else:
    print(f'{port}: no data')
  time.sleep(0.5)

