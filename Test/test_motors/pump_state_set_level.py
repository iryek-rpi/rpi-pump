import transitions
from transitions import *
from transitions.extensions import MachineFactory

import picologging as logging

import calendar
import pexpect

from pump_screen import *
from pump_variables import PV
from pump_util import list_to_number, change_digit
from pump_btn import PumpButtons, buttons
import config

FORMAT = ("%(asctime)-15s %(threadName)-15s"
          " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s")
logging.basicConfig(
    #format='%(asctime)s %(threadName) %(levelname)s:%(filename)s:%(message)s',
    format=FORMAT,
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()


#class SetTimeStateMachine(metaclass=ThreadSafeSingleton):
class SetLevelStateMachine():
  states = [
      {
          'name': 'ENTER-SET-LEVEL',
          'on_enter': ['enter_set_level']
      }, {
          'name': 'LEVEL-HIGH-010',
          'on_enter': ['high_2']
      }, {
          'name': 'LEVEL-HIGH-01',
          'on_enter': ['high_1']
      }, {
          'name': 'LEVEL-LOW-010',
          'on_enter': ['low_2']
      }, {
          'name': 'LEVEL-LOW-01',
          'on_enter': ['low_1']
      }, {
          'name': 'SETTING-NEXT',
          'on_enter': ['setting_next']
      }
      #, { 'name':'SAVE_LEVEL', 'on_enter':['save_level'] }
      #, { 'name':'DONT_SAVE_LEVEL', 'on_enter':['dont_save_level'] }
      #, { 'name':'LEAVE_SET_LEVEL', 'on_enter':['leave_set_level'] }
  ]

  transitions = [
      {
          'source': '*',
          'trigger': 'enter',
          'dest': 'ENTER-SET-LEVEL'
      },
      {
          'source': 'ENTER-SET-LEVEL',
          'trigger': 'init',
          'dest': 'LEVEL-HIGH-010'
      },
      {
          'source': '*',
          'trigger': 'btn1_l',
          'dest': 'SETTING-NEXT'
      }
      #, { 'source':'*', 'trigger':'leave', 'dest':'LEAVE_SET_LEVEL'}
      ,
      {
          'source': 'LEVEL-HIGH-010',
          'trigger': 'btn1_s',
          'dest': 'LEVEL-HIGH-01'
      },
      {
          'source': 'LEVEL-HIGH-01',
          'trigger': 'btn1_s',
          'dest': 'LEVEL-LOW-010'
      },
      {
          'source': 'LEVEL-LOW-010',
          'trigger': 'btn1_s',
          'dest': 'LEVEL-LOW-01'
      },
      {
          'source': 'LEVEL-LOW-01',
          'trigger': 'btn1_s',
          'dest': 'LEVEL-HIGH-010'
      },
      {
          'source': 'LEVEL-HIGH-010',
          'trigger': 'btn2_s',
          'dest': 'LEVEL-HIGH-010',
          'before': 'h10_inc'
      },
      {
          'source': 'LEVEL-HIGH-010',
          'trigger': 'btn3_s',
          'dest': 'LEVEL-HIGH-010',
          'before': 'h10_dec'
      },
      {
          'source': 'LEVEL-HIGH-01',
          'trigger': 'btn2_s',
          'dest': 'LEVEL-HIGH-01',
          'before': 'h01_inc'
      },
      {
          'source': 'LEVEL-HIGH-01',
          'trigger': 'btn3_s',
          'dest': 'LEVEL-HIGH-01',
          'before': 'h01_dec'
      },
      {
          'source': 'LEVEL-LOW-010',
          'trigger': 'btn2_s',
          'dest': 'LEVEL-LOW-010',
          'before': 'L10_inc'
      },
      {
          'source': 'LEVEL-LOW-010',
          'trigger': 'btn3_s',
          'dest': 'LEVEL-LOW-010',
          'before': 'L10_dec'
      },
      {
          'source': 'LEVEL-LOW-01',
          'trigger': 'btn2_s',
          'dest': 'LEVEL-LOW-01',
          'before': 'L01_inc'
      },
      {
          'source': 'LEVEL-LOW-01',
          'trigger': 'btn3_s',
          'dest': 'LEVEL-LOW-01',
          'before': 'L01_dec'
      }

      #, { 'source':'*', 'trigger':'btn1_l', 'dest':'SAVE_OR_NOT'}
      #, { 'source':'SAVE_OR_NOT', 'trigger':'btn2_s', 'dest':'SAVE_LEVEL'}
      #, { 'source':'SAVE_OR_NOT', 'trigger':'btn3_s', 'dest':'DONT_SAVE_LEVEL'}
  ]

  def __init__(self, *args, **kwargs):
    self.name = kwargs.get('name')
    self.pv: PV = kwargs.get('pv')
    self.sm_locked_cls = MachineFactory.get_predefined(locked=True)
    self.machine = self.sm_locked_cls(
        model=self,
        #self.machine = Machine(model=self,
        states=SetLevelStateMachine.states,
        transitions=SetLevelStateMachine.transitions,
        initial='ENTER_SET_LEVEL',
        ignore_invalid_triggers=True)

    self.high_old = [0, 0]
    self.low_old = [0, 0]

    self.high = [0, 0]
    self.low = [0, 0]

  def enter_set_level(self):
    logger.debug(f"enter_set_level:{self}")
    #buttons().set_statemachine(self)
    self.high_old = [(self.pv.setting_high // 10) % 10,
                     self.pv.setting_high % 10]
    self.low_old = [(self.pv.setting_low // 10) % 10, self.pv.setting_low % 10]
    self.high = self.high_old.copy()
    self.low = self.low_old.copy()
    scr_enter_set_level(self.pv)
    self.init()

  def setting_next(self):
    self.pv.setting_high = list_to_number(self.high)
    config.update_config('CONTROLLER', 'AUTO_H', self.pv.setting_high)
    self.pv.setting_low = list_to_number(self.low)
    config.update_config('CONTROLLER', 'AUTO_L', self.pv.setting_low)
    sm = buttons().next_state()
    sm.enter()

  def save_or_not(self):
    if (self.high_old != self.high) or (self.low_old != self.low):
      scr_setting_save_or_not(self.pv)
    else:
      self.leave()

  def save_level(self):
    self.leave()

  def dont_save_level(self):
    self.leave()

  def leave_set_level(self):
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

  def high_2(self):
    scr_set_level_h10(self.pv)

  def high_1(self):
    scr_set_level_h01(self.pv)

  def low_2(self):
    scr_set_level_L10(self.pv)

  def low_1(self):
    scr_set_level_L01(self.pv)

  def h10_inc(self):
    self.high[0] = change_digit(self.high[0], 1)

  def h01_inc(self):
    self.high[1] = change_digit(self.high[1], 1)

  def h10_dec(self):
    self.high[0] = change_digit(self.high[0], -1)

  def h01_dec(self):
    self.high[1] = change_digit(self.high[1], -1)

  def L10_inc(self):
    self.low[0] = change_digit(self.low[0], 1)

  def L01_inc(self):
    self.low[1] = change_digit(self.low[1], 1)

  def L10_dec(self):
    self.low[0] = change_digit(self.low[0], -1)

  def L01_dec(self):
    self.low[1] = change_digit(self.low[1], -1)
