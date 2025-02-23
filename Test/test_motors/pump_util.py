#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://raspberrytips.nl/lcd-scherm-20x4-i2c-raspberry-pi/
# https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load?answertab=votes#tab-top
# https://github.com/adafruit/Adafruit_Python_SSD1306

import sys
from subprocess import check_output     
from re import findall            
import os
import datetime
from datetime import timedelta
import threading

import time
import datetime

def change_list_digit(lst, idx, amount=1):
  lst[idx] = change_digit(lst[idx], idx, amount)

def list_to_number(lst):
  return sum(d * 10**i for i, d in enumerate(lst[::-1]))

def change_digit(v, amount=1):
  v = v+amount
  if v<0:
    v = 9 
  elif v>9:
    v = 0

  return v

def get_time():
  now = datetime.datetime.now()
  return f"{now.year}/{now.month}/{now.day} {now.hour:02d}:{now.minute:02d}" 
  #lcd_string(i2c,  str(now.day)+'/'+str(now.month)+'/'+str(now.year)+' '+str(now.hour)+':'+str(now.minute),LCD_LINE_2) #Время и дата

def run_cmd(cmd):
  return check_output(cmd, shell=True).decode('utf-8')

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
#  uptime = run_cmd ("uptime | awk 'NR==1{print $3}'")
#  return (uptime)
def get_sysuptime():
  with open('/proc/uptime', 'r') as f:
    uptime_seconds = float(f.readline().split()[0])
    uptime_string = str(timedelta(seconds = uptime_seconds))
    sysuptime = uptime_string
  return sysuptime

#Запрос температуры CPU
def get_temp():
  temp = check_output(["vcgencmd","measure_temp"]).decode()  # Выполняем запрос температуры
  temp = float(findall('\d+\.\d+', temp)[0])           # Извлекаем при помощи регулярного выражения значение температуры из строки "temp=47.8'C"
  return(temp)                         # Возвращаем результат

#Запрос темперауры с датчика DS18B20
def get_dallas():
  tfile=open("/sys/bus/w1/devices/28-0317249ce7ff/w1_slave")
  ttext=tfile.read()
  tfile.close()
  temp=ttext.split("\n")[1].split(" ")[9]
  temperature=float(temp[2:])/1000
  return temperature

# Based on tornado.ioloop.IOLoop.instance() approach.
# See https://github.com/facebook/tornado
# Whole idea for this metaclass is taken from: https://stackoverflow.com/a/6798042/2402281
#class ThreadSafeSingleton(type):
#  _instances = {}
#  _singleton_lock = threading.Lock()
#
#  def __call__(cls, *args, **kwargs):
#    # double-checked locking pattern (https://en.wikipedia.org/wiki/Double-checked_locking)
#    if cls not in cls._instances:
#      with cls._singleton_lock:
#        if cls not in cls._instances:
#          cls._instances[cls] = super(ThreadSafeSingleton, cls).__call__(*args, **kwargs)
#    return cls._instances[cls]
