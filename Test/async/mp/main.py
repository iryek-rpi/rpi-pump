import sys
import time
import multiprocessing as mp

import threads

    p_respond, p_req = mp.Pipe()
    responder = threads.RespondThread(execute=modbus_respond.respond,
                                          kwargs={
                                              'chip': chip,
                                              'pipe': p_respond,
                                              'pv': pv()
                                          })
    responder.start()

    comm_proc = mp.Process(name="Modbus Server",
                           target=modbus_server_serial.rtu_server_proc,
                           kwargs={
                               'pipe_request': p_req,
                               'modbus_id': pv().modbus_id
                           })
    comm_proc.start()
    logger.info(f"@@@@@@@ comm_proc: {comm_proc.pid}")