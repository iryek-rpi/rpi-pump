#from gpiozero import OutputDevice
from time import sleep
#from serial import Serial

import lgpio

#RE = 23
#DE = 24
TXDEN = 24
RO = 15 #RXD
DI = 14 #TXD

def init_485(h_chip):
    #lgpio.gpio_claim_output(h_chip, RE) #, 0, lgpio.SET_ACTIVE_LOW)
    #lgpio.gpio_claim_output(h_chip, DE) #, 0, lgpio.SET_ACTIVE_LOW)
    lgpio.gpio_claim_output(h_chip, TXDEN) #, 0, lgpio.SET_ACTIVE_LOW)

    s = lgpio.serial_open("serial0", 19200)
    #s = lgpio.serial_open("serial1", 19200)

    return s

def main(h_chip):
    s = init_485(h_chip)
    if s<0:
        print("Error open serial: ", s)
        exit(0)
    
    #lgpio.gpio_write(h_chip, RE, 0)
    #lgpio.gpio_write(h_chip, DE, 0)
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

'''
with Serial('/dev/ttyS0', 19200) as s:
	while True:
		# waits for a single character
		rx = s.read(1)

		# print the received character
		print("RX: {0}".format(rx))

		# wait some time before echoing
		sleep(0.1)

		# enable transmission mode
		de.on()
		re.on()

		#' echo the received character
		s.write(rx)
		s.flush()

		#' disable transmission mode
		de.off()
		re.off()
'''
