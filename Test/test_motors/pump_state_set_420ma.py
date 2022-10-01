from transitions import *
from transitions.extensions import MachineFactory

import calendar
import pexpect

import picologging as logging

from pump_screen import *
from pump_variables import PV
#from pump_util import ThreadSafeSingleton
from pump_btn import PumpButtons, buttons


#class SetTimeStateMachine(metaclass=ThreadSafeSingleton):
class SetSet420MAStateMachine():
  states = [{
      'name': 'ENTER_SET_LEVEL',
      'on_enter': ['enter_set_level']
  }, {
      'name': 'LEVEL_HIGH_4',
      'on_enter': ['high_4']
  }, {
      'name': 'LEVEL_HIGH_3',
      'on_enter': ['high_3']
  }, {
      'name': 'LEVEL_HIGH_2',
      'on_enter': ['high_2']
  }, {
      'name': 'LEVEL_HIGH_1',
      'on_enter': ['high_1']
  }, {
      'name': 'LEVEL_LOW_3',
      'on_enter': ['low_3']
  }, {
      'name': 'LEVEL_LOW_2',
      'on_enter': ['low_2']
  }, {
      'name': 'LEVEL_LOW_1',
      'on_enter': ['low_1']
  }, {
      'name': 'SAVE_LEVEL',
      'on_enter': ['save_level']
  }, {
      'name': 'DONT_SAVE_LEVEL',
      'on_enter': ['dont_save_level']
  }, {
      'name': 'LEAVE_SET_LEVEL',
      'on_enter': ['leave_set_level']
  }]

  transitions = [{
      'source': '*',
      'trigger': 'enter',
      'dest': 'ENTER_SET_LEVEL'
  }, {
      'source': 'ENTER_SET_LEVEL',
      'trigger': 'init',
      'dest': 'LEVEL_HIGH_4'
  }, {
      'source': 'LEVEL_HIGH_4',
      'trigger': 'btn1_s',
      'dest': 'LEVEL_HIGH_3'
  }, {
      'source': 'LEVEL_HIGH_3',
      'trigger': 'btn1_s',
      'dest': 'LEVEL_HIGH_2'
  }, {
      'source': 'LEVEL_HIGH_2',
      'trigger': 'btn1_s',
      'dest': 'LEVEL_HIGH_1'
  }, {
      'source': 'LEVEL_HIGH_1',
      'trigger': 'btn1_s',
      'dest': 'LEVEL_LOW_3'
  }, {
      'source': 'LEVEL_LOW_3',
      'trigger': 'btn1_s',
      'dest': 'LEVEL_LOW_2'
  }, {
      'source': 'LEVEL_LOW_2',
      'trigger': 'btn1_s',
      'dest': 'LEVEL_LOW_1'
  }, {
      'source': 'LEVEL_LOW_1',
      'trigger': 'btn1_s',
      'dest': 'LEVEL_HIGH_4'
  }, {
      'source': 'LEVEL_HIGH_4',
      'trigger': 'btn2_s',
      'dest': 'LEVEL_HIGH_4',
      'before': 'h_4_inc'
  }, {
      'source': 'LEVEL_HIGH_4',
      'trigger': 'btn3_s',
      'dest': 'LEVEL_HIGH_4',
      'before': 'h_4_dec'
  }, {
      'source': 'LEVEL_HIGH_3',
      'trigger': 'btn2_s',
      'dest': 'LEVEL_HIGH_3',
      'before': 'h_3_inc'
  }, {
      'source': 'LEVEL_HIGH_3',
      'trigger': 'btn3_s',
      'dest': 'LEVEL_HIGH_3',
      'before': 'h_3_dec'
  }, {
      'source': 'LEVEL_HIGH_2',
      'trigger': 'btn2_s',
      'dest': 'LEVEL_HIGH_2',
      'before': 'h_2_inc'
  }, {
      'source': 'LEVEL_HIGH_2',
      'trigger': 'btn3_s',
      'dest': 'LEVEL_HIGH_2',
      'before': 'h_2_dec'
  }, {
      'source': 'LEVEL_HIGH_1',
      'trigger': 'btn2_s',
      'dest': 'LEVEL_HIGH_1',
      'before': 'h_1_inc'
  }, {
      'source': 'LEVEL_HIGH_1',
      'trigger': 'btn3_s',
      'dest': 'LEVEL_HIGH_1',
      'before': 'h_1_dec'
  }, {
      'source': 'LEVEL_LOW_3',
      'trigger': 'btn2_s',
      'dest': 'LEVEL_LOW_3',
      'before': 'L_3_inc'
  }, {
      'source': 'LEVEL_LOW_3',
      'trigger': 'btn3_s',
      'dest': 'LEVEL_LOW_3',
      'before': 'L_3_dec'
  }, {
      'source': 'LEVEL_LOW_2',
      'trigger': 'btn2_s',
      'dest': 'LEVEL_LOW_2',
      'before': 'L_2_inc'
  }, {
      'source': 'LEVEL_LOW_2',
      'trigger': 'btn3_s',
      'dest': 'LEVEL_LOW_2',
      'before': 'L_2_dec'
  }, {
      'source': 'LEVEL_LOW_1',
      'trigger': 'btn2_s',
      'dest': 'LEVEL_LOW_1',
      'before': 'L_1_inc'
  }, {
      'source': 'LEVEL_LOW_1',
      'trigger': 'btn3_s',
      'dest': 'LEVEL_LOW_1',
      'before': 'L_1_dec'
  }, {
      'source': '*',
      'trigger': 'btn1_l',
      'dest': 'SAVE_OR_NOT'
  }, {
      'source': 'SAVE_OR_NOT',
      'trigger': 'btn2_s',
      'dest': 'SAVE_LEVEL'
  }, {
      'source': 'SAVE_OR_NOT',
      'trigger': 'btn3_s',
      'dest': 'DONT_SAVE_LEVEL'
  }, {
      'source': '*',
      'trigger': 'leave',
      'dest': 'LEAVE_SET_LEVEL'
  }]

  def __init__(self, *args, **kwargs):
    self.name = kwargs.get('name')
    self.pv = kwargs.get('pv')
    self.sm_locked_cls = MachineFactory.get_predefined(locked=True)
    self.machine = self.sm_locked_cls(
        model=self,
        #self.machine = Machine(model=self,
        states=Set420MAStateMachine.states,
        transitions=Set420MAStateMachine.transitions,
        initial='ENTER_SET_LEVEL',
        ignore_invalid_triggers=True)

    print("Set420MAStateMachine.__init__(pv:", self.pv)

    self.high_old = [0, 0, 0, 0]
    self.low_old = [0, 0, 0]

    self.high = [0, 0, 0, 0]
    self.low = [0, 0, 0]

  def enter_set_level(self):
    print("enter_set_level:", self)
    buttons().set_statemachine(self)
    self.high_old = [
        self.pv.setting_high // 1000, (self.pv.setting_high // 100) % 10,
        (self.pv.setting_high // 10) % 10, self.pv.setting_high % 10
    ]
    self.low_old = [
        self.pv.setting_low // 100, (self.pv.setting_low // 10) % 10,
        self.pv.setting_low % 10
    ]
    self.high = self.high_old.copy()
    self.low = self.low_old.copy()
    scr_enter_set_level(self.pv)
    self.init()

  def save_or_not(self):
    print("callback: save_or_not", self)
    if self.y_old != self.y or self.m_old != self.m or self.d_old != self.d or self.h_old != self.h or self.min_old != self.min:
      scr_setting_save_or_not(self.pv)
    else:
      self.leave()

  def save_time(self):
    ts = f"{self.m}/{self.d}/{self.y} {self.h}:{self.min}"
    print(f"callback: save_time:{ts}", self)
    c = pexpect.spawn(f"sudo /usr/bin/date --set='{ts}'")
    try:  # 현재 user id에 따라서 sudo password prompt가 안나올 수도 있음
      c.expect('password')
      c.sendline(self.pv.password)
      print(c.read())
    except:
      pass
    self.leave()

  def dont_save_time(self):
    print("callback: dont_save_time", self)
    self.leave()

  def leave_time_setting(self):
    print("callback: leave_time_setting", self)
    buttons().restore_statemachine()

  def check_leap(self):
    if self.m == 2 and self.d > 28:
      self.d = 29
      if calendar.isleap(self.y) == False:
        self.d = 28
        scr_settime_d01(self.pv)

  def check_date(self):
    if self.m == 2:
      self.check_leap()
    elif self.d == 31 and self.m in [4, 6, 9, 11]:
      self.d = 30
      scr_settime_d01(self.pv)

  def high_4(self):
    print("callback: high_4")
    scr_set_level_h4(self.pv)

  def high_3(self):
    print("callback: high_3")
    scr_set_level_h3(self.pv)

  def high_2(self):
    print("callback: high_2")
    scr_set_level_h2(self.pv)

  def high_1(self):
    print("callback: high_1")
    scr_set_level_h1(self.pv)

  def low_3(self):
    print("callback: low_3")
    scr_set_level_L3(self.pv)

  def low_2(self):
    print("callback: low_2")
    scr_set_level_L2(self.pv)

  def low_1(self):
    print("callback: low_1")
    scr_set_level_L1(self.pv)

  def adjust_list_digit(lst, idx, amount=1):
    lst[idx] = adjust_digit(lst[idx], idx, amount)

  def list_to_number(lst):
    return sum(d * 10**i for i, d in enumerate(lst[::-1]))

  def adjust_digit(v, amount=1):
    v = v + amount
    if v < 0:
      v = 9
    elif v > 9:
      v = 0

    return v

  def h_4_inc(self):
    self.high[0] = adjust_digit(self.high[0], 1)

  def h_3_inc(self):
    self.high[1] = adjust_digit(self.high[1], 1)

  def h_2_inc(self):
    self.high[2] = adjust_digit(self.high[2], 1)

  def h_1_inc(self):
    self.high[3] = adjust_digit(self.high[3], 1)

  def h_4_dec(self):
    self.high[0] = adjust_digit(self.high[0], -1)

  def h_3_dec(self):
    self.high[1] = adjust_digit(self.high[1], -1)

  def h_2_dec(self):
    self.high[2] = adjust_digit(self.high[2], -1)

  def h_1_dec(self):
    self.high[3] = adjust_digit(self.high[3], -1)

  def L_3_inc(self):
    self.low[0] = adjust_digit(self.low[0], 1)

  def L_2_inc(self):
    self.low[1] = adjust_digit(self.low[1], 1)

  def L_1_inc(self):
    self.low[2] = adjust_digit(self.low[2], 1)

  def L_3_dec(self):
    self.low[0] = adjust_digit(self.low[0], -1)

  def L_2_dec(self):
    self.low[1] = adjust_digit(self.low[1], -1)

  def L_1_dec(self):
    self.low[2] = adjust_digit(self.low[2], -1)
