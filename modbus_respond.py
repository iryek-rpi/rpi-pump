import logging

def respond(**kwargs):
    """Main 프로세스의 RespondThread에서 실행되는 Modbus 요청에 대한 응답 루틴
    """
    p_respond=kwargs['pipe']
    logging.info(f"Starting respond thread({kwargs})")
    while 1:
        logging.info(f"Receiving from Pipe:{p_respond}")
        n = p_respond.recv()
        logging.info(f"Received from Pipe:{n}, sending: {n+100}")
        p_respond.send(n+100)
        logging.info(f"sent: {n+100}")