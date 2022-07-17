import smbus2
import time

addr = 0x51
t = [0x00,0x00,0x18,0x04,0x12,0x08,0x15]
w = ["SUN","Mon","Tues","Wed","Thur","Fri","Sat"]

bus = smbus2.SMBus(10)
def rtcSetTime():
  bus.write_i2c_block_data(addr, 0x00, t)

def rtcReadTime():
  return bus.read_i2c_block_data(addr, 0x00, 7)

def readTime():
  while 1:
    t = rtcReadTime()
    print("rtcReadTime()=",t)
    t[0] = t[0]&0x7F
    t[1] = t[1]&0x7F
    t[2] = t[2]&0x3F
    t[3] = t[3]&0x07
    t[4] = t[4]&0x3F
    t[5] = t[5]&0x1F
    print("20{:x}/{:x}/{:x} {:x}:{:x}:{:x}  {}".format(t[6],t[5],t[4],t[2],t[1],t[0],w[t[3]-1]))
    time.sleep(1)
