import sys
#import RPi.GPIO as GPIO
import time
import serial

#GPIO.setmode(GPIO.BOARD)
#GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

port = '/dev/ttyAMA0'
if len(sys.argv)>1:
    port = '/dev/'+sys.argv[1]

ser = serial.Serial(port=port,
                    baudrate=9600,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=0) #None=blocking 0=Non-blocking

#ser=serial.Serial(port=port,9600,timeout=0)

while True:
    msg = b"1234567890ABCDEFG "
    ser.write(msg)
    time.sleep(0.5)

    received_data=ser.read(len(msg))
    print(received_data)
    print()
    time.sleep(0.5)

