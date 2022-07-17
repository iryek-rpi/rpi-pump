import sys
import time
import lgpio

BTN1 = 20
BTN2 = 16
BTN3 = 21

lgpio.exceptions = True
gpio_buttons = [BTN1, BTN2, BTN3]
button_names = {BTN1:"Button#1", BTN2:"Button#2", BTN3:"Button#3"}

def cpu_bound(number):
   print()
   print("calculating ", number)
   start_time = time.time()

   s=sum(i * i for i in range(number))

   duration = time.time() - start_time
   print(f"Duration {duration:.2f} seconds")

   return s

def cbf(chip, gpio, level, tick):
   print("chip={} gpio={} level={} time={:.09f}".format(
      chip, button_names[gpio], level,  tick / 1e9))

def init_buttons(h_chip, gpios, cbf):
    for i in range(len(gpios)):
        err = lgpio.gpio_claim_alert(h_chip, gpios[i], lgpio.BOTH_EDGES)
        if err < 0:
            print("GPIO in use {}:{} ({})".format(h_chip, gpio[i], lgpio.error_text(err)))
            return -1

        err = lgpio.gpio_set_debounce_micros(h_chip, gpios[i], 2000) # 2ms
        if err != 0:
            print("\nerr: ", err, " - gpio_set_debounce_micros() failed!\n")

        cb_id = lgpio.callback(h_chip, gpios[i], lgpio.BOTH_EDGES, cbf)
    
    return 1

if __name__ == '__main__':
    ch = lgpio.gpiochip_open(0)
    init_buttons(ch, gpio_buttons, cbf)
    while True:
        #print("idle...")
        #time.sleep(10)
        cpu_bound(5000000)