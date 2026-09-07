"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import logging
import os
from datetime import datetime
from typing import Any, cast


DETAILED_INFO = 15
logging.addLevelName(DETAILED_INFO, "DETAILED_INFO")


class MetaGenLogger(logging.Logger):
    """
    A logger that knows the DETAILED_INFO level, sitting between INFO and DEBUG.

    The method used to be attached onto ``logging.Logger`` itself, which handed it
    to every logger in the process, MetaGen's or not (A-11). Only the two loggers
    built below need it, so it lives in a subclass of their own.
    """

    def detailed_info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a message with the DETAILED_INFO level.

        :param message: The message to log.
        :type message: str
        """
        if self.isEnabledFor(DETAILED_INFO):
            self._log(DETAILED_INFO, message, args, **kwargs)


def _get_metagen_logger(name: str) -> MetaGenLogger:
    """
    Return one of MetaGen's own loggers, built as a `MetaGenLogger`.

    The logger class is swapped only around the call and restored right after, so
    loggers belonging to anybody else keep the class they would have had.

    :param name: The name of the logger.
    :type name: str
    :return: The logger, created on the first call and reused afterwards.
    :rtype: MetaGenLogger
    """
    previous_class = logging.getLoggerClass()
    logging.setLoggerClass(MetaGenLogger)
    try:
        logger = logging.getLogger(name)
    finally:
        logging.setLoggerClass(previous_class)
    return cast(MetaGenLogger, logger)


def get_handler_by_name(logger: logging.Logger, name: str) -> logging.Handler | None:
    res = None
    for handler in logger.handlers:
        if handler.get_name() == name:
            res = handler
    return res

def logger_has_filehandler(logger: logging.Logger) -> bool:
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return True
    return False

def add_console_handler(logger: logging.Logger):
    # Idempotent: this used to be called once per get_remote_metagen_logger(), so
    # the handlers piled up and every line was printed once per call (A-11).
    if get_handler_by_name(logger, 'console') is not None:
        return
    console_handler = logging.StreamHandler()
    console_handler.set_name('console')
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

def add_file_handler(logger: logging.Logger, log_dir: str) -> None:
    # Idempotent for the same reason, and with a sharper one of its own: each call
    # opens a new timestamped file.
    if logger_has_filehandler(logger):
        return
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"metagen_{timestamp}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.set_name('file')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

def set_metagen_logger_level(level: int = logging.DEBUG):
    """
    Turn MetaGen's console output on at the given level.

    This is the configuration step: importing the package installs a NullHandler
    and nothing else, the way a library is supposed to leave the logging setup to
    whoever is using it. Calling this twice leaves one console handler, not two.

    :param level: The level to log at, DEBUG by default.
    :type level: int
    """
    logger = metagen_logger

    # Removed and rebuilt so that a second call replaces the handler instead of
    # stacking another one. Guarded: there is no console handler until the first
    # call, and this used to do None.close() (A-11).
    console = get_handler_by_name(logger, 'console')
    if console is not None:
        logger.removeHandler(console)
        console.close()

    logger.setLevel(level)
    add_console_handler(logger)


def set_metagen_logger_file_handler(log_dir:str = "metagen_logs"):
    add_file_handler(metagen_logger, log_dir)

def get_remote_metagen_logger(level: int=logging.CRITICAL) -> MetaGenLogger:
    logger = _get_metagen_logger('metagen_remote_logger')
    logger.setLevel(level)
    add_console_handler(logger)
    return logger


metagen_logger = _get_metagen_logger('metagen_logger')
metagen_logger.setLevel(logging.CRITICAL)

# A NullHandler and nothing else on import. Installing a StreamHandler here made
# MetaGen decide, just by being imported, where every one of its records went
# (A-11). set_metagen_logger_level() is how console output is turned on.
metagen_logger.addHandler(logging.NullHandler())
