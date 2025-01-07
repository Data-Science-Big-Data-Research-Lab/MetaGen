import logging
import os
from datetime import datetime

class DistributedLogger:
    """
    Logger distribuido con control flexible desde el método estático get_logger.
    - Si se proporcionan parámetros, reconfigura el logger.
    - Si no se proporcionan, usa la configuración existente.
    """
    _instance = None

    def __new__(cls, log_dir: str = "logs", level: int = logging.INFO, console_output: bool = True):
        if cls._instance is None:
            cls._instance = super(DistributedLogger, cls).__new__(cls)
            cls._instance._setup_logger(log_dir, level, console_output)
        return cls._instance

    def _setup_logger(self, log_dir: str, level: int, console_output: bool):
        """Configura el logger con un archivo por ejecución y control de salida."""
        self.logger = logging.getLogger("DistributedLogger")
        self.logger.handlers.clear()
        self.logger.setLevel(level)

        # Crear el directorio si no existe
        os.makedirs(log_dir, exist_ok=True)

        # Generar un archivo de log con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"log_{timestamp}.log")

        # Configurar handler de archivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        # Formato del log
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Configurar handler de consola si está habilitado
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    @staticmethod
    def get_logger(log_dir: str = None, level: int = None, console_output: bool = None):
        """
        Método estático flexible:
        - Si se proporcionan parámetros, reconfigura el logger con ellos.
        - Si no se proporcionan, usa la configuración actual.
        """
        if DistributedLogger._instance is None:
            # Si no existe una instancia, la crea con valores predeterminados
            DistributedLogger(log_dir or "logs", level or logging.INFO, console_output or True)
        else:
            # Reconfigurar si se pasan parámetros opcionales
            if log_dir or level or console_output is not None:
                DistributedLogger._instance._setup_logger(
                    log_dir or "logs",
                    level or DistributedLogger._instance.logger.level,
                    console_output if console_output is not None else True
                )
        return DistributedLogger._instance.logger