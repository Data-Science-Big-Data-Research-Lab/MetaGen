import logging
import os
from datetime import datetime

import ray


def get_metagen_logger():
    return logging.getLogger('metagen_logger')


def metagen_logger_setup(level: int=logging.INFO, console_output: bool=True):
    logger = logging.getLogger('metagen_logger')
    logger.setLevel(level)

    if console_output:
        console_handler = yield_console_handler(level)
        logger.addHandler(console_handler)

    file_handler = yield_file_handler("metagen_logs/local", "metagen", level)
    logger.addHandler(file_handler)

def metagen_remote_logger_setup(level: int=logging.INFO, console_output: bool=True):
    logger = logging.getLogger('metagen_logger')
    logger.setLevel(level)

    if console_output:
        console_handler = yield_console_handler(level)
        logger.addHandler(console_handler)

    file_handler = yield_file_handler("metagen_logs/remotes", ray.get_runtime_context().get_worker_id(), level)
    logger.addHandler(file_handler)


def yield_file_handler(log_dir: str, file_prefix: str, level: int):
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{file_prefix}_{timestamp}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    return file_handler

def yield_console_handler(level: int):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    return console_handler

