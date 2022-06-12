import multiprocessing as mp
import logging

def respond(**kwargs):
    """Main 프로세스의 RespondThread에서 실행되는 Modbus 요청에 대한 응답 루틴
    """
    p_respond=kwargs['pipe']
    while 1:
        n = p_respond.recv()
        logging.info(f"Received from Pipe:{n}, send{n+100}")
        p_respond.send(n+100)