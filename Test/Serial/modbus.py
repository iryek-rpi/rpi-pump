import serial
import serial.rs485
import time
import lgpio

TXDEN=24 # transmit enable pin

#GPIO.setup(TXDEN_1, GPIO.OUT, initial=GPIO.HIGH)
def init_485(h_chip):
    lgpio.gpio_claim_output(h_chip, TXDEN) #, 0, lgpio.SET_ACTIVE_LOW)

    #s = lgpio.serial_open("serial0", 19200)
    s = serial.rs485.RS485(port='/dev/ttyAMA0',
                baudrate=9600, timeout=5,
                parity=serial.PARITY_EVEN,
                stopbits=1, bytesize=serial.EIGHTBITS)
    #s = serial.Serial(port='/dev/ttyAMA0',
    #            baudrate=9600, timeout=5
    #            ,parity=serial.PARITY_EVEN)
    s.rs485_mode = serial.rs485.RS485Settings(rts_level_for_tx=False,
                rts_level_for_rx=False,
                delay_before_tx=0.0,
                delay_before_rx=-0.0)
    return s

# data is in hex format in python since rs485 rtu uses hex encoded data
SendFrame =b'\x01\x03\x00\x02\x00\x01\x25\xCA'
def main(h_chip):
    s = init_485(h_chip)
    
    while True:
        print("Sending a frame..")

        #write enabled for sending data frame to read the register
        lgpio.gpio_write(h_chip, TXDEN, 1)
        s.write(SendFrame)

        #read enabled to get reply from pymodbus slave software
        lgpio.gpio_write(h_chip, TXDEN, 0)

        #checking buffer with data available
        coming_data = s.inWaiting()

        # if no data is available comming data will be equal to 0
        print("Coming data:", coming_data)

        #reading the actual data from pymodbus slave
        if coming_data > 0:
            x = s.read(coming_data)

            #printing in hex format
            print(repr(x))
            print('ok')
        time.sleep(2)

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
while True:
    GPIO.output(TXDEN_1, GPIO.HIGH) #write enabled for sending data frame to read the register
    ser.write(SendFrame) #sending data frame
    GPIO.output(TXDEN_1, GPIO.LOW) #read enabled to get reply from pymodbus slave software
    coming_data = ser.inWaiting() #checking buffer with data available
    print “comming_data:”,coming_data # if no data is available comming data will be equal to 0
    x=ser.read(ser.inWaiting()) #reading the actual data from pymodbus slave
    print repr(x)# printing in hex format
    print “ok”
    time.sleep(2)
'''