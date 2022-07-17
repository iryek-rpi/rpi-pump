# https://www.circuitbasics.com/using-potentiometers-with-raspberry-pi/

#import RPi.GPIO as GPIO
from lgpio import *
import time

h = gpiochip_open(0)
print("h: ", h)

G18 = 18
G24 = 24

def discharge():
    gpio_claim_input(h, G18)
    gpio_claim_output(h, G24, False)
    gpio_write(h, G24, False)
    time.sleep(0.004)

def charge_time():
    gpio_claim_input(h, G24)
    gpio_claim_output(h, G18, False)
    count = 0
    gpio_write(h, G18, True)
    while not gpio_read(h, G24):
        count = count + 1
        print("count: ", count)
    return count

def analog_read():
    discharge()
    return charge_time()

while True:
    print("analog_read:", analog_read())
    time.sleep(1)
