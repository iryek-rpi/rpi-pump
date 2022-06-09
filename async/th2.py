import threading
import time
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s',)

class MyThread(threading.Thread):
  def __init__(self, group=None, execute=None, target=None, name=None,
            args=(), kwargs=None):
    #super(MyThread,self).__init__(group=group, target=target, 
    #name=name)
    threading.Thread.__init__(self)
    self.args = args
    self.kwargs = kwargs
    self.execute = execute
    return

  def run(self):
    logging.debug('running with %s and %s', self.args, self.kwargs)
    self.execute(*self.args, **self.kwargs)
    return

def foo(*args, **kwargs):
  print(kwargs)

if __name__ == '__main__':
  for i in range(3):
	  t = MyThread(execute=foo, kwargs={'a':1, 'b':2})
	  t.start()