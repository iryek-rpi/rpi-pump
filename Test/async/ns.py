import multiprocessing
import time

import numpy as np
import pandas as pd

my_2darray = np.array([[1, 2, 3], [4, 5, 6]])
df = pd.DataFrame(my_2darray)
print(df)

def producer(ns, event):
    global df
    ns.value = df
    event.set()
    time.sleep(2)
    print("producer waiting")
    event.wait()
    print("producer got the event")
    dff=ns.value
    print(dff)


def consumer(ns, event):
    try:
        print('Before event: {}'.format(ns.value))
    except Exception as err:
        print('Before event, error:', str(err))
    event.wait()
    print('After event:', ns.value)
    dff=ns.value
    dff[0][0]=123
    ns.value=dff
    print("consumer set event")
    event.set()


if __name__ == '__main__':
    mgr = multiprocessing.Manager()
    namespace = mgr.Namespace()
    event = multiprocessing.Event()
    p = multiprocessing.Process(
        target=producer,
        args=(namespace, event),
    )
    c = multiprocessing.Process(
        target=consumer,
        args=(namespace, event),
    )

    c.start()
    p.start()

    c.join()
    p.join()

