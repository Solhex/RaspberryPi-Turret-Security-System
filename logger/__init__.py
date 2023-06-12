"""This module is to addon a more sophisticated
external logging feature to the logging module.
"""


import os  # For manipulating the operating system.
import logging  # For logging functionality.
from datetime import datetime  # For getting the current date and time.
from logging.handlers import RotatingFileHandler  # For external logs.


def init_outfile_logging(
        log_name: str, log_folder: str = './logs',
        max_logs: int = 10, log_level=logging.DEBUG):
    """Initializes the python logging function with the added feature
    of an external folder with temporary log files, used for personal
    use.
    
    :param log_name: The name of the file to be logged usually
        `__name__` should be passed through by the main file
    :type log_name: str
    :param log_folder: The path to the log folder, defaults to `./logs`
    :type log_folder: str, optional
    :param max_logs: The maximum amount of logs to be present within
        the logs folder at a time, defaults to 10
    :type max_logs: int, optional
    :param log_level: 
    :type log_level: class`logging.logger`, optional
    
    :return: The initialized logging class
    :rtype: `logging.logger`
    """
    
    if not os.path.exists(log_folder):
        # Checks if the logs folder exists and if not create it.
        os.mkdir(log_folder)
    else:
        logs_dir = os.listdir(log_folder)
        # Gets every file in the log folder.

        logs_in_dir = []
        for i in logs_dir:
            if '.log' in i:
                logs_in_dir.append(i)
        # Creates an empty list and places every file that ends in .log
        # into it.

        if len(logs_in_dir) > max_logs:
            # If too many logs in log folder execute code which will
            # delete old logs.

            logs_timed = {}
            for i in logs_in_dir:
                logs_timed[i] = os.path.getmtime(f'{log_folder}/{i}')
            # Gets each log and checks it modification time and adds
            # it into a dictionary.

            for i in range(len(logs_in_dir) - max_logs):
                oldest_log = min(logs_timed, key=logs_timed.get)
                os.remove(
                    f'{log_folder}/{oldest_log}')
                del logs_timed[oldest_log]
            # For every file over the max_logs delete the oldest
            # log file.

    log = logging.getLogger(log_name)
    log.setLevel(log_level)
    # Creates the log instance and sets the default logging level.

    formatter = logging.Formatter(
        '[%(asctime)s]:%(levelname)s:%(name)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Sets what information each log will hold.

    dt_string = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    handler = RotatingFileHandler(
        f'logs/{dt_string}.log', mode='w',
        maxBytes=5 * 1024 * 1024, backupCount=5,
        delay=False
    )
    # Sets the name of each log file.

    handler.setFormatter(formatter)
    log.addHandler(handler)
    # Finalises the log instance and then returns it to be used.

    return log
