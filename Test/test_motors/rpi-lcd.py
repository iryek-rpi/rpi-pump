#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://raspberrytips.nl/lcd-scherm-20x4-i2c-raspberry-pi/
# https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load?answertab=votes#tab-top
# https://github.com/adafruit/Adafruit_Python_SSD1306

import sys
import time
import datetime
from subprocess import check_output         # Импортируем библиотеку по работе с внешними процессами
from re import findall                      # Импортируем библиотеку по работе с регулярными выражениями
import os
from datetime import timedelta

import lgpio

#===========================================================
import signal
import time
import datetime

is_shutdown = False

def stop(sig, frame):
    #global i2c
    #gpio.i2c_close(i2c)
    print(f"SIGTERM at {datetime.datetime.now()}")
    global is_shutdown
    is_shutdown = True

def ignore(sig, frame):
    print(f"SIGHUP at {datetime.datetime.now()}")

signal.signal(signal.SIGTERM, stop)
#signal.signal(signal.SIGHUP, ignore)
signal.signal(signal.SIGHUP, stop)

print(f"\n=================================================")
print(f"\nSTART at {datetime.datetime.now()}")
#===========================================================

I2C_RTC  = 0x51 # I2C device address

I2C_LCD  = 0x27 # I2C device address
LCD_WIDTH = 20   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

LCD_BACKLIGHT  = 0x08  # On 0X08 / Off 0x00

ENABLE = 0b00000100 # Enable bit

E_DELAY=0.0005
E_PULSE=0.0005

def run_cmd(cmd):
    return check_output(cmd, shell=True).decode('utf-8')

#Запрос IP-адреса
def get_my_ipwlan():
    val = run_cmd(["hostname -I | cut -d\' \' -f1 | head --bytes -1"])
    if val == "":
      val = "No connection!"
    return val

#Запрос загрузки CPU
def get_cpusage():
    cpu = run_cmd(["top -bn1 | grep load | awk '{printf \" %.2f\", $(NF-2)}'"])
    return(cpu)

#Запрос загрузки RAM
def get_memusage():
    ram = run_cmd ("free -m | awk 'NR==2{print $3\"MB/\"$2\"MB\"}'")
    return(ram)

#Запрос памяти SD-карты
def get_checkmem():
    mem = run_cmd("df -B100000000 | grep /dev/root | awk '{print $3/10\"/\"$2/10\"GB\", $5}'")
    return (mem)

#Запрос памяти HDD
def get_checkhdd():
    hdd = run_cmd ("df -BMB | grep /mnt/*** | awk '{print $2\"/\"$3, $5}'")
    return (hdd)

#Запрос Uptime
#def get_uptime():
#    uptime = run_cmd ("uptime | awk 'NR==1{print $3}'")
#    return (uptime)
def get_sysuptime():
    with open('/proc/uptime', 'r') as f:
      uptime_seconds = float(f.readline().split()[0])
      uptime_string = str(timedelta(seconds = uptime_seconds))
      sysuptime = uptime_string
    return sysuptime

#Запрос температуры CPU
def get_temp():
    temp = check_output(["vcgencmd","measure_temp"]).decode()    # Выполняем запрос температуры
    temp = float(findall('\d+\.\d+', temp)[0])                   # Извлекаем при помощи регулярного выражения значение температуры из строки "temp=47.8'C"
    return(temp)                                                 # Возвращаем результат

#Запрос темперауры с датчика DS18B20
def get_dallas():
    tfile=open("/sys/bus/w1/devices/28-0317249ce7ff/w1_slave")
    ttext=tfile.read()
    tfile.close()
    temp=ttext.split("\n")[1].split(" ")[9]
    temperature=float(temp[2:])/1000
    return temperature


def lcd_init(i2c):
    lcd_byte(i2c, 0x33,LCD_CMD) # 110011 initialization
    lcd_byte(i2c, 0x32,LCD_CMD) # 110010 initialization
    lcd_byte(i2c, 0x06,LCD_CMD) # 000110 Increment cursor to the right
    lcd_byte(i2c, 0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(i2c, 0x28,LCD_CMD) # 101000 Data length, number of lines, font size
    lcd_byte(i2c, 0x01,LCD_CMD) # 000001 Clear Device Screen
    time.sleep(E_DELAY)

def lcd_byte(i2c, bits, mode):
  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  lgpio.i2c_write_byte(i2c, bits_high)
  #lcd_toggle_enable(bits_high)
  time.sleep(E_DELAY)
  lgpio.i2c_write_byte(i2c, (bits_high | ENABLE))
  time.sleep(E_PULSE)
  lgpio.i2c_write_byte(i2c, (bits_high & ~ENABLE))
  time.sleep(E_DELAY)

  lgpio.i2c_write_byte(i2c, bits_low)
  #lcd_toggle_enable(bits_low)
  time.sleep(E_DELAY)
  lgpio.i2c_write_byte(i2c, (bits_low | ENABLE))
  time.sleep(E_PULSE)
  lgpio.i2c_write_byte(i2c, (bits_low & ~ENABLE))
  time.sleep(E_DELAY)

def lcd_string(i2c, message, line):

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(i2c, line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(i2c, ord(message[i]), LCD_CHR)



def main(i2c2):
  i2c_lcd = i2c2[0]
  i2c_rtc = i2c2[1]
  lcd_init(i2c_lcd)
  while not is_shutdown:
    now = datetime.datetime.now()

    lcd_string(i2c_lcd, "IP:{}".format(get_my_ipwlan()),LCD_LINE_1) #IP-адрес
    lcd_string(i2c_lcd, "RAM:{}".format(get_memusage()),LCD_LINE_2) #Использование RAM
    time.sleep(2)

    try:
      r=lgpio.i2c_read_device(i2c_rtc,1)
      lcd_string(i2c_lcd, "RTC: {}".format(r), LCD_LINE_2)
      print("RTC: ",r)
    except:
      lcd_string(i2c_lcd, "RTC None", LCD_LINE_2)
    time.sleep(2)

    lcd_string(i2c_lcd, "CPU Load:{}".format(get_cpusage()),LCD_LINE_2) #Время работы
    time.sleep(2)

    try:
      r=lgpio.i2c_read_device(i2c_rtc,1)
      lcd_string(i2c_lcd, "RTC: {}".format(r), LCD_LINE_2)
      print("RTC: ",r)
    except:
      lcd_string(i2c_lcd, "RTC None", LCD_LINE_2)
    time.sleep(2)

    lcd_string(i2c_lcd,  str(now.day)+'/'+str(now.month)+'/'+str(now.year)+' '+str(now.hour)+':'+str(now.minute),LCD_LINE_2) #Время и дата
    time.sleep(2)

    try:
      r=lgpio.i2c_read_device(i2c_rtc,1)
      lcd_string(i2c_lcd, "RTC: {}".format(r), LCD_LINE_2)
      print("RTC: ",r)
    except:
      lcd_string(i2c_lcd, "Read None", LCD_LINE_2)
    time.sleep(2)

if __name__ == '__main__':
  try:
    try:
      i2c_bus = 1   # 1 for LCD bus on CM4IO board
      i2c_lcd = lgpio.i2c_open(i2c_bus, I2C_LCD)
      time.sleep(0.1)
    except:
      time.sleep(0.1)
      i2c_bus = 10
      i2c_lcd = lgpio.i2c_open(i2c_bus, I2C_LCD)
      time.sleep(0.1)
    finally:
      print("BUS:{:02d} LCD ADDR:{:02X}".format(i2c_bus, I2C_LCD))

    try:
      i2c_rtc = lgpio.i2c_open(10, I2C_RTC) # 10 for RTC bus both on pump & CM4IO board
    except:
      i2c_rtc = -1

    main((i2c_lcd,i2c_rtc))
  except KeyboardInterrupt:
    pass
  finally:
    lcd_byte(i2c_lcd, 0x01, LCD_CMD)

