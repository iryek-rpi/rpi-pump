import time
import serial

ser1 = serial.Serial(
    port='/dev/serial1',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1)

c = 0
while 1:
  msg = f'From pi#{c}'
  msg = bytes(msg, 'utf-8')
  #ser1.write(b'serial')
  ser1.write(msg)
  print(f"write {msg}")
  c += 1

  time.sleep(0.5)

  x = ser1.read(10)
  if len(x)>0:
      print(x)
  else:
      print('no data to read')
  time.sleep(0.5)
