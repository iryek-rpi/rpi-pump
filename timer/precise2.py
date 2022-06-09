import time
import _thread
import datetime

class Event:
    __slots__ = ( "_flag", "_lock", "_nl", "_pc", "_waiters" )

    _lock_type = _thread.LockType
    _timedelta = datetime.timedelta
    _perf_counter = time.perf_counter

    class _switch:
        __slots__ = ("_on",)

        def __call__(self, on: bool = None):
            if on is None:
                return self._on

            self._on = on

        def __bool__(self):
            return self._on

        def __init__(self):
            self._on = False

    def clear(self):
        with self._lock:
            self._flag(False)

    def is_set(self) -> bool:
        return self._flag()

    def set(self):
        with self._lock:
            self._flag(True)
            waiters = self._waiters

            for waiter in waiters:
                waiter.release()

            waiters.clear()

    def wait(self, timeout: float = None) -> bool:
        with self._lock:
            return self._wait(self._pc(), timeout)

    def _new_waiter(self) -> _lock_type:
        waiter = self._nl()
        waiter.acquire()
        self._waiters.append(waiter)
        return waiter

    def _wait(self, start: float, timeout: float, td=_timedelta,
          pc=_perf_counter, end: _timedelta = None, waiter: _lock_type = None,
          new_thread=_thread.start_new_thread, thread_delay=_timedelta(milliseconds=3) ) -> bool:
        flag = self._flag

        if flag:
            return True
        elif timeout is None:
            waiter = self._new_waiter()
        elif timeout <= 0:
            return False
        else:
            delay = td(seconds=timeout)
            end = td(seconds=start) + delay

            if delay > thread_delay:
                mark = end - thread_delay
                waiter = self._new_waiter()
                new_thread(self._wait_thread, (flag, mark, waiter))

        lock = self._lock
        lock.release()

        try:
            if waiter:
                waiter.acquire()

            if end:
                while ( not flag and td(seconds=pc()) < end ):
                    pass

        finally:
            lock.acquire()

            if waiter and not flag:
                self._waiters.remove(waiter)

        return flag()

    @staticmethod
    def _wait_thread(
            flag: _switch, 
            mark: _timedelta, 
            waiter: _lock_type, 
            td=_timedelta, 
            pc=_perf_counter, 
            sleep=time.sleep):
        while not flag and td(seconds=pc()) < mark:
            sleep(0.001)

        if waiter.locked():
            waiter.release()

    #__slots__ = ( "_flag", "_lock", "_nl", "_pc", "_waiters" )
    def __new__(cls):
        _self = object.__new__(cls)
        _self._flag = cls._switch()
        _self._lock = _thread.allocate_lock()
        _self._nl = _thread.allocate_lock
        _self._pc = cls._perf_counter
        _self._waiters = []
        return _self

def hello(s):
    #print('hello {} ({:.4f})'.format(s, time.perf_counter())) #time.time()))
    pass

if __name__ == "__main__":
    def test_wait_time():
        td = datetime.timedelta(microseconds=1)
        wait_time = td.total_seconds()  # 1e-06

        def test(event=Event(), delay=wait_time, pc=time.perf_counter):
            pc1 = pc()
            event.wait(delay)
            hello("test")
            print(f"pc1:{pc1:f}", " td:", td, f"wait_time:{wait_time:f}")
            pc2 = pc()
            #pc1, pc2 = [ int(nbr * 1_000_000_000) for nbr in (pc1, pc2) ]
            #pc1, pc2 = [ nbr for nbr in (pc1, pc2) ]
            return pc2 - pc1

        lst = [ f"{i}: {test():f}" for i in range(1, 11) ]
        print("\n".join(lst))

    test_wait_time()
    del test_wait_time

