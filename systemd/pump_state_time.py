from transitions import *
from transitions.extensions import MachineFactory

import calendar
import pexpect

from pump_screen import *
from pump_variables import PV
from pump_util import ThreadSafeSingleton
from pump_btn import PumpButtons, buttons

#class SetTimeStateMachine(metaclass=ThreadSafeSingleton):
class SetTimeStateMachine():
  states = [
    { 'name':'ENTER_TIME_SETTING', 'on_enter':['enter_time_setting'] }
    , { 'name':'YEAR10', 'on_enter':['year10'] }
    , { 'name':'YEAR01', 'on_enter':['year01'] }
    , { 'name':'MONTH10', 'on_enter':['month10'] }
    , { 'name':'MONTH01', 'on_enter':['month01'] }
    , { 'name':'DAY10', 'on_enter':['day10'] }
    , { 'name':'DAY01', 'on_enter':['day01'] }
    , { 'name':'HOUR10', 'on_enter':['hour10'] }
    , { 'name':'HOUR01', 'on_enter':['hour01'] }
    , { 'name':'MIN10', 'on_enter':['min10'] }
    , { 'name':'MIN01', 'on_enter':['min01'] }
    , { 'name':'SAVE_OR_NOT', 'on_enter':['save_or_not'] }
    , { 'name':'SAVE_TIME', 'on_enter':['save_time'] }
    , { 'name':'DONT_SAVE_TIME', 'on_enter':['dont_save_time'] }
    , { 'name':'LEAVE_TIME_SETTING', 'on_enter':['leave_time_setting'] }
  ]

  transitions = [
    { 'source':'*', 'trigger':'enter', 'dest':'ENTER_TIME_SETTING'}
    , { 'source':'ENTER_TIME_SETTING', 'trigger':'init', 'dest':'YEAR10'}
    , { 'source':'YEAR10', 'trigger':'btn1_s', 'dest':'YEAR01'}
    #, { 'source':'YEAR01', 'trigger':'btn1_s', 'dest':'MONTH10'}
    , { 'source':'YEAR01', 'trigger':'btn1_s', 'dest':'MONTH01', 'before':'check_leap'}
    , { 'source':'MONTH10', 'trigger':'btn1_s', 'dest':'MONTH01'}
    , { 'source':'MONTH01', 'trigger':'btn1_s', 'dest':'DAY10', 'before':'check_date'}
    , { 'source':'DAY10', 'trigger':'btn1_s', 'dest':'DAY01'}
    , { 'source':'DAY01', 'trigger':'btn1_s', 'dest':'HOUR10'}
    , { 'source':'HOUR10', 'trigger':'btn1_s', 'dest':'HOUR01'}
    , { 'source':'HOUR01', 'trigger':'btn1_s', 'dest':'MIN10'}
    , { 'source':'MIN10', 'trigger':'btn1_s', 'dest':'MIN01'}
    , { 'source':'MIN01', 'trigger':'btn1_s', 'dest':'YEAR10'}

    , { 'source':'YEAR10', 'trigger':'btn2_s', 'dest':'YEAR10', 'before':'y10_inc'}
    , { 'source':'YEAR10', 'trigger':'btn3_s', 'dest':'YEAR10', 'before':'y10_dec'}
    , { 'source':'YEAR01', 'trigger':'btn2_s', 'dest':'YEAR01', 'before':'y01_inc'}
    , { 'source':'YEAR01', 'trigger':'btn3_s', 'dest':'YEAR01', 'before':'y01_dec'}
    , { 'source':'MONTH10', 'trigger':'btn2_s', 'dest':'MONTH10', 'before':'m10_inc'}
    , { 'source':'MONTH10', 'trigger':'btn3_s', 'dest':'MONTH10', 'before':'m10_dec'}
    , { 'source':'MONTH01', 'trigger':'btn2_s', 'dest':'MONTH01', 'before':'m01_inc'}
    , { 'source':'MONTH01', 'trigger':'btn3_s', 'dest':'MONTH01', 'before':'m01_dec'}
    , { 'source':'DAY10', 'trigger':'btn2_s', 'dest':'DAY10', 'before':'d10_inc'}
    , { 'source':'DAY10', 'trigger':'btn3_s', 'dest':'DAY10', 'before':'d10_dec'}
    , { 'source':'DAY01', 'trigger':'btn2_s', 'dest':'DAY01', 'before':'d01_inc'}
    , { 'source':'DAY01', 'trigger':'btn3_s', 'dest':'DAY01', 'before':'d01_dec'}
    , { 'source':'HOUR10', 'trigger':'btn2_s', 'dest':'HOUR10', 'before':'h10_inc'}
    , { 'source':'HOUR10', 'trigger':'btn3_s', 'dest':'HOUR10', 'before':'h10_dec'}
    , { 'source':'HOUR01', 'trigger':'btn2_s', 'dest':'HOUR01', 'before':'h01_inc'}
    , { 'source':'HOUR01', 'trigger':'btn3_s', 'dest':'HOUR01', 'before':'h01_dec'}
    , { 'source':'MIN10', 'trigger':'btn2_s', 'dest':'MIN10', 'before':'min10_inc'}
    , { 'source':'MIN10', 'trigger':'btn3_s', 'dest':'MIN10', 'before':'min10_dec'}
    , { 'source':'MIN01', 'trigger':'btn2_s', 'dest':'MIN01', 'before':'min01_inc'}
    , { 'source':'MIN01', 'trigger':'btn3_s', 'dest':'MIN01', 'before':'min01_dec'}

    , { 'source':'*', 'trigger':'btn1_l', 'dest':'SAVE_OR_NOT'}
    , { 'source':'SAVE_OR_NOT', 'trigger':'btn2_s', 'dest':'SAVE_TIME'}
    , { 'source':'SAVE_OR_NOT', 'trigger':'btn3_s', 'dest':'DONT_SAVE_TIME'}
    , { 'source':'*', 'trigger':'leave', 'dest':'LEAVE_TIME_SETTING'}
  ]

  def __init__(self, *args, **kwargs):
    self.name = kwargs.get('name')
    self.pv = kwargs.get('pv')
    self.sm_locked_cls = MachineFactory.get_predefined(locked=True)
    self.machine = self.sm_locked_cls(model=self, 
    #self.machine = Machine(model=self, 
      states=SetTimeStateMachine.states, 
      transitions=SetTimeStateMachine.transitions,
      initial='ENTER_TIME_SETTING',
      ignore_invalid_triggers=True)

    print("SetTimeStateMachine.__init__(pv:",self.pv)

    self.y_old = 0
    self.m_old = 0
    self.d_old = 0
    self.h_old = 0
    self.min_old = 0

    self.y = 0
    self.m = 0
    self.d = 0
    self.h = 0
    self.min = 0

  def enter_time_setting(self):
    print("enter_time_setting:",self)
    buttons().set_statemachine(self)
    now = datetime.datetime.now()
    #ct = f"{now.year}/{now.month}/{now.day} {now.hour}:{now.minute:02d}" 
    self.y_old = now.year
    self.m_old = now.month
    self.d_old = now.day
    self.h_old = now.hour
    self.min_old = now.minute

    self.y = now.year
    self.m = now.month
    self.d = now.day
    self.h = now.hour
    self.min = now.minute
    scr_enter_time_setting(self.pv)
    self.init()

  def save_or_not(self):
    print("callback: save_or_not", self)
    if self.y_old!=self.y or self.m_old!=self.m or self.d_old!=self.d or self.h_old!=self.h or self.min_old!=self.min:
      scr_setting_save_or_not(self.pv)
    else:
      self.leave()

  def save_time(self):
    ts = f"{self.m}/{self.d}/{self.y} {self.h}:{self.min}"
    print(f"callback: save_time:{ts}",self)
    c = pexpect.spawn(f"sudo /usr/bin/date --set='{ts}'")
    try:  # 현재 user id에 따라서 sudo password prompt가 안나올 수도 있음
      c.expect('password')
      c.sendline('rudakwkd')
      print(c.read())
    except:
      pass
    self.leave()

  def dont_save_time(self):
    print("callback: dont_save_time",self)
    self.leave()

  def leave_time_setting(self):
    print("callback: leave_time_setting",self)
    buttons().restore_statemachine()

  def check_leap(self):
    if self.m==2 and self.d>28:
      self.d=29
      if calendar.isleap(self.y)==False:
        self.d=28
        scr_settime_d01(self.pv)

  def check_date(self):
    if self.m==2:
      self.check_leap()
    elif self.d==31 and self.m in [4,6,9,11]:
        self.d=30
        scr_settime_d01(self.pv)

  def year10(self):
    print("callback: year10")
    scr_settime_y10(self.pv)

  def year01(self):
    print("callback: year01")
    scr_settime_y01(self.pv)

  def month10(self):
    print("callback: month10")
    scr_settime_m10(self.pv)

  def month01(self):
    print("callback: month01")
    scr_settime_m01(self.pv)
    
  def day10(self):
    print("callback: day10")
    scr_settime_d10(self.pv)

  def day01(self):
    print("callback: day01")
    scr_settime_d01(self.pv)

  def hour10(self):
    print("callback: hour10")
    scr_settime_h10(self.pv)

  def hour01(self):
    print("callback: hour01")
    scr_settime_h01(self.pv)

  def min10(self):
    print("callback: min10")
    scr_settime_min10(self.pv)

  def min01(self):
    print("callback: min01")
    scr_settime_min01(self.pv)

  def y10_inc(self):
    print("before inc: year10->year10")
    temp = (self.y//10)%100
    temp += 1
    if temp==10:
        temp=2
    self.y = ((((self.y//100)*10)+temp)*10)+(self.y%10)

  def y10_dec(self):
    print("before dec: year10->year10")
    temp = (self.y//10)%100
    temp -= 1
    if temp==1:
        temp=9
    self.y = ((((self.y//100)*10)+temp)*10)+(self.y%10)

  def y01_inc(self):
    print("before inc: year01->year01")
    temp = self.y%10
    temp += 1
    if self.y<2030:
      if temp==10:
        temp=2
    else:
      if temp==10:
        temp=0

    self.y = ((self.y//10)*10)+temp

  def y01_dec(self):
    print("before dec: year01->year01")
    temp = self.y%10
    temp -= 1
    if self.y<2030:
      if temp==1:
        temp=9
    else:
      if temp==-1:
        temp=9

    self.y = ((self.y//10)*10)+temp

  def m10_inc(self):
    print("before inc: month10->month10")
    temp = self.m//10
    temp += 1
    if temp>1:
        temp=0
    
    self.m = temp*10+self.m%10

  def m10_dec(self):
    print("before dec: year10->year10")
    temp = (self.y//10)%100
    temp -= 1
    if temp==1:
        temp=9
    self.y = ((((self.y//100)*10)+temp)*10)+(self.y%10)

  def m01_inc(self):
    print("before inc: month01->month01")
    if self.m>11:
      self.m = 1
    else:
      self.m += 1

  def m01_dec(self):
    print("before dec: month01->month01")
    if self.m<2:
      self.m = 12
    else:
      self.m -= 1

  def d10_inc(self):
    print("before inc: day10->day10")
    if self.m==2:
      if self.d==19:
        if calendar.isleap(self.y)==False:
          self.d += 9 
        else:
          self.d += 10
      elif self.d==20:
        self.d = 1
      elif self.d<19:
        self.d += 10
      else:
        self.d -= 20
    elif self.m in [4,6,9,11]:
      if self.d>29:
        self.d = 1
      elif self.d>20:
        self.d -= 20
      else:
        self.d += 10
    else:
      if self.d>30:
        self.d = 1
      elif self.d>21:
        self.d -= 20
      else:
        self.d += 10

  def d10_dec(self):
    print("before dec: day10->day10")
    if self.m==2:
      if self.d==9:
        if calendar.isleap(self.y)==False:
          self.d += 19 # 9 -> 28 
        else:
          self.d += 20 # 9 -> 29
      elif self.d==10:
        self.d = 1     # 10 -> 01
      elif self.d<10:
        self.d += 20   # 8 -> 28
      else:
        self.d -= 10   # 20 -> 10
    elif self.m in [4,6,9,11]:
      if self.d==10:
        self.d = 1
      elif self.d<10:
        self.d += 20  # 9 -> 29
      else:
        self.d -= 10  # 25 -> 15
    else:
      if self.d==10:
        self.d = 1
      elif self.d==1:
        self.d = 31
      elif self.d<10:
        self.d += 20  # 9 -> 29
      else:
        self.d -= 10  # 25 -> 15

  def d01_inc(self):
    print("before inc: day01->day01")
    if self.m==2:
      if self.d==28:
        if calendar.isleap(self.y)==False:
          self.d = 20 
        else:
          self.d = 29
      elif self.d==29:
        self.d = 20
      else:
        self.d = ((self.d//10)*10)+((self.d%10)+1)%10 
    elif self.m in [4,6,9,11]:
      if self.d==30:
        self.d = 30
      else:
        self.d = ((self.d//10)*10)+((self.d%10)+1)%10 
    else:
      if self.d==30:
        self.d = 30
      else:
        self.d = ((self.d//10)*10)+((self.d%10)+1)%10 

  def d01_dec(self):
    print("before dec: day01->day01")
    if self.m==2:
      if self.d==20:
        if calendar.isleap(self.y)==False:
          self.d = 28
        else:
          self.d = 29
      elif (self.d%10)==0: # 10
        self.d = self.d+9  # 10 -> 19
      elif self.d==1:
        self.d = 9
      else:
        self.d = ((self.d//10)*10)+(self.d%10)-1 
    elif self.m in [4,6,9,11]:
      if self.d==1:
        self.d = 9 
      elif self.d==30:
        self.d = 29
      elif (self.d%10)==0:
        self.d = (self.d//10)*10 + 9
      else:
        self.d = ((self.d//10)*10)+(self.d%10)-1 
    else:
      if self.d==1:
        self.d = 9 
      elif self.d==31:
        self.d = 30 
      elif self.d==30:
        self.d = 29
      elif (self.d%10)==0:
        self.d = (self.d//10)*10 + 9
      else:
        self.d = ((self.d//10)*10)+(self.d%10)-1 

  def h10_inc(self):
    print("before inc: hour10->hour10")

    modulo = 3

    temp = (((self.h//10)+1)%modulo)*10 + self.h%10
    if temp>23:
      temp = 23
    self.h = temp

  def h10_dec(self):
    print("before dec: hour10->hour10")
    if self.h//10 == 0:
      self.h += 20    # 1 -> 21
    else:
      self.h = (((self.h//10)-1)%3)*10 + self.h%10

  def h01_inc(self):
    print("before inc: hour01->hour01")

    temp = (self.h//10)*10 + ((self.h%10)+1)%10
    if temp > 23:
      temp = 23
    self.h = temp

  def h01_dec(self):
    print("before dec: hour10->hour10")
    if self.h%10 == 0:
      temp = (self.h//10)*10 + 9
      if temp>23:
        temp=23
      self.h = temp
    else:
      self.h = (self.h//10)*10 + (self.h%10)-1

  def min10_inc(self):
    print("before inc: min10->min10")

    modulo = 6 

    self.min = (((self.min//10)+1)%modulo)*10 + self.min%10

  def min10_dec(self):
    print("before dec: min10->min10")
    if self.min//10 == 0:
      self.min += 50    # 01 -> 51
    else:
      self.min = (((self.min//10)-1)%6)*10 + self.min%10

  def min01_inc(self):
    print("before inc: min01->min01")

    self.min = ((self.min//10)*10) + ((self.min%10)+1)%10

  def min01_dec(self):
    print("before dec: min01->min01")
    if self.min%10 == 0:
      self.min = (self.min//10)*10 + 9
    else:
      self.min = (self.min//10)*10 + (self.min%10)-1