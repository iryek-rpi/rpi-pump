#!/usr/bin/env python

#from uModbus
from serial import Serial
from collections import defaultdict

from umodbus.server.serial import get_server
from umodbus.server.serial.rtu import RTUServer
from umodbus.utils import log_to_stream

import logging

# Add stream handler to logger 'uModbus'.
log_to_stream(level=logging.DEBUG)

#s = Serial('/dev/ttyS0')
s = Serial('/dev/serial1')
s.timeout = 10

data_store = defaultdict(int)
app = get_server(RTUServer, s)


@app.route(slave_ids=[1], function_codes=[1, 2], addresses=list(range(0, 10)))
def read_data_store(slave_id, function_code, address):
    """" Return value of address. """
    return data_store[address]


@app.route(slave_ids=[1], function_codes=[5, 15], addresses=list(range(0, 10)))
def write_data_store(slave_id, function_code, address, value):
    """" Set value for address. """
    data_store[address] = value
    print(data_store)

if __name__ == '__main__':
    try:
        app.serve_forever()
    finally:
        app.shutdown()