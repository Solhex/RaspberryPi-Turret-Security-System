"""This module is to addon a more sophisticated
external logging feature to the logging module.
"""


import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


def init_outfile_logging(
        log_name, log_folder: str = './logs',
        max_logs: int = 10, log_level=logging.DEBUG):
    """Initializes the python logging function with the added feature
    of an external folder with temporary log files, used for personal use.

    :return: logging
    """
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    else:
        logs_dir = os.listdir(log_folder)
        logs_in_dir = []
        for i in logs_dir:
            if '.log' in i:
                logs_in_dir.append(i)
        if len(logs_in_dir) > max_logs:
            logs_timed = {}
            for i in logs_in_dir:
                logs_timed[i] = os.path.getmtime(f'{log_folder}/{i}')
            for i in range(len(logs_in_dir) - max_logs):
                oldest_log = min(logs_timed, key=logs_timed.get)
                os.remove(
                    f'{log_folder}/{oldest_log}')
                del logs_timed[oldest_log]

    log = logging.getLogger(log_name)
    log.setLevel(log_level)

    formatter = logging.Formatter(
        '[%(asctime)s]:%(levelname)s:%(name)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    dt_string = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    handler = RotatingFileHandler(
        f'logs/{dt_string}.log', mode='w',
        maxBytes=5 * 1024 * 1024, backupCount=5,
        delay=False)

    handler.setFormatter(formatter)
    log.addHandler(handler)

    return log
