'''
https://github.com/iryek-rpi/pi-fan-controller/blob/master/fancontrol.py
'''
import time
import os
import signal

import pump_util as util

from gpiozero import OutputDevice

ON_THRESHOLD = 60
OFF_THRESHOLD = 50 

SLEEP_INTERVAL = 20  # (seconds) How often we check the core temperature.

GPIO_PIN=12

is_shutdown = False

def ctrl_c_handler(sig, frame):
  print(f"fan_proc: SIGINT at {datetime.datetime.now()}")
  print('fan_proc: You pressed Ctrl+C! in fan_proc')
  print(f"fan_proc: frame:{frame}")
  global is_shutdown
  is_shutdown=True

def stop(sig, frame):
  print(f"fan_proc: SIGTERM at {datetime.datetime.now()}")
  print(f"fan_proc: frame:{frame}")
  global is_shutdown
  is_shutdown = True

def ignore(sig, frame):
  print(f"fan_proc: SIGHUP at {datetime.datetime.now()}")
  print(f"fan_proc: frame:{frame}")

#signal.signal(signal.SIGTERM, stop)
#signal.signal(signal.SIGINT, ctrl_c_handler)
#signal.signal(signal.SIGHUP, ignore)

def get_temp():
    #with open('/sys/class/thermal/thermal_zone0/temp') as f:
    with open('/sys/devices/virtual/thermal/thermal_zone0/temp') as f:
        temp_str = f.read()

    try:
        return int(temp_str) / 1000
    except (IndexError, ValueError,) as e:
        raise RuntimeError('Could not parse temperature output.') from e

def fan_proc(**kwargs):
    logger = util.make_logger(name=util.FAN_LOGGER_NAME, filename=util.FAN_LOGFILE_NAME)
    #logger = kwargs['fan_logger']

    logger.info(f"############## fan_proc: {os.getpid()}")
    global is_shutdown 
    
    fan = OutputDevice(GPIO_PIN)

    fan.on()
    time.sleep(5)

    while not is_shutdown:
        temp = get_temp()

        if temp > ON_THRESHOLD and not fan.value:
            logger.info(f"Temperature: {temp} Turn On the Fan")
            fan.on()
        elif fan.value and temp<OFF_THRESHOLD:
            logger.info(f"Temperature: {temp} Turn Off the Fan")
            fan.off()
        else:
            logger.info(f"Temperature: {temp} Continue Fan State")
          

        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    fan_proc()
