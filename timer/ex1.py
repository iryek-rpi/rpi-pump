import time
from threading import Event

time.sleep(3)  # to relax

# time.sleep()
tspan = 1
N = 1000
t1 = time.perf_counter()
for _ in range(N):
    time.sleep(tspan/N)
t2 = time.perf_counter()

print(t2-t1)

time.sleep(3)  # to relax

# Event.wait()    
tspan = 1
event = Event()
t1 = time.perf_counter()
for _ in range(N):
    event.wait(tspan/N)
t2 = time.perf_counter()

print(t2-t1)