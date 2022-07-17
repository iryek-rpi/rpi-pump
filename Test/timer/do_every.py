import time
import datetime

def hello(s):
    #print('hello {} ({:.4f})'.format(s, time.perf_counter())) #time.time()))
    pass
    #time.sleep(2)

def do_every2(period,f,*args):
    def g_tick():
        t = time.perf_counter()
        print("outside while: ", t)
        while True:
            t += period
            t_now = time.perf_counter()
            gap = t-t_now
            #print("while t: ", t, "t_now: ", t_now, " gap: ", gap)
            print(f"t:{t} t_now:{t_now} period:{period:f} gap:{gap:f}")
            yield max(gap,0)
    g = g_tick()
    n = 0
    while n<10:
        pc1 = time.perf_counter()
        t = next(g)
        print("sleep: ", t)
        time.sleep(t)
        f(*args)
        pc2 = time.perf_counter()
        pc1, pc2 = [ int(nbr * 1_000_000) for nbr in (pc1, pc2) ]
        print(f"{n}: {pc2-pc1}")
        n += 1

#do_every2(3,hello,'foo')
def do_every3(period):
    n=0
    t = time.perf_counter()
    while n<10:
        t += period
        pc1 = time.perf_counter()
        gap = t - pc1
        delay = max(gap, 0)
        print(f"t:{t:f} pc1:{pc1:f} period:{period:f} gap:{gap:f} sleep:{delay:f}")
        time.sleep(delay)
        pc2 = time.perf_counter()
        #pc1, pc2 = [ int(nbr * 1_000_000) for nbr in (pc1, pc2) ]
        print(f"{n}: sleep:{delay:f} elapsed:{pc2-pc1}")
        n += 1

if __name__ == "__main__":
        td = datetime.timedelta(microseconds=200)
        delay = td.total_seconds()  # 1e-06

        do_every2(delay, hello, 'foo')
        print()
        do_every3(delay)

'''
if __name__ == "__main__":
    def test_wait_time():
        td = datetime.timedelta(microseconds=1)
        wait_time = td.total_seconds()  # 1e-06

        def test(event=Event(), delay=wait_time, pc=time.perf_counter):
            pc1 = pc()
            event.wait(delay)
            pc2 = pc()
            pc1, pc2 = [ int(nbr * 1_000_000_000) for nbr in (pc1, pc2) ]
            #pc1, pc2 = [ nbr for nbr in (pc1, pc2) ]
            return pc2 - pc1

        lst = [ f"{i}.\t\t{test()}" for i in range(1, 11) ]
        print("\n".join(lst))

    test_wait_time()
    del test_wait_time
'''