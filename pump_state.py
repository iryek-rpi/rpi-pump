import transitions
from transitions import *
from transitions.extensions import MachineFactory

import logging

from pump_screen import *
from pump_variables import PV
from pump_util import ThreadSafeSingleton
from pump_state_set_time import SetTimeStateMachine
from pump_state_set_level import SetLevelStateMachine
from pump_btn import buttons

logging.getLogger('transitions').setLevel(logging.WARNING)

#class LCDStateMachine(metaclass=ThreadSafeSingleton):
class LCDStateMachine():
  states = [
      { 'name':'ENTER-MAIN', 'on_enter':['enter_main'] }
    , { 'name':'IDLE-1', 'on_enter':['idle_1'] }
    , { 'name':'IDLE-2', 'on_enter':['idle_2'] }
    , { 'name':'IDLE-3', 'on_enter':['idle_3'] }
    , { 'name':'IDLE-4', 'on_enter':['idle_4'] }
    , { 'name':'SETTING-NEXT', 'on_enter':['setting_next'] }
    #, { 'name':'SETTING-TIME', 'on_enter':['setting_time'] }
  ]

  transitions = [
      { 'source':'*', 'trigger':'enter', 'dest':'ENTER-MAIN'}
    , { 'source':'ENTER-MAIN', 'trigger':'init', 'dest':'IDLE-1'}
    , { 'source':'*', 'trigger':'btn1_l', 'dest':'SETTING-NEXT'}
    , { 'source':'IDLE-1', 'trigger':'update_idle', 'dest':'IDLE-1'}
    , { 'source':'IDLE-2', 'trigger':'update_idle', 'dest':'IDLE-2'}
    , { 'source':'IDLE-3', 'trigger':'update_idle', 'dest':'IDLE-3'}
    , { 'source':'IDLE-4', 'trigger':'update_idle', 'dest':'IDLE-4'}
    , { 'source':'IDLE-1', 'trigger':'btn1_s', 'dest':'IDLE-2'}
    , { 'source':'IDLE-2', 'trigger':'btn1_s', 'dest':'IDLE-3'}
    , { 'source':'IDLE-3', 'trigger':'btn1_s', 'dest':'IDLE-4'}
    , { 'source':'IDLE-4', 'trigger':'btn1_s', 'dest':'IDLE-1'}
    #, { 'source':'SETTING', 'trigger':'btn1_l', 'dest':'IDLE-1'}
    #, { 'source':'SETTING', 'trigger':'btn1_s', 'dest':'SETTING-TIME'}
    #, { 'source':'SETTING-TIME', 'trigger':'btn1_l', 'dest':'IDLE-1'}
    #, { 'source':'SETTING-TIME', 'trigger':'btn1_s', 'dest':'SETTING'}
  ]

  def __init__(self, *args, **kwargs):
    self.name = kwargs.get('name')
    self.pv = kwargs.get('pv')
    self.sm_locked_cls = MachineFactory.get_predefined(locked=True)
    self.machine = self.sm_locked_cls(model=self, 
      states=LCDStateMachine.states, 
      transitions=LCDStateMachine.transitions,
      initial='IDLE-1',
      ignore_invalid_triggers=True)
    
    #self.sm_set_level = SetLevelMachine(name='SetLevelStateMachine', pv=self.pv)
    #self.sm_time = SetTimeStateMachine(name='SetTimeStateMachine', pv=self.pv)
    #self.sm_list = [self, self.set_level, self.sm_time]
    self.enter()

  def enter_main(self):
    self.init()

  def idle_1(self):
    self.pv.motor1 = 1
    self.pv.motor2 = 0 
    self.pv.motor3 = 1
    scr_idle_1(self.pv)

  def idle_2(self):
    self.pv.motor1 = 0 
    self.pv.motor2 = 1
    self.pv.motor3 = 1
    scr_idle_2(self.pv)

  def idle_3(self):
    self.pv.motor1 = 1 
    self.pv.motor2 = 1
    self.pv.motor3 = 0 
    scr_idle_3(self.pv)

  def idle_4(self):
    scr_idle_4(self.pv)

  def setting_next(self):
    sm=buttons().next_state()
    sm.enter()
    #self.sm_time.enter()
    
  #def setting_time(self):
  #  print("callback: setting_time")
  #  scr_setting_time(self.pv)
