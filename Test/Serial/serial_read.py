#!/usr/bin/env python

import time
import serial

#o port = '/dev/serial1'
port = '/dev/serial2'
#o port = '/dev/ttyAMA0'
#x port = '/dev/ttyAMA1'
ser = serial.Serial(
    port,
    baudrate = 115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=3
)

while 1:
    #x=ser.readline()
    x=ser.read(3)
    if len(x)>1:
       print(x)
    time.sleep(2)
