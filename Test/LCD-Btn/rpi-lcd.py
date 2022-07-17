#!/usr/bin/python
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

I2C_ADDR  = 0x27 # I2C device address
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



def main(i2c):
  lcd_init(i2c)
  while True:
    now = datetime.datetime.now()

    lcd_string(i2c, "IP:{}".format(get_my_ipwlan()),LCD_LINE_1) #IP-адрес
    lcd_string(i2c, "RAM:{}".format(get_memusage()),LCD_LINE_2) #Использование RAM
    time.sleep(5)
#    lcd_string("CPU Temp:{}".format(get_temp()),LCD_LINE_3) #Темп-ра CPU
#    lcd_string(i2c, "SDmem:{}".format(get_checkmem()),LCD_LINE_2) #Использование SD
#    time.sleep(5)

#    lcd_byte(i2c, 0x01, LCD_CMD)
#    lcd_string(i2c, "UP: {}".format(get_sysuptime()),LCD_LINE_1) #Время работы
    lcd_string(i2c, "CPU Load:{}".format(get_cpusage()),LCD_LINE_2) #Время работы
    time.sleep(3)
    #lcd_string("DS18B20 Temp:{}".format(get_dallas()),LCD_LINE_3) #Темп-ра с внешнего датчика
    lcd_string(i2c,  str(now.day)+'/'+str(now.month)+'/'+str(now.year)+' '+str(now.hour)+':'+str(now.minute),LCD_LINE_2) #Время и дата
    time.sleep(3)

if __name__ == '__main__':
  try:
    i2c = lgpio.i2c_open(1, I2C_ADDR)
    chip0 = lgpio.gpiochip_open(0)
    main(i2c)
  except KeyboardInterrupt:
    pass
  finally:
    lcd_byte(i2c, 0x01, LCD_CMD)
