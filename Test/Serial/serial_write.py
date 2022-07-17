import time
import serial

ser = serial.Serial(
    #port='/dev/ttyAMA0',
    port='/dev/serial1',
    baudrate = 115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=5
)

while 1:
    #var = input(">>: ")
    #s = var.strip()
    #print("you entered ", s.encode('ASCII'))
    #ser.write("%s\r"%var)
    #ser.write(b"abc\r")
    ser.write(b"abc")
    time.sleep(2)