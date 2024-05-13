#import picologging as logging
import logging

import modbus_address as ma
import pump_variables
import pump_monitor
import config

import pump_util as util

#logger = logging.getLogger(util.MODBUS_LOGGER_NAME)
#logger.setLevel(logging.info)

def respond(**kwargs):
  """Main 프로세스의 RespondThread에서 실행되는 Modbus 요청에 대한 응답 루틴
    """
  p_respond = kwargs['pipe']
  pv: pump_variables.PV = kwargs['pv']

  logger = util.make_logger(name=util.MODBUS_CLIENT_LOGGER_NAME, filename=util.MODBUS_CLIENT_LOGFILE_NAME, level=logging.DEBUG)
  logger.info(f"Starting respond thread")
  while 1:
    logger.info(f"Waiting for msg from...")
    msg = p_respond.recv()
    logger.info(f"Received from Pipe:{msg}")
    wr, address, count, values = msg

    if not wr:
      values = pv.get_modbus_sequence(address=address, count=count)
      logger.info(f"get modbus block: {values} at: {address}")
    else:
      pv.set_modbus_sequence(address=address, values=values)
      logger.info(f"set modbus block at {address}")

    msg = (address, values)
    p_respond.send(msg)
    logger.info(f"sent: {msg}")