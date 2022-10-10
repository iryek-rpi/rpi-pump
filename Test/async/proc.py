import logging
import multiprocessing as mp
import signal
import datetime
import os

import threading, time, signal
from datetime import timedelta
from pprint import pp


def mqtt_pub_proc(**kwargs):
  while 1:
    print(
        f"Name: {mp.current_process().name} PID: {os.getpid()} thread name: {threading.current_thread().name}"
    )
    time.sleep(5)


def main():
  try:
    print(
        f"Name: {mp.current_process().name} PID: {os.getpid()} thread name: {threading.current_thread().name}"
    )

    proc_mqtt_pub = mp.Process(name="MQTT PUBLISHER",
                               target=mqtt_pub_proc,
                               kwargs={'mqtt_topic': "topic1"})
    proc_mqtt_pub.start()

    pp("\n########## proc_aqtt_pub started")
    #pp(dir(proc_mqtt_pub))

    while 1:
      print(
          f"Name: {mp.current_process().name} PID: {os.getpid()} thread name: {threading.current_thread().name}"
      )
      time.sleep(1)

    # 스레드와 프로세스 정리
    proc_mqtt_pub.join()

  except KeyboardInterrupt:
    print("keyboard interrupt")


if __name__ == '__main__':
  main()