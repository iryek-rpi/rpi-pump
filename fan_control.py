'''
https://github.com/iryek-rpi/pi-fan-controller/blob/master/fancontrol.py
'''
import time
import os

import pump_util as util

from gpiozero import OutputDevice

ON_THRESHOLD = 50
OFF_THRESHOLD = 48

SLEEP_INTERVAL = 5  # (seconds) How often we check the core temperature.

GPIO_PIN=12

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

    fan = OutputDevice(GPIO_PIN)

    fan.on()
    time.sleep(5)

    while True:
        temp = get_temp()

        if temp > ON_THRESHOLD and not fan.value:
            logger.info(f"Temperature: {temp} Turn On the Fan")
            fan.on()
            print("Fan On")
        elif fan.value and temp<OFF_THRESHOLD:
            logger.info(f"Temperature: {temp} Turn Off the Fan")
            fan.off()
            print("Fan Off")

        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    fan_proc()
