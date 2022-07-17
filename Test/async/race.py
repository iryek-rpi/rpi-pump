from threading import Thread, Lock
from time import sleep

counter = 0

def increase(by, lock):
    global counter
    lock.acquire()
    local_counter = counter
    sleep(1)
    local_counter += by
    counter = local_counter
    lock.release()
    print(f'counter={counter}')

lock = Lock()
t1 = Thread(target=increase, args=(10,lock))
t2 = Thread(target=increase, args=(20,lock))

t1.start()
t2.start()

t1.join()
t2.join()

print(f'The final counter is {counter}')