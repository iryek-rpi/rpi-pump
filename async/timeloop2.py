import threading, time, signal
import datetime
from datetime import timedelta
import signal

WAIT_TIME_SECONDS = 1

is_shutdown = False

def stop(sig, frame):
  print(f"SIGTERM at {datetime.datetime.now()}")
  global is_shutdown
  is_shutdown = True

def sigint(sig, frame):
  print(f"SIGINT at {datetime.datetime.now()}")
  global is_shutdown
  is_shutdown = True

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, sigint)

def foo():
    print(time.ctime())
    print(threading.active_count())
    t=threading.Timer(1, foo)
    t.start()

if __name__ == "__main__":
    
    #foo()
    while not is_shutdown:
      print(time.ctime())
      print("Number of threads:", threading.active_count())
      time.sleep(1)

#output
#Tue Oct 16 17:47:51 2018
#Tue Oct 16 17:47:52 2018
#Tue Oct 16 17:47:53 2018
#^CProgram killed: running cleanup code