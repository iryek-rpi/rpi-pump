"""Modbus server process
main thread에서 생성하는 subprocess
"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
#import picologging as logging
import logging
import pathlib

from pymodbus.version import version
from pymodbus.server import StartSerialServer
from pymodbus.device import ModbusDeviceIdentification

from pymodbus.datastore import ModbusSlaveContext
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
#from pymodbus.datastore import ModbusSparseDataBlock
import pymodbus.datastore as ds

#from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.transaction import ModbusRtuFramer

import modbus_address as ma
import pump_util as util

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
#PORT = "/dev/serial2"
PORT = "/dev/ttyAMA1"

#logging.basicConfig()
#logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

def rtu_server_proc(**kwargs):  #pipe_req, modbus_id):
  """Modbus 서버 프로세스
    """
  pipe_req = kwargs['pipe_request']
  modbus_id = kwargs['modbus_id']

  #logging.basicConfig()
  #logger = logging.getLogger('pymodbus.server')
  #logger.setLevel(logging.DEBUG)

  logger = util.make_logger(name=util.MODBUS_SERVER_LOGGER_NAME, filename=util.MODBUS_SERVER_LOGFILE_NAME, level=logging.DEBUG)

  logger.info(
      f"Starting a sync_server in rtu_server_proc(modbus_id:{modbus_id})")

#  global logger

  server = run_server(pipe_req, modbus_id, logger)

  logger.info("Shutdown serial sync server")
  server.shutdown()

def run_server(pipe_req, modbus_id, logger):
  """Run server."""
  holding_reg = PumpDataBlock(ma.modbus_address_list, pipe_req, logger)
  store = ModbusSlaveContext(hr=holding_reg)
  context = ModbusServerContext(slaves={modbus_id: store}, single=False)

  # ----------------------------------------------------------------------- #
  # initialize the server information
  # If you don"t set this or any fields, they are defaulted to empty strings.
  # ----------------------------------------------------------------------- #
  identity = ModbusDeviceIdentification(
      info_name={
          "VendorName": "SMTech",
          "ProductCode": "PU",
          "VendorUrl": "http://forsmt.co.kr",
          "ProductName": "AI Water Level Controller",
          "ModelName": "SM-001",
          "MajorMinorRevision": version.short(),
      })

  server = StartSerialServer(context=context,
                          identity=identity,
                          framer=ModbusRtuFramer,
                          port=PORT,
                          timeout=3.0,
                          baudrate=9600,
                          autoreconnect=False)
  return server



class PumpDataBlock(ds.ModbusSequentialDataBlock):
  """Creates a sequential modbus datastore."""

  def __init__(self, address, pipe_req, logger):
    """Initialize the datastore.
        """
    self.address = address.copy()
    self.values = {}
    self.default_value = 0
    self.pipe_req = pipe_req
    self.logger = logger

  def validate(self, address, count=1):
    """Check to see if the request is in range.

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        """
    #address += 40000
    self.logger.info(f"validate: address({address}) in {self.address}")
    return address in self.address

  def getValues(self, address, count=1):
    """Return the requested values of the datastore.
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
    msg = (False, address, count, [])
    self.logger.info(f"MODBUS SERVER: sending request to getValues(address:{address}, count:{count}, msg:{msg})")
    self.pipe_req.send(msg)
    response = self.pipe_req.recv()
    self.logger.info(
        f"MODBUS SERVER: received response:{response} for getValues(address:{address} msg:{msg})"
    )
    return response[1]

  def setValues(self, address, values):
    """Set the requested values of the datastore.
        :param address: The starting address
        :param values: The new values to be set
        """
    msg = (True, address, 0, values)
    self.logger.info(
        f"MODBUS SERVER: sending {msg} to setValues(address:{address}, values:{values})"
    )
    self.pipe_req.send(msg)
    response = self.pipe_req.recv()
    self.logger.info(
        f"MODBUS SERVER: received response:{response} for setValues(address:{address}, values:{values})"
    )