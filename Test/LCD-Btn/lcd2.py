
import sys
import time
import lgpio

import buttons

I2C_ADDR  = 0x27 # I2C device address
LCD_WIDTH = 20   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

LCD_BACKLIGHT  = 0x08  # On 0X08 / Off 0x00

ENABLE = 0b00000100 # Enable bit

E_DELAY=0.0005
E_PULSE=0.0005

def lcd():
  return lcd.handle
lcd.handle = -1

def lcd_init(i2c):
    lcd.handle = i2c

    lcd_byte(i2c, 0x33,LCD_CMD) # 110011 initialization
    lcd_byte(i2c, 0x32,LCD_CMD) # 110010 initialization
    lcd_byte(i2c, 0x06,LCD_CMD) # 000110 Increment cursor to the right
    lcd_byte(i2c, 0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(i2c, 0x28,LCD_CMD) # 101000 Data length, number of lines, font size
    lcd_byte(i2c, 0x01,LCD_CMD) # 000001 Clear Device Screen
    time.sleep(E_DELAY)

def lcd_byte(i2c, bits, mode):
    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

    lgpio.i2c_write_byte(i2c, bits_high)
    #lcd_toggle_enable(bits_high)
    time.sleep(E_DELAY)
    lgpio.i2c_write_byte(i2c, (bits_high | ENABLE))
    time.sleep(E_PULSE)
    lgpio.i2c_write_byte(i2c, (bits_high & ~ENABLE))
    time.sleep(E_DELAY)

    lgpio.i2c_write_byte(i2c, bits_low)
    #lcd_toggle_enable(bits_low)
    time.sleep(E_DELAY)
    lgpio.i2c_write_byte(i2c, (bits_low | ENABLE))
    time.sleep(E_PULSE)
    lgpio.i2c_write_byte(i2c, (bits_low & ~ENABLE))
    time.sleep(E_DELAY)

def lcd_string(message, line):
    message = message.ljust(LCD_WIDTH," ")

    lcd_byte(lcd(), line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(lcd(), ord(message[i]), LCD_CHR)


g_i2c = 0 

def cbf(chip, gpio, level, tick):
    global g_i2c
    lcd_byte(g_i2c, 0x01, LCD_CMD)
    lcd_string(g_i2c, "chp={} g={}".format(chip, buttons.button_names[gpio]), LCD_LINE_1)
    lcd_string(g_i2c, "lvl={} t={:.09f}".format(level,  tick / 1e9), LCD_LINE_2)

def main(i2c, chip):
    global g_i2c
    lcd_init(i2c)
    g_i2c = i2c
    buttons.init_buttons(chip, buttons.gpio_buttons, cbf)
    while True:
        time.sleep(5)

if __name__ == '__main__':
    try:
        lgpio.exceptions = True
        h_i2c = lgpio.i2c_open(10, 0x27)
        h_chip = lgpio.gpiochip_open(0)
        main(h_i2c, h_chip)
    except KeyboardInterrupt:
        pass
    finally:
        lcd_byte(h_i2c, 0x01, LCD_CMD)
