
# The functions only: the logger object is called like the module that holds it,
# metagen.logging.metagen_logger, and importing it here would hide the module.
from .metagen_logger import set_metagen_logger_file_handler, set_metagen_logger_level

__all__ = ["set_metagen_logger_file_handler", "set_metagen_logger_level"]
