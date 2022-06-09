from time import sleep
import lgpio
TXDEN = 24

def init485(port=0):
    chip = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(chip, TXDEN) #, 0, lgpio.SET_ACTIVE_LOW)

    if port==0:
        s = lgpio.serial_open("serial0", 19200)
    else:
        s = lgpio.serial_open("serial1", 19200)

    return (chip, s)

def init_serial(port=0):
    chip = lgpio.gpiochip_open(0)

    if port==0:
        s = lgpio.serial_open("/dev/serial0", 19200)
    else:
        s = lgpio.serial_open("/dev/serial1", 19200)

    return (chip, s)

def run_serial(h_chip, s):
    while True:
        print("Checking serial port...")
        ba = lgpio.serial_data_available(s)
        if ba>0:
            (b, d) = lgpio.serial_read(s, ba)
            print("({}, {}) = seral_read(count={})".format(b,d,ba))
            sleep(0.1)
            if b>0:
                print("d=",d)
                print("bytes(d)=",bytes(d))
                e=lgpio.serial_write(s, bytes(d))
                if e <0:
                    print("Error {} = serial_write({})".format(e, d))
        sleep(3)

def run485(h_chip, s):
    lgpio.gpio_write(h_chip, TXDEN, 0)
    while True:
        print("Checking serial port...")
        ba = lgpio.serial_data_available(s)
        if ba>0:
            (b, d) = lgpio.serial_read(s, ba)
            print("({}, {}) = seral_read(count={})".format(b,d,ba))
            sleep(0.1)
            if b>0:
                #lgpio.gpio_write(h_chip, RE, 1)
                #lgpio.gpio_write(h_chip, DE, 1)
                lgpio.gpio_write(h_chip, TXDEN, 1)
                print("d=",d)
                print("bytes(d)=",bytes(d))
                e=lgpio.serial_write(s, bytes(d))
                if e <0:
                    print("Error {} = serial_write({})".format(e, d))
                #lgpio.gpio_write(h_chip, RE, 0)
                #lgpio.gpio_write(h_chip, DE, 0)
                lgpio.gpio_write(h_chip, TXDEN, 0)
        sleep(3)

def main(h_chip):
    s = init485(h_chip)
    if s<0:
        print("Error open serial: ", s)
        exit(0)
    
    lgpio.gpio_write(h_chip, TXDEN, 0)
    while True:
        print("Checking serial port...")
        ba = lgpio.serial_data_available(s)
        if ba>0:
            (b, d) = lgpio.serial_read(s, ba)
            print("({}, {}) = seral_read(count={})".format(b,d,ba))
            sleep(0.1)
            if b>0:
                print("d:", d)
                #lgpio.gpio_write(h_chip, RE, 1)
                #lgpio.gpio_write(h_chip, DE, 1)
                lgpio.gpio_write(h_chip, TXDEN, 1)
                print("d=",d)
                print("bytes(d)=",bytes(d))
                e=lgpio.serial_write(s, bytes(d))
                if e <0:
                    print("Error {} = serial_write({})".format(e, d))
                #lgpio.gpio_write(h_chip, RE, 0)
                #lgpio.gpio_write(h_chip, DE, 0)
                lgpio.gpio_write(h_chip, TXDEN, 0)
        sleep(3)

if __name__ == '__main__':
    try:
        lgpio.exceptions = True
        h_chip = lgpio.gpiochip_open(0)
        main(h_chip)
    except KeyboardInterrupt:
        pass
    finally:
        pass
