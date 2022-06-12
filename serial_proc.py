"""Modbus 통신을 위한 프로세스

RS-232 연결, Modbus 통신 관련 코드
"""

import logging
import asyncio

from pymodbus.version import version
from pymodbus.server.async_io import StartSerialServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock

from pymodbus.framer.rtu_framer import ModbusRtuFramer

import multiprocessing as mp

# from pymodbus.datastore import ModbusSparseDataBlock

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
FORMAT = (
    "%(asctime)-15s %(threadName)-15s"
    " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def modbus_proc():
  """Modbus 통신 프로세스
  """
  pass

