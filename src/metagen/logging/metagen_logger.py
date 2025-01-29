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


DETAILED_INFO = 15
logging.addLevelName(DETAILED_INFO, "DETAILED_INFO")

def detailed_info(self, message, *args, **kws):
    if self.isEnabledFor(DETAILED_INFO):
        self._log(DETAILED_INFO, message, args, **kws)

logging.Logger.detailed_info = detailed_info

def get_metagen_logger(level: int=logging.INFO, console_output: bool=True, distributed: bool=False):
    logger = logging.getLogger('metagen_logger')
    if not logger.handlers:
        if distributed:
            metagen_logger_setup(level, console_output, "metagen_logs/remotes")
        else:
            metagen_logger_setup(level, console_output, "metagen_logs/local")
    else:
        if not logger_has_filehandler():
            if distributed:
                set_metagen_logger_file_handler(level,"metagen_logs/remotes")
            else:
                set_metagen_logger_file_handler(level,"metagen_logs/local")
    return logger

def metagen_logger_setup(level: int, console_output: bool, log_dir:str):
    logger = logging.getLogger('metagen_logger')
    set_metagen_logger_level_console_output(level, console_output)
    set_metagen_logger_file_handler(level, log_dir)
    logger.setLevel(level)

def set_metagen_logger_level_console_output(level: int = logging.DEBUG, console_output: bool=True):
    logger = logging.getLogger('metagen_logger')
    logger.setLevel(level)
    if console_output:
        console_handler = yield_console_handler(level)
        logger.addHandler(console_handler)

def set_metagen_logger_file_handler (level: int, log_dir: str):
    logger = logging.getLogger('metagen_logger')
    file_handler = yield_file_handler(log_dir, "metagen", level)
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

def logger_has_filehandler() -> bool:
    logger = logging.getLogger('metagen_logger')
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return True
    return False

