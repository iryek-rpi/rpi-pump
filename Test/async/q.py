import threading, queue
from time import sleep

q = queue.Queue()


def worker():
  while True:
    item = q.get()
    print(f'Working on {item}')
    print(f'Finished {item}')
    sleep(0.1)
    q.task_done()


threading.Thread(target=worker, daemon=True).start()

for item in range(30):
  q.put(item)
print('All task requests sent\n', end='')

q.join()
print('All work completed')