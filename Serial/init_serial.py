import os, sys
import serial
import time

#port = '/dev/ttyAMA0'
port = '/dev/serial1'

def init_serial():
    return serial.Serial(port,19200, timeout = 5)

def run(s):
    msg = b'567'
    n_read=3
    while True:
        print("Reading {} bytes from {}".format(n_read, port))
        line = s.read(n_read)
        print("line: ", line)
        if len(line) > 0:
            print("Received: ", line)
            #hex_list = ["{:x}".format(ord(c)) for c in line];
            #print(''.join(hex_list))
        print("Writing {} bytes to {}".format(len(msg), port))
        s.write(msg)
        time.sleep(3)

if __name__ == '__main__':
  s=init_serial()
  run(s)