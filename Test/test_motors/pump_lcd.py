#from smbus2 import SMBus
#from RPi.GPIO import RPI_REVISION
import lgpio
from time import sleep
from re import findall, match
from subprocess import check_output
from os.path import exists

import picologging as logging

FORMAT = ("%(asctime)-15s %(threadName)-15s"
          " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s")
logging.basicConfig(
    #format='%(asctime)s %(threadName) %(levelname)s:%(filename)s:%(message)s',
    format=FORMAT,
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()

# old and new versions of the RPi have swapped the two i2c buses
# they can be identified by RPI_REVISION (or check sysfs)
#BUS_NUMBER = 0 if RPI_REVISION == 1 else 1
BUS_NUMBER = 10

# other commands
LCD_CLEAR_DISPLAY = 0x01  # 0000 0001 other commands
LCD_RETURN_HOME = 0x02  # 0000 0010

LCD_ENTRY_MODE = 0x04  # 0000 0100 1. Entry Mode
LCD_DISPLAY_CONTROL = 0x08  # 0000 1000 2. Display Control
LCD_CURSOR_SHIFT = 0x10  # 0001 0000 3. Cursor Shift
LCD_FUNCTION_SET = 0x20  # 0010 0000 4. Function Set
LCD_SET_CGRAM_ADDR = 0x40  # 0100 0000 5. Custom Graphics RAM
LCD_SET_DDRAM_ADDR1 = 0x80  # 1000 0000 6. Display Data RAM
LCD_SET_DDRAM_ADDR2 = 0xC0  # 1100 0000

# 1. flags for display entry mode
LCD_ENTRY_SHIFT_DEC = 0x00  # 0000 0000
LCD_ENTRY_SHIFT_INC = 0x01  # 0000 0001
LCD_ENTRY_RIGHT = 0x00  # 0000 0000
LCD_ENTRY_LEFT = 0x02  # 0000 0010

# 2. flags for display on/off control
LCD_DISPLAY_OFF = 0x00  # 0000 0000
LCD_DISPLAY_ON = 0x04  # 0000 0100

LCD_CURSOR_OFF = 0x00  # 0000 0000
LCD_CURSOR_ON = 0x02  # 0000 0010

LCD_CURSOR_BLINK_OFF = 0x00  # 0000 0000
LCD_CURSOR_BLINK_ON = 0x01  # 0000 0001

# 3. flags for display/cursor shift
LCD_CURSOR_MOVE = 0x00  # 0000 0000
LCD_DISPLAY_MOVE = 0x08  # 0000 1000
LCD_MOVE_LEFT = 0x00  # 0000 0000
LCD_MOVE_RIGHT = 0x04  # 0000 0100

# 4. flags for function set
LCD_4BIT_MODE = 0x00  # 0000 0000
LCD_8BIT_MODE = 0x10  # 0001 0000
LCD_1LINE = 0x00  # 0000 0000
LCD_2LINE = 0x08  # 0000 1000
LCD_5x8DOTS = 0x00  # 0000 0000
LCD_5x10DOTS = 0x04  # 0000 0100

# flags for backlight control
LCD_BACKLIGHT_NONE = 0x00  # 0000 0000
LCD_BACKLIGHT = 0x08  # 0000 1000

En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit

# 2022/01/31 12:25
# 0123456789012345
CURSOR_Y10 = 0xC0 + 2
CURSOR_Y01 = 0xC0 + 3
CURSOR_M10 = 0xC0 + 5
CURSOR_M01 = 0xC0 + 6
CURSOR_D10 = 0xC0 + 8
CURSOR_D01 = 0xC0 + 9
CURSOR_H10 = 0xC0 + 11
CURSOR_H01 = 0xC0 + 12
CURSOR_MIN10 = 0xC0 + 14
CURSOR_MIN01 = 0xC0 + 15


def lcd():
  return lcd.instance


lcd.instance = -1


class I2CDevice:

  def __init__(self, addr=None, addr_default=None, bus=BUS_NUMBER):
    if not addr:
      # try autodetect address, else use default if provided
      try:
        self.addr = int('0x{}'.format(
          findall("[0-9a-z]{2}(?!:)", check_output(['/usr/sbin/i2cdetect', '-y', str(bus)]).decode())[0]), base=16) \
          if exists('/usr/sbin/i2cdetect') else addr_default
      except:
        self.addr = addr_default
    else:
      self.addr = addr
    #self.bus = SMBus(bus)
    self.device = lgpio.i2c_open(bus, addr)

  # write a single command
  def write_cmd(self, cmd):
    #self.bus.write_byte(self.addr, cmd)
    lgpio.i2c_write_byte(self.device, cmd)
    sleep(0.0001)

  # write a command and argument
  #def write_cmd_arg(self, cmd, data):
  #  self.bus.write_byte_data(self.addr, cmd, data)
  #  sleep(0.0001)

  # write a block of data
  #def write_block_data(self, cmd, data):
  #  self.bus.write_block_data(self.addr, cmd, data)
  #  sleep(0.0001)

  # read a single byte
  #def read(self):
  #  return self.bus.read_byte(self.addr)

  # read
  #def read_data(self, cmd):
  #  return self.bus.read_byte_data(self.addr, cmd)

  # read a block of data
  #def read_block_data(self, cmd):
  #  return self.bus.read_block_data(self.addr, cmd)


class Lcd:

  def __init__(self, addr=0x27, bus=10):
    self.addr = addr
    self.i2c = I2CDevice(addr=self.addr, addr_default=0x27, bus=bus)
    self.write(0x03)
    sleep(0.0045)  # wait minimum 4.1ms
    self.write(0x03)
    sleep(0.0045)  # wait minimum 4.1ms
    self.write(0x03)
    sleep(0.0015)
    self.write(0x02)  # set to 4-bit interface
    self.write(LCD_FUNCTION_SET | LCD_2LINE | LCD_5x8DOTS | LCD_4BIT_MODE)
    self.write(LCD_DISPLAY_CONTROL | LCD_DISPLAY_ON)
    self.write(LCD_CLEAR_DISPLAY)
    self.write(LCD_ENTRY_MODE | LCD_ENTRY_LEFT)
    sleep(0.2)
    self.cc = CustomCharacters()
    self.load_bar_data()

  # write a command to lcd
  def write(self, cmd, mode=0):
    self.write_four_bits(mode | (cmd & 0xF0))
    self.write_four_bits(mode | ((cmd << 4) & 0xF0))

  def write_four_bits(self, data):
    self.i2c.write_cmd(data | LCD_BACKLIGHT)
    self.lcd_strobe(data)

  # clocks EN to latch command
  def lcd_strobe(self, data):
    self.i2c.write_cmd(data | En | LCD_BACKLIGHT)
    sleep(.0005)
    self.i2c.write_cmd(((data & ~En) | LCD_BACKLIGHT))
    sleep(.0001)

  # put string function
  def string(self, msg, line):
    LCD_WIDTH = 16
    msg = msg.ljust(LCD_WIDTH, " ")
    logger.debug("|{}|".format(msg))

    if line == 1:
      self.write(0x80)
    if line == 2:
      self.write(0xC0)
    for char in msg:
      self.write(ord(char), Rs)

  # put a char on the current cursor position
  def put_char(self, c):
    self.write(ord(c), Rs)

  # put a string on the current cursor position
  def put_str(self, s):
    for c in s:
      self.write(ord(c), Rs)

  def cursor_pos(self, line=1, pos=0):
    if line == 1:
      line_flag = 0x80
    else:
      line_flag = 0xC0

    line_flag |= pos

    self.write(line_flag)
    self.write(LCD_DISPLAY_CONTROL | LCD_DISPLAY_ON | LCD_CURSOR_ON |
               LCD_CURSOR_BLINK_ON)

  def cursor_off(self):
    self.write(LCD_DISPLAY_CONTROL | LCD_DISPLAY_ON | LCD_CURSOR_OFF)

  def cursor_on(self):
    self.write(LCD_DISPLAY_CONTROL | LCD_CURSOR_ON | LCD_CURSOR_BLINK_ON)

  # put extended string function. Extended string may contain placeholder like {0xFF} for
  # displaying the particular symbol from the symbol table
  def extended_string(self, msg, line):
    if line == 1:
      self.write(0x80)
    if line == 2:
      self.write(0xC0)
    # Process the string
    while msg:
      # Trying to find pattern {0xFF} representing a symbol
      result = match(r'\{0[xX][0-9a-fA-F]{2}\}', msg)
      if result:
        self.write(int(result.group(0)[1:-1], 16), Rs)
        msg = msg[6:]
      else:
        self.write(ord(msg[0]), Rs)
        msg = msg[1:]

  # clear lcd and set to home
  def clear(self):
    self.write(LCD_CLEAR_DISPLAY)
    self.write(LCD_RETURN_HOME)

  # backlight control (on/off)
  # options: backlight(1) = ON, backlight(0) = OFF
  def backlight(self, state):
    if state == 1:
      self.i2c.write_cmd(LCD_BACKLIGHT)
    elif state == 0:
      self.i2c.write_cmd(LCD_BACKLIGHT_NONE)

  # load custom character data to CG RAM for later use in extended string. Data for
  # characters is hold in file custom_characters.txt in the same folder as i2c_dev.py
  # file. These custom characters can be used in printing of extended string with a
  # placeholder with desired character codes: 1st - {0x00}, 2nd - {0x01}, 3rd - {0x02},
  # 4th - {0x03}, 5th - {0x04}, 6th - {0x05}, 7th - {0x06} and 8th - {0x07}.
  def load_bar_data(self):
    chars_list = self.cc.bar_chars

    # commands to load character adress to RAM srarting from desired base adresses:
    char_load_cmds = [0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70, 0x78]
    for char_num in range(8):
      # command to start loading data into CG RAM:
      self.write(char_load_cmds[char_num])
      for line_num in range(8):
        line = chars_list[char_num][line_num]
        binary_str_cmd = "0b000{0}".format(line)
        self.write(int(binary_str_cmd, 2), Rs)

  def bar(self, percent, line):
    bar_repr = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    bar = ""
    for i in range(len(bar_repr)):
      if percent >= ((i + 1) * 10):
        bar_repr[i] = 1
      else:
        bar_repr[i] = 0
        if i == 0 and percent >= 5:
          bar_repr[i] = 1

      if i == 0:
        if bar_repr[i] == 0:  # Left character
          bar = bar + "{0x01}"  # Left empty
        else:
          bar = bar + "{0x00}"  # Left full
      elif i == 9:
        if bar_repr[i] == 0:  # Right character
          bar = bar + "{0x05}"  # Right empty
        else:
          bar = bar + "{0x04}"  # Right full
      else:
        if bar_repr[i] == 0:  # Central character
          bar = bar + "{0x03}"  # Central empty character
        else:
          bar = bar + "{0x02}"  # Central full character

    self.extended_string(bar + " {:2.1f}% ".format(percent), line)


class CustomCharacters:

  def __init__(self):
    # Data for custom character #1. Code {0x00}.
    self.char_1_data = [
        "11111", "10001", "10001", "10001", "10001", "10001", "10001", "11111"
    ]
    # Data for custom character #2. Code {0x01}
    self.char_2_data = [
        "11111", "10001", "10001", "10001", "10001", "10001", "10001", "11111"
    ]
    # Data for custom character #3. Code {0x02}
    self.char_3_data = [
        "11111", "10001", "10001", "10001", "10001", "10001", "10001", "11111"
    ]
    # Data for custom character #4. Code {0x03}
    self.char_4_data = [
        "11111", "10001", "10001", "10001", "10001", "10001", "10001", "11111"
    ]
    # Data for custom character #5. Code {0x04}
    self.char_5_data = [
        "11111", "10001", "10001", "10001", "10001", "10001", "10001", "11111"
    ]
    # Data for custom character #6. Code {0x05}
    self.char_6_data = [
        "11111", "10001", "10001", "10001", "10001", "10001", "10001", "11111"
    ]
    # Data for custom character #7. Code {0x06}
    self.char_7_data = [
        "11111", "10001", "10001", "10001", "10001", "10001", "10001", "11111"
    ]
    # Data for custom character #8. Code {0x07}
    self.char_8_data = [
        "11111", "10001", "10001", "10001", "10001", "10001", "10001", "11111"
    ]

    # bar graph characters
    # Left full character. Code {0x00}.
    self.c1_left_full = [
        "01111", "11000", "10011", "10111", "10111", "10011", "11000", "01111"
    ]

    # Left empty character. Code {0x01}.
    self.c2_left_empty = [
        "01111", "11000", "10000", "10000", "10000", "10000", "11000", "01111"
    ]

    # Central full character. Code {0x02}.
    self.c3_center_full = [
        "11111", "00000", "11011", "11011", "11011", "11011", "00000", "11111"
    ]

    # Central empty character. Code {0x03}.
    self.c4_center_empty = [
        "11111", "00000", "00000", "00000", "00000", "00000", "00000", "11111"
    ]

    # Right full character. Code {0x04}.
    self.c5_right_full = [
        "11110", "00011", "11001", "11101", "11101", "11001", "00011", "11110"
    ]

    # Right empty character. Code {0x05}.
    self.c6_right_empty = [
        "11110", "00011", "00001", "00001", "00001", "00001", "00011", "11110"
    ]

    self.custom_chars = [
        self.char_1_data, self.char_2_data, self.char_3_data, self.char_4_data,
        self.char_5_data, self.char_6_data, self.char_7_data, self.char_8_data
    ]

    self.bar_chars = [
        self.c1_left_full, self.c2_left_empty, self.c3_center_full,
        self.c4_center_empty, self.c5_right_full, self.c6_right_empty,
        self.char_7_data, self.char_8_data
    ]
