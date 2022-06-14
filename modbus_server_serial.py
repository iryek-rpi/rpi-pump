#!/usr/bin/env python3
"""Pymodbus Asyncio Server - asyncio_server_serial.py

Pymodbus Asyncio Server example 코드를 기반으로 작성
"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
import logging
import asyncio

from pymodbus.version import version
from pymodbus.server.async_io import StartSerialServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.framer.rtu_framer import ModbusRtuFramer

import pymodbus.datastore as ds
import modbus_address as ma

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

PORT = "/dev/serial1"

class PumpDataBlock(ds.ModbusSparseDataBlock):
    """Creates a sequential modbus datastore."""

    def __init__(self, address_list, pipe_req):
        """Initialize the datastore.
        """
        self.address = address_list.copy()
        self.values = {}
        self.default_value = 0
        self.pipe_req = pipe_req

    def validate(self, address, count=1):
        """Check to see if the request is in range.

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        """
        address += 40000
        logging.info(f"validate: address({address}) in {self.address}")
        return address in self.address

    def getValues(self, address, count=1):
        """Return the requested values of the datastore.

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        logging.info(f"MODBUS SERVER: sending request to getValues(address:{address})")
        self.pipe_req.send(address)
        response=self.pipe_req.recv()
        logging.info(f"MODBUS SERVER: received response:{response} for getValues(address:{address})")
        return response

    def setValues(self, address, values):
        """Set the requested values of the datastore.

        :param address: The starting address
        :param values: The new values to be set
        """
        logging.info(f"MODBUS SERVER: sending request to setValues(address:{address}, values:{values})")
        self.pipe_req.send(address)
        response=self.pipe_req.recv()
        logging.info(f"MODBUS SERVER: received response:{response} for setValues(address:{address}, values:{values})")

        #if not isinstance(values, list):
        #    values = [values]
        #start = address - self.address
        #self.values[start : start + len(values)] = values

def rtu_server_proc(pipe_req):
    """Modbus 서버 프로세스
    """
    logging.info("Starting rtu_server_proc()")
    asyncio.run(run_server(pipe_req))

async def run_server(pipe_req):
    """Run server."""
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
    # both forms of behavior::
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
    holding_reg = PumpDataBlock(ma.modbus_address_list, pipe_req)
    store = ModbusSlaveContext( hr=holding_reg )

    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
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
        }
    )

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    # 	deferred start:
    #server = await StartTcpServer(
    #    context,
    #    identity=identity,
    #    address=("0.0.0.0", 5020),  # nosec
    #    allow_reuse_address=True,
    #    defer_start=True,
    #)

    #asyncio.get_event_loop().call_later(20, lambda: server.serve_forever)
    #await server.serve_forever()

    # RTU:
    await StartSerialServer(context, framer=ModbusRtuFramer, identity=identity,
                        port=PORT, timeout=.005, baudrate=9600, autoreconnect=True)

if __name__ == "__main__":
    asyncio.run(run_server())
