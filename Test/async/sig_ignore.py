import signal
import os


def do_exit(sig, stack):
  signal.signal(signal.SIGINT, signal.SIG_IGN)
  raise SystemExit('Exiting')


#signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGINT, do_exit)
signal.signal(signal.SIGUSR1, do_exit)

print('My PID:', os.getpid())

signal.pause()