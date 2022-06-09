#gpiozero test

from gpiozero import Button
from time import sleep

B0 = 16
B1 = 20
B2 = 21

BOUNCE_TIME = 0.2
HOLD_TIME = 1.0

b0 = Button(B0, bounce_time=BOUNCE_TIME, hold_time=HOLD_TIME)
b1 = Button(B1, bounce_time=BOUNCE_TIME, hold_time=HOLD_TIME)
b2 = Button(B2, bounce_time=BOUNCE_TIME, hold_time=HOLD_TIME)

def when_held0(d):
    print("B0 held:",d)

def when_held1(d):
    print("B1 held:",d)

def when_held2(d):
    print("B2 held:",d)

def when_pressed0(d):
    print("B0 pressed:",d)

def when_pressed1(d):
    print("B1 pressed:",d)

def when_pressed2(d):
    print("B2 pressed:",d)

b0.when_held = when_held0
b1.when_held = when_held1
b2.when_held = when_held2

b0.when_pressed = when_pressed0
b1.when_pressed = when_pressed1
b2.when_pressed = when_pressed2

while True:
    sleep(0.01)