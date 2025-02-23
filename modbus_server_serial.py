"""Modbus server process
main thread에서 생성하는 subprocess
Pymodbus Asyncio Server - asyncio_server_serial.py을 기반으로 작성
"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
#import picologging as logging
import logging
import pathlib
import asyncio

from pymodbus.version import version
from pymodbus.server.async_io import StartAsyncSerialServer
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

  logger = util.make_logger(name=util.MODBUS_SERVER_LOGGER_NAME, filename=util.MODBUS_SERVER_LOGFILE_NAME, level=logging.DEBUG)

  logger.info(
      f"Starting rtu_server_proc(modbus_id:{modbus_id})")

#  global logger

  asyncio.run(run_server(pipe_req, modbus_id, logger))


async def run_server(pipe_req, modbus_id, logger):
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

  server = await StartAsyncSerialServer(context=context,
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

    #if not isinstance(values, list):
    #    values = [values]
    #start = address - self.address
    #self.values[start : start + len(values)] = values



if __name__ == "__main__":
  asyncio.run(run_server())

  # ----------------------------------------------------------------------- #
  # initialize your data store
  # ----------------------------------------------------------------------- #
  # The datastores only respond to the addresses that they are initialized to
  # Therefore, if you initialize a DataBlock to addresses of 0x00 to 0xFF, a
  # request to 0x100 will respond with an invalid address exception. This is
  # because many devices exhibit this kind of behavior (but not all)::
  #
  #     block = ModbusSequentialDataBlock(0x00, [0]*0xff)
  #     block = ModbusSequentialDataBlock(0x00, [0]*0xff)
  #
  # Continuing, you can choose to use a sequential or a sparse DataBlock in
  # your data context.  The difference is that the sequential has no gaps in
  # the data while the sparse can. Once again, there are devices that exhibit
  # both forms of behavior#python3 /home/hwan/pump/pump.py >> /home/hwan/pump/logs/stream.log 2>&1::
  #
  #     block = ModbusSparseDataBlock({0x00: 0, 0x05: 1})
  #     block = ModbusSequentialDataBlock(0x00, [0]*5)
  #
  # Alternately, you can use the factory methods to initialize the DataBlocks
  # or simply do not pass them to have them initialized to 0x00 on the full
  # address range::
  #
  #     store = ModbusSlaveContext(di = ModbusSequentialDataBlock.create())
  #     store = ModbusSlaveContext()
  #
  # Finally, you are allowed to use the same DataBlock reference for every
  # table or you may use a separate DataBlock for each table.
  # This depends if you would like functions to be able to access and modify
  # the same data or not::
  #
  #     block = ModbusSequentialDataBlock(0x00, [0]*0xff)
  #     store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
  #block = ModbusSequentialDataBlock(0x00, [0]*0xff)
  #store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
  #
  # The server then makes use of a server context that allows the server to
  # respond with different slave contexts for different unit ids. By default
  # it will return the same context for every unit id supplied (broadcast
  # mode).
  # However, this can be overloaded by setting the single flag to False and
  # then supplying a dictionary of unit id to context mapping::
  #
  #     slaves  = {
  #         0x01: ModbusSlaveContext(...),
  #         0x02: ModbusSlaveContext(...),
  #         0x03: ModbusSlaveContext(...),
  #     }
  #     context = ModbusServerContext(slaves=slaves, single=False)
  #
  # The slave context can also be initialized in zero_mode which means that a
  # request to address(0-7) will map to the address (0-7). The default is
  # False which is based on section 4.4 of the specification, so address(0-7)
  # will map to (1-8)::
  #
  #     store = ModbusSlaveContext(..., zero_mode=True)
  # ----------------------------------------------------------------------- #
  # 번지	  Description	         R/W	    기타
  # 40001	  현재 수위	            읽기	%단위(0~100)
  # 40002	  예측 수위	            읽기	%단위(0~100)
  # 40003 	수위 모드	            읽기	0:현재 수위로 운전
  #                                  1:예측 수위로 운전"
  # 40004 	펌프1 상태	          읽기	0:펌프1 정지 1:펌프1 가동
  # 40005 	펌프2 상태	          읽기	0:펌프2 정지 1:펌프2 가동
  # 40006 	펌프3 상태	          읽기	0:펌프3 정지 1:펌프3 가동
  # 40007 	spare	              읽기
  # 40008 	spare	              읽기
  # 40009 	spare	              읽기
  # 40010 	spare	              읽기
  # 40011 	수위H값(정지수위)       쓰기   %단위(0~100)
  # 40012 	수위L값(가동수위)       쓰기	 %단위(0~100)
  # 40013 	펌프운전모드	          쓰기	 0: 수동운전(펌프 제어값에 의한 운전)
  #                                    1: 자동운전(수위 설정값에 의한 운전)
  # 40014 	펌프1제어	            쓰기	  0:정지, 1:가동
  # 40015 	펌프2제어	            쓰기	  0:정지, 1:가동
  # 40016 	펌프3제어	            쓰기	  0:정지, 1:가동
  # 40017 	펌프가동댓수(자동운전시)  쓰기	 1:1대, 2:2대, 3:3대