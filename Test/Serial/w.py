import time
import serial
import sys

port = '/dev/ttyAMA0'
if len(sys.argv)>1:
    port = '/dev/'+sys.argv[1]

ser1 = serial.Serial(
    port=port,
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0) #None=blocking 0=Non-blocking

c = 0
while 1:
  msg = f'1234567890ABCDEFG '
  msg = bytes(msg, 'utf-8')
  n=ser1.write(msg)
  print(f"{port}:write {msg} written:{n}")
  c += 1

  time.sleep(0.5)
