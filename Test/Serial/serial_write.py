import time
import serial

ser1 = serial.Serial(
    #port='/dev/ttyAMA0',
    port='/dev/serial2',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=5)

c = 0
while 1:
  msg = f'serial#{c}'
  msg = bytes(msg, 'utf-8')
  #ser1.write(b'serial')
  ser1.write(msg)
  print(f"message {msg}")
  c += 1

  #var = input(">>: ")
  #s = var.strip()
  #print("you entered ", s.encode('ASCII'))
  #ser.write("%s\r"%var)
  #ser.write(b"abc\r")
  time.sleep(1)
