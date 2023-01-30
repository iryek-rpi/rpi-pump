import gpiozero
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Button
from time import sleep

#import picologging as logging
import logging

#from pump_lcd import lcd_string

import pump_util as util

logger = logging.getLogger(util.MAIN_LOGGER_NAME)

class PButton(Button):

  def __init__(self, pin=None, bounce_time=None, hold_time=1, sm=None):
    super().__init__(pin=pin, bounce_time=bounce_time, hold_time=hold_time)
    self.sm = sm
    self.held = False


B1 = 16
B2 = 20
B3 = 21

BOUNCE_TIME = 0.05  #50ms
HOLD_TIME = 1.5  # 500ms  # long press 시간


def buttons(inst=None):
  if inst != None:
    buttons.instance = inst
  return buttons.instance


buttons.instance = None


def held_1(d):
  logger.debug(f"B1 held:{d}")
  d.held = True
  d.sm.btn1_l()
  logger.debug(f"Button1 Held: state:{d.sm.state}")


def held_2(d):
  logger.debug(f"B2 held:{d}")
  d.held = True
  logger.debug(f"state:{d.sm.state}")


def held_3(d):
  logger.debug(f"B3 held:{d}")
  d.held = True
  logger.debug(f"state:{d.sm.state}")


def pressed_1(d):
  logger.debug(f"B1 pressed:{d}")
  d.held = False
  #d.sm.btn1_s()
  logger.debug(f"state:{d.sm.state}")


def released_1(d):
  if d.held == False:
    logger.debug(f"B1 released:{d}")
    d.sm.btn1_s()
    logger.debug(f"state:{d.sm.state}")
  else:
    d.held = False


def pressed_2(d):
  logger.debug(f"B2 pressed:{d}")
  d.held = False
  logger.debug(f"state:{d.sm.state}")


def released_2(d):
  if d.held == False:
    logger.debug(f"B2 released:{d}")
    d.sm.btn2_s()
    logger.debug(f"state:{d.sm.state}")
  else:
    d.held = False


def pressed_3(d):
  logger.debug(f"B3 pressed:{d}")
  d.held = False
  logger.debug(f"state:{d.sm.state}")


def released_3(d):
  if d.held == False:
    logger.debug(f"B3 released:{d}")
    logger.debug(f"state:{d.sm.state}")
    d.sm.btn3_s()
  else:
    d.held = False


class PumpButtons(object):

  def __init__(self, sm_list):
    self.current_sm = 0
    init_sm = sm_list[self.current_sm]
    self.sm_list = sm_list
    #self.previous_sm = init_sm

    self.b1 = PButton(pin=B1,
                      bounce_time=BOUNCE_TIME,
                      hold_time=HOLD_TIME,
                      sm=init_sm)
    self.b2 = PButton(pin=B2,
                      bounce_time=BOUNCE_TIME,
                      hold_time=HOLD_TIME,
                      sm=init_sm)
    self.b3 = PButton(pin=B3,
                      bounce_time=BOUNCE_TIME,
                      hold_time=HOLD_TIME,
                      sm=init_sm)

    self.b1.when_held = held_1
    self.b2.when_held = held_2
    self.b3.when_held = held_3

    self.b1.when_released = released_1
    self.b2.when_released = released_2
    self.b3.when_released = released_3

  def next_state(self):
    self.current_sm = (self.current_sm + 1) % len(self.sm_list)
    next_state = self.sm_list[self.current_sm]
    self.set_statemachine(next_state)
    return next_state

  def set_statemachine(self, new_sm):
    self.previous_sm = self.b1.sm
    logger.debug(f"new_sm:{new_sm}")
    logger.debug(f"b1:{self.b1}")
    self.b1.sm = new_sm
    self.b2.sm = new_sm
    self.b3.sm = new_sm

  def restore_statemachine(self):
    logger.debug(f"previous_sm:{self.previous_sm}")
    logger.debug(f"self.b1.sm:{self.b1.sm}")
    self.b1.sm = self.previous_sm
    self.previous_sm = self.b2.sm
    self.b2.sm = self.b1.sm
    self.b3.sm = self.b1.sm
    logger.debug(f"self.b1.sm:{self.b1.sm}")
    self.b1.sm.enter()

  def statemachine(self):
    return self.b1.sm