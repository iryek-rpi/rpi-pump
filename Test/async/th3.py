import picologging as logging
import threading
import time

logging.basicConfig(
    level=logging.DEBUG,
    format='(%(threadName)-9s) %(message)s',
)

logger = logging.getLogger()


def thread_function(name):
  logger.info("Thread %s: starting", name)
  time.sleep(2)
  logger.info("Thread %s: finishing", name)


if __name__ == "__main__":
  format = "%(asctime)s: %(message)s"
  logging.basicConfig(format=format, level=logger.info, datefmt="%H:%M:%S")

  logger.info("Main    : before creating thread")
  x = threading.Thread(target=thread_function, args=(1,))
  logger.info("Main    : before running thread")
  x.start()
  logger.info("Main    : wait for the thread to finish")
  # x.join()
  logger.info("Main    : all done")
