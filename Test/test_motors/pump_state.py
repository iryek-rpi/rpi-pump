import transitions
from transitions import *
from transitions.extensions import MachineFactory

import logging

from pump_screen import *
import pump_variables
from pump_variables import PV
#from pump_util import ThreadSafeSingleton
from pump_state_set_time import SetTimeStateMachine
from pump_state_set_level import SetLevelStateMachine
from pump_btn import buttons
import motors

logging.getLogger('transitions').setLevel(logging.DEBUG)


#class LCDStateMachine(metaclass=ThreadSafeSingleton):
class LCDStateMachine():
  states = [{
      'name': 'ENTER-MAIN',
      'on_enter': ['enter_main']
  }, {
      'name': 'IDLE-1',
      'on_enter': ['idle_1']
  }, {
      'name': 'IDLE-1-MOTOR',
      'on_enter': ['idle_1_motor']
  }, {
      'name': 'IDLE-2',
      'on_enter': ['idle_2']
  }, {
      'name': 'IDLE-3',
      'on_enter': ['idle_3']
  }, {
      'name': 'IDLE-4',
      'on_enter': ['idle_4']
  }, {
      'name': 'SETTING-NEXT',
      'on_enter': ['setting_next']
  }
            #, { 'name':'SETTING-TIME', 'on_enter':['setting_time'] }
           ]

  transitions = [
      {
          'source': '*',
          'trigger': 'enter',
          'dest': 'ENTER-MAIN'
      }, {
          'source': 'ENTER-MAIN',
          'trigger': 'init',
          'dest': 'IDLE-1'
      }, {
          'source': '*',
          'trigger': 'btn1_l',
          'dest': 'SETTING-NEXT'
      }, {
          'source': 'IDLE-1',
          'trigger': 'update_idle',
          'dest': 'IDLE-1'
      }, {
          'source': 'IDLE-1',
          'trigger': 'btn3_s',
          'dest': 'IDLE-1-MOTOR'
      }, {
          'source': 'IDLE-1-MOTOR',
          'trigger': 'exit_motor',
          'dest': 'IDLE-1'
      }, {
          'source': 'IDLE-2',
          'trigger': 'update_idle',
          'dest': 'IDLE-2'
      }, {
          'source': 'IDLE-3',
          'trigger': 'update_idle',
          'dest': 'IDLE-3'
      }, {
          'source': 'IDLE-4',
          'trigger': 'update_idle',
          'dest': 'IDLE-4'
      }, {
          'source': 'IDLE-1',
          'trigger': 'btn3_s',
          'dest': 'IDLE-1-MOTOR'
      }, {
          'source': 'IDLE-2',
          'trigger': 'btn1_s',
          'dest': 'IDLE-3'
      }, {
          'source': 'IDLE-3',
          'trigger': 'btn1_s',
          'dest': 'IDLE-4'
      }, {
          'source': 'IDLE-4',
          'trigger': 'btn1_s',
          'dest': 'IDLE-1'
      }, {
          'source': 'IDLE-1',
          'trigger': 'btn3_s',
          'dest': 'IDLE-1'
      }
      #, { 'source':'SETTING', 'trigger':'btn1_l', 'dest':'IDLE-1'}
      #, { 'source':'SETTING', 'trigger':'btn1_s', 'dest':'SETTING-TIME'}
      #, { 'source':'SETTING-TIME', 'trigger':'btn1_l', 'dest':'IDLE-1'}
      #, { 'source':'SETTING-TIME', 'trigger':'btn1_s', 'dest':'SETTING'}
  ]

  def __init__(self, *args, **kwargs):
    self.name = kwargs.get('name')
    self.pv: pump_variables.PV = kwargs.get('pv')
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
    scr_idle_1(self.pv)

  def idle_1_motor(self):
    m3, m2, m1 = motors.get_all_motors(self.pv.chip)
    self.pv.motor2_in = m3
    self.pv.motor1_in = m2
    self.pv.motor0_in = m1
    logger.info(f"{(m3,m2,m1)} = get_all_motors()")

    self.pv.motor_out_count = self.pv.motor_out_count + 1
    self.pv.motor_out_count = self.pv.motor_out_count % 8

    n1 = self.pv.motor_out_count % 2
    n2 = (self.pv.motor_out_count // 2) % 2
    n3 = ((self.pv.motor_out_count // 2) // 2) % 2
    motors.set_all_motors(self.pv.chip, (n3, n2, n1))
    self.pv.motor2_out = n3
    self.pv.motor1_out = n2
    self.pv.motor0_out = n1

    logger.info(f"set_all_motors({self.pv.motor_out_count} )")
    logger.info(f"set_all_motors({(n3,n2,n1)} )")

    if not self.pv.run_mode_out:
      self.pv.run_mode_out = 1
    else:
      self.pv.run_mode_out = 0

    motors.set_run_mode(self.pv.chip, self.pv.run_mode_out)
    self.exit_motor()

  def idle_2(self):
    scr_idle_2(self.pv)

  def idle_3(self):
    scr_idle_3(self.pv)

  def idle_4(self):
    scr_idle_4(self.pv)

  def setting_next(self):
    sm = buttons().next_state()
    sm.enter()
    #self.sm_time.enter()

  #def setting_time(self):
  #  print("callback: setting_time")
  #  scr_setting_time(self.pv)
