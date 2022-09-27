#!/usr/bin/python3
# -*- coding: utf-8 -*-

import picologging as logging
import paho.mqtt.publish as publish
from paho import mqtt

from pump_variables import PV, pv
import pump_util as util
import config


logger = logging.getLogger(util.MAIN_LOGGER_NAME)

def mqtt_publish(topic, level, client):
  #client.publish.single(topic=topic, payload=level, hostname=broker)
  client.publish(topic=topic, payload=level)
  logger.info(f"mqtt topic:{topic} payload:{level}")
  #publish.multiple(msgs, hostname=host)

def mqtt_init(broker, port):
  client = mqtt.client.Client('pump_monitor')
  client.connect(broker, int(port))
  return client

#client = mqtt.Client("iot gateway 1")
#client.connect(broker, port)

#while True:
#    num = uniform(1,10)
#    client.publish("Iotgateway/MFMmeter", num)
#    print("just published" + str(num) + " to" + str(broker) +  "on topic EdgeGrid/Iotgateway/MFMmeter")
#    time.sleep(1)
