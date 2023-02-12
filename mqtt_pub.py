#!/usr/bin/python3
# -*- coding: utf-8 -*-

#import picologging as logging
import logging
import paho.mqtt.publish as publish
from paho import mqtt

from pump_variables import PV, pv
import pump_util as util
import config
import constant

logger = util.make_logger(name=util.MQTT_LOGGER_NAME, filename=util.MQTT_LOGFILE_NAME, level=logging.INFO)

def mqtt_init(client_name, broker, port):
  client = mqtt.client.Client(client_name)
  client.connect(broker, int(port))
  return client

def mqtt_pub_proc(**kwargs):
  """mqtt publisher 프로세스
     'pipe_pub': pipe_mqtt_pub,
     'mqtt_broker': mqtt_broker,
     'mqtt_port': mqtt_port,
     'mqtt_client_name': mqtt_client_name,
     'mqtt_topic': mqtt_topic
    """
  _pipe = kwargs['pipe_pub']
  _broker = kwargs['mqtt_broker']
  _port = kwargs['mqtt_port']
  _client_name = kwargs['mqtt_client_name']
  _topic = kwargs['mqtt_topic']

  client = mqtt.client.Client(_client_name)
  logger.info(f"MQTT client:{_client_name}:{client}")
  r = None
  try:
    r = client.connect(_broker, int(_port))
    logger.info(f"MQTT connect() returns:{r}")
  except Exception:
    print("\nException creating a MQTT connection. Exiting MQTT Publisher\n")
    return

  while 1:
    (level_sensor, level_ai, setting_low, setting_high) = _pipe.recv()
    msg = f"{level_sensor} {level_ai} {setting_low} {setting_high}"
    client.publish(topic=_topic, payload=msg)
    logger.info(f"mqtt topic:{_topic} payload:{msg}")
