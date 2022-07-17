# https://medium.com/greedygame-engineering/an-elegant-way-to-run-periodic-tasks-in-python-61b7c477b679

import threading, time, signal

from datetime import timedelta

WAIT_TIME_SECONDS = 1

class ProgramKilled(Exception):
  pass

def foo(**kwargs):
  print(kwargs)
  print(time.ctime())
    
def signal_handler(signum, frame):
  raise ProgramKilled
    
class Job(threading.Thread):
  def __init__(self, interval, execute, args=(), kwargs=None):
    threading.Thread.__init__(self)
    self.daemon = False
    self.stopped = threading.Event()
    self.interval = interval
    self.execute = execute
    self.args = args
    self.kwargs = kwargs
    print("kwargs:",kwargs)
    
  def stop(self):
    self.stopped.set()
    self.join()

  def run(self):
    while not self.stopped.wait(self.interval.total_seconds()):
      self.execute(*self.args, **self.kwargs)
          
if __name__ == "__main__":
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)
  job = Job(interval=timedelta(seconds=WAIT_TIME_SECONDS), 
            execute=foo, args=(), kwargs={'a':100})
  job.start()
  
  while True:
    try:
      time.sleep(1)
    except ProgramKilled:
      print("Program killed: running cleanup code")
      job.stop()
      break
#output
#Tue Oct 16 17:47:51 2018
#Tue Oct 16 17:47:52 2018
#Tue Oct 16 17:47:53 2018
#^CProgram killed: running cleanup code