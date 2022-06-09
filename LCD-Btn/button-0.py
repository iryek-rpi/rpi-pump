from gpiozero import Button
from time import sleep
import lgpio
from pprint import pprint

from lcd import *

L1 = LCD_LINE_1
L2 = LCD_LINE_2

B0 = 16
B1 = 20
B2 = 21

BOUNCE_TIME = 0.05 #50ms 
HOLD_TIME = 1.0 # 1sec


def when_held0(d):
    when_held0.held=True
    print()
    print("B0 held:",d)
    #pprint(dir(d))
    print(f"is_active:{d.is_active} active_time:{d.active_time}")
    print(f"is_held:{d.is_held} held_time:{d.held_time}")
    print(f"is_pressed:{d.is_pressed} pressed_time:{d.pressed_time}")
    print(f"hold_time:{d.hold_time}")
    lcd_string("B0 held",L2)
when_held0.held=False

def when_held1(d):
    print()
    print("B1 held:",d)

def when_held2(d):
    print()
    print("B2 held:",d)

def when_pressed0(d):
    when_held0.held=False
    #print()
    #print("B0 pressed:",d)
    #lcd_string("B0 pressed",L1)

def when_pressed1(d):
    print()
    print("B1 pressed:",d)

def when_pressed2(d):
    print()
    print("B2 pressed:",d)

def when_released0(d):
    if when_held0.held==False:
        print()
        print("B0 released:",d)
        #pprint(dir(d))
        print(f"is_active:{d.is_active} active_time:{d.active_time}")
        print(f"is_held:{d.is_held} held_time:{d.held_time}")
        print(f"is_pressed:{d.is_pressed} pressed_time:{d.pressed_time}")
        print(f"hold_time:{d.hold_time}")
        lcd_string("B0 released",L1)


def when_released1(d):
    print()
    print("B1 released:",d)
    #pprint(dir(d))
    lcd_string("B1 released",L1)

def when_released2(d):
    print()
    print("B2 released:",d)
    #pprint(dir(d))
    lcd_string("B2 released",L1)

def button_init():
    b0 = Button(B0, bounce_time=BOUNCE_TIME, 
            hold_time=HOLD_TIME)
            #, pin_factory=LGPIOFactory)
    b1 = Button(B1, bounce_time=BOUNCE_TIME, 
            hold_time=HOLD_TIME)
    b2 = Button(B2, bounce_time=BOUNCE_TIME, 
            hold_time=HOLD_TIME)

    b0.when_held = when_held0
    b1.when_held = when_held1
    b2.when_held = when_held2

    b0.when_pressed = when_pressed0
    b1.when_pressed = when_pressed1
    b2.when_pressed = when_pressed2

    b0.when_released = when_released0
    b1.when_released = when_released1
    b2.when_released = when_released2

if __name__ == '__main__':
    button_init()
    lcd = lgpio.i2c_open(10, 0x27)
    lcd_init(lcd)

    while True:
        sleep(0.01)