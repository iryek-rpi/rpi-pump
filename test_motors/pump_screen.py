import time
import datetime

import logging

import lgpio
from pump_lcd import lcd
import pump_variables
from pump_variables import PV
from pump_variables import SOURCE_SENSOR
from pump_variables import SOURCE_AI
from pump_util import get_time, get_my_ipwlan, list_to_number
from pump_btn import buttons
from pump_monitor import water_level_rate

#LCD_WIDTH = 20    # Maximum characters per line
LCD_WIDTH = 16  # Maximum characters per line
LCD_CHR = 1  # Mode - Sending data
LCD_CMD = 0  # Mode - Sending command
LCD_LINE_1 = 0x80  # LCD RAM address for line 1
LCD_LINE_2 = 0xC0  # LCD RAM address for line 2
L1 = 1  # LCD RAM address for the 1st line
L2 = 2  # LCD RAM address for the 2nd line
LCD_BACKLIGHT = 0x08  # On 0X08 / Off 0x00
ENABLE = 0b00000100  # Enable bit
E_DELAY = 0.0005
E_PULSE = 0.0005

#===================================================================
# 0123456789012345
#    Save Time?
#      Yes  No
#   Setting Time
# 2022/01/31 12:25
# 0123456789012345
#===================================================================
CURSOR_Y10 = 0xC0 + 2
CURSOR_Y01 = 0xC0 + 3
CURSOR_M10 = 0xC0 + 5
CURSOR_M01 = 0xC0 + 6
CURSOR_D10 = 0xC0 + 8
CURSOR_D01 = 0xC0 + 9
CURSOR_H10 = 0xC0 + 11
CURSOR_H01 = 0xC0 + 12
CURSOR_MIN10 = 0xC0 + 14
CURSOR_MIN01 = 0xC0 + 15

#===================================================================
# 0123456789012345
#  Set Water H/L
# High:00% Low:00%
# 0123456789012345
#===================================================================
CURSOR_LH10 = 0xC0 + 5
CURSOR_LH01 = 0xC0 + 6
CURSOR_LL10 = 0xC0 + 13
CURSOR_LL01 = 0xC0 + 14


def scr_idle_1(pv: pump_variables.PV):
  logging.debug("scr_idle_1:level:{}".format(pv.water_level))
  if pv.source == SOURCE_AI:
    s1 = f"PWL: "
  else:
    s1 = f"WL:  "

  if not pv.run_mode_out:
    s1 += " X "
  else:
    s1 += " O "

  if not pv.motor2_in:
    s1 += "X"
  else:
    s1 += "O"

  if not pv.motor1_in:
    s1 += "X"
  else:
    s1 += "O"

  if not pv.motor0_in:
    s1 += "X "
  else:
    s1 += "O "

  if not pv.motor2_out:
    s1 += "X"
  else:
    s1 += "O"

  if not pv.motor1_out:
    s1 += "X"
  else:
    s1 += "O"

  if not pv.motor0_out:
    s1 += "X"
  else:
    s1 += "O"

  rate = water_level_rate(pv)

  lcd().string(s1, L1)
  lcd().bar(rate, L2)


def scr_idle_2(pv):
  if pv.source == SOURCE_AI:
    s1 = f"AI PWL:{pv.water_level:.1f}"
  else:
    s1 = f"PLC WL:{pv.water_level:.1f}"

  mt1 = ""
  mt2 = ""
  mt3 = ""
  if pv.motor1 == 0:
    mt1 = "M1:-  "
  elif pv.motor1 > 0:
    mt1 = "M1:O  "

  if pv.motor2 == 0:
    mt2 = "M2:-  "
  elif pv.motor2 > 0:
    mt2 = "M2:O  "

  if pv.motor3 == 0:
    mt3 = "M3:-"
  elif pv.motor3 > 0:
    mt3 = "M3:O"

  s2 = f"{mt1}{mt2}{mt3}"
  #s2 = "2022/12/31 12:55"

  lcd().string(s1, L1)
  lcd().string(s2, L2)


def scr_idle_3(pv):
  if pv.source == SOURCE_AI:
    s1 = f"AI PWL:{pv.water_level:.1f} "
  else:
    s1 = f"PLC WL:{pv.water_level:.1f} "

  if pv.motor1 == 0:
    s1 += "X"
  elif pv.motor1 > 0:
    s1 += "O"

  if pv.motor2 == 0:
    s1 += "X"
  elif pv.motor2 > 0:
    s1 += "O"

  if pv.motor3 == 0:
    s1 += "X"
  elif pv.motor3 > 0:
    s1 += "O"

  s2 = get_time()

  lcd().string(s1, L1)
  lcd().string(s2, L2)


def scr_idle_4(pv):
  s1 = get_my_ipwlan()
  s2 = get_time()

  lcd().string(s1, L1)
  lcd().string(s2, L2)


'''
def scr_setting(pv):
  if pv.mode == MODE_AI:
    s1 = f"AI PWL:{pv.water_level:.1f}"
  else:
    s1 = f"PLC WL:{pv.water_level:.1f}"

  s2 = f"setting"

  lcd().string(s1, L1)
  lcd().string(s2, L2)
'''


#===================================================================
# 0123456789012345
#  Set Water H/L
# High:00% Low:00%
# 0123456789012345
#===================================================================
def scr_enter_set_level(pv):
  sm = buttons().statemachine()
  level = f"High:{list_to_number(sm.high):02d}% Low:{list_to_number(sm.low):02d}%"

  lcd().string(" Set Water H/L", L1)
  lcd().string(level, L2)


def scr_set_level_h10(pv):
  v = buttons().statemachine().high[0]
  p = CURSOR_LH10
  logging.debug(f"h10:{v}")
  lcd().cursor_pos(2, p)
  lcd().cursor_off()
  lcd().put_str(str(v))
  lcd().cursor_pos(2, p)


def scr_set_level_h01(pv):
  v = buttons().statemachine().high[1]
  p = CURSOR_LH01
  logging.debug(f"h01:{v}")
  lcd().cursor_pos(2, p)
  lcd().cursor_off()
  lcd().put_str(str(v))
  lcd().cursor_pos(2, p)


def scr_set_level_L10(pv):
  v = buttons().statemachine().low[0]
  p = CURSOR_LL10
  logging.debug(f"L10:{v}")
  lcd().cursor_pos(2, p)
  lcd().cursor_off()
  lcd().put_str(str(v))
  lcd().cursor_pos(2, p)


def scr_set_level_L01(pv):
  v = buttons().statemachine().low[1]
  p = CURSOR_LL01
  logging.debug(f"L01:{v}")
  lcd().cursor_pos(2, p)
  lcd().cursor_off()
  lcd().put_str(str(v))
  lcd().cursor_pos(2, p)


#===================================================================
# 0123456789012345
#    Save Time?
#      Yes  No
#   Setting Time
# 2022/01/31 12:25
# 0123456789012345
#===================================================================
def scr_enter_time_setting(pv):
  sm = buttons().statemachine()
  ct = f"{sm.y}/{sm.m:02d}/{sm.d:02d} {sm.h:02d}:{sm.min:02d}"

  lcd().string("  Setting Time", L1)
  lcd().string(ct, L2)


def scr_setting_save_or_not(pv):
  lcd().string("   Save Time?   ", L1)
  lcd().string("     Yes  No    ", L2)


def scr_settime_save(pv):
  pass


def scr_settime_y10(pv):
  y = buttons().statemachine().y
  y10 = (y // 10) % 100
  logging.debug(f"y:{y} y10:{y10}")  #" str(y10):",str(y10))
  lcd().cursor_pos(2, CURSOR_Y10)
  lcd().cursor_off()
  lcd().put_str(str(y10))
  lcd().cursor_pos(2, CURSOR_Y10)


def scr_settime_y01(pv):
  y = buttons().statemachine().y
  y01 = y % 10
  lcd().cursor_pos(2, CURSOR_Y01)
  lcd().cursor_off()
  lcd().put_str(str(y01))
  lcd().cursor_pos(2, CURSOR_Y01)


def scr_settime_m10(pv):
  lcd().cursor_pos(2, CURSOR_M10)


def scr_settime_m01(pv):
  m = buttons().statemachine().m
  lcd().cursor_off()
  lcd().cursor_pos(2, CURSOR_M01 - 1)
  lcd().cursor_off()
  lcd().put_str("{0:02d}".format(m))
  lcd().cursor_pos(2, CURSOR_M01)


def scr_settime_d10(pv):
  d = buttons().statemachine().d
  lcd().cursor_off()
  lcd().cursor_pos(2, CURSOR_D10)
  lcd().cursor_off()
  lcd().put_str("{0:02d}".format(d))
  lcd().cursor_pos(2, CURSOR_D10)


def scr_settime_d01(pv):
  d = buttons().statemachine().d
  lcd().cursor_off()
  lcd().cursor_pos(2, CURSOR_D01 - 1)
  lcd().cursor_off()
  lcd().put_str("{0:02d}".format(d))
  lcd().cursor_pos(2, CURSOR_D01)


def scr_settime_h10(pv):
  h = buttons().statemachine().h
  lcd().cursor_off()
  lcd().cursor_pos(2, CURSOR_H10)
  lcd().cursor_off()
  lcd().put_str("{0:02d}".format(h))
  lcd().cursor_pos(2, CURSOR_H10)


def scr_settime_h01(pv):
  h = buttons().statemachine().h
  lcd().cursor_off()
  lcd().cursor_pos(2, CURSOR_H01 - 1)
  lcd().cursor_off()
  lcd().put_str("{0:02d}".format(h))
  lcd().cursor_pos(2, CURSOR_H01)


def scr_settime_min10(pv):
  min = buttons().statemachine().min
  lcd().cursor_off()
  lcd().cursor_pos(2, CURSOR_MIN10)
  lcd().cursor_off()
  lcd().put_str("{0:02d}".format(min))
  lcd().cursor_pos(2, CURSOR_MIN10)


def scr_settime_min01(pv):
  min = buttons().statemachine().min
  lcd().cursor_off()
  lcd().cursor_pos(2, CURSOR_MIN01 - 1)
  lcd().cursor_off()
  lcd().put_str("{0:02d}".format(min))
  lcd().cursor_pos(2, CURSOR_MIN01)
