import logging
import multiprocessing as mp
import signal
import datetime
import os

#from paho import mqtt
import paho.mqtt.client as mqtt_client

#from multiprocessing.connection import Listener, Client
import threading, time, signal
from datetime import timedelta


class RThread(threading.Thread):

  def __init__(self, name, interval, execute, args=(), kwargs=None):
    threading.Thread.__init__(self)
    self.name = name
    self.daemon = False
    self.event_stopped = threading.Event()
    self.interval = timedelta(seconds=interval)
    self.execute = execute
    self.args = args
    self.kwargs = kwargs

  def stop(self):
    self.event_stopped.set()
    self.join()

  def run(self):
    print(
        f"Name: {mp.current_process().name} PID: {os.getpid()} thread name: {threading.current_thread().name}  id: {threading.get_ident()}"
    )
    while not self.event_stopped.wait(timeout=self.interval.total_seconds()):
      self.execute(*self.args, **self.kwargs)


th_count = 0


def mqtt_thread_func(**kwargs):
  pipe_mqtt_sensor = kwargs['pipe']

  global th_count

  #if pipe_mqtt_sensor.poll(timeout=1):
  #if pipe_mqtt_sensor.poll():
  #  pass

  print("Sensor")
  for i in range(200):
    #pipe_mqtt_sensor.send(th_count)
    print(f"before sending:{i+10}")
    r = pipe_mqtt_sensor.send(i + 10)
    th_count += 1
    if i % 10 == 0:
      print(f"sending {i} returns:{r}")

  print(
      f"Name: {mp.current_process().name} PID: {os.getpid()} thread name: {threading.current_thread().name}  id: {threading.get_ident()}"
  )


def mqtt_pub_proc(**kwargs):
  """mqtt publisher 프로세스
     'pipe_pub': pipe_mqtt_pub,
     'mqtt_broker': mqtt_broker,
     'mqtt_port': mqtt_port,
     'mqtt_client_name': mqtt_client_name,
     'mqtt_topic': mqtt_topic
    """
  pipe_pub = kwargs['pipe_pub']
  broker = kwargs['mqtt_broker']
  port = kwargs['mqtt_port']
  client_name = kwargs['mqtt_client_name']
  topic = kwargs['mqtt_topic']

  client = mqtt_client.Client(client_name)
  try:
    client.connect(broker, int(port))
  except Exception:
    print("\nException creating a MQTT connection\n")
    pass

  r = pipe_pub.recv()
  print(f"PUB received: {r}")
  while 1:
    continue
    print(
        f"Received:{r} Name: {mp.current_process().name} PID: {os.getpid()} thread name: {threading.current_thread().name}  id: {threading.get_ident()}"
    )
    r = pipe_pub.recv()


def main():
  try:
    count = 0
    print(
        f"count:{count} Name: {mp.current_process().name} PID: {os.getpid()} thread name: {threading.current_thread().name}  id: {threading.get_ident()}"
    )

    client = mqtt_client.Client('client1')
    r = 1
    try:
      r = client.connect('ubuntu1t.local', int(1883))
    except Exception:
      print("\nException creating a MQTT connection\n")

    print(f"\nconnect returns:{r}\n")

    pipe_mqtt_sensor, pipe_mqtt_pub = mp.Pipe()
    mqtt_thread = RThread(name="MQTT_SENSOR",
                          interval=5,
                          execute=mqtt_thread_func,
                          kwargs={
                              'pipe': pipe_mqtt_sensor,
                              'pv': client
                          })
    mqtt_thread.start()

    proc_mqtt_pub = mp.Process(name="MQTT PUBLISHER",
                               target=mqtt_pub_proc,
                               kwargs={
                                   'pipe_pub': pipe_mqtt_pub,
                                   'mqtt_broker': "ubuntu1t.local",
                                   'mqtt_port': 3881,
                                   'mqtt_client_name': "client1",
                                   'mqtt_topic': "topic1"
                               })
    proc_mqtt_pub.start()

    while 1:
      print(
          f"count:{count} Name: {mp.current_process().name} PID: {os.getpid()} thread name: {threading.current_thread().name}  id: {threading.get_ident()}"
      )
      count += 1
      time.sleep(1)

    # 스레드와 프로세스 정리
    mqtt_thread.stop()
    proc_mqtt_pub.join()

  except KeyboardInterrupt:
    pass


class CThread(threading.Thread):

  def __init__(self, port, execute, *args, **kwargs):
    threading.Thread.__init__(self)
    self.daemon = False
    self.port = port
    self.execute = execute
    self.args = args
    self.kwargs = kwargs

  def stop(self):
    self.join()

  def run(self):
    self.execute(self.port, *self.args, **self.kwargs)


class ResThread(threading.Thread):

  def __init__(self, execute, args=(), kwargs=None):
    threading.Thread.__init__(self)
    self.daemon = False
    self.event_stopped = threading.Event()
    self.execute = execute
    self.args = args
    self.kwargs = kwargs

  def stop(self):
    self.event_stopped.set()
    self.join()

  def run(self):
    while not self.event_stopped.wait(0):
      self.execute(*self.args, **self.kwargs)


if __name__ == '__main__':
  main()