from multiprocessing.connection import Listener, Client
import threading, time, signal
from datetime import timedelta


class RepeatThread(threading.Thread):

  def __init__(self, interval, execute, args=(), kwargs=None):
    threading.Thread.__init__(self)
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
    while not self.event_stopped.wait(timeout=self.interval.total_seconds()):
      self.execute(*self.args, **self.kwargs)


class CommThread(threading.Thread):

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


class RespondThread(threading.Thread):

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