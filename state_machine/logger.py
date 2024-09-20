# standard library imports
import logging
import logging.handlers

# local imports
from .config import Config
from .logger_model import LoggerModel


master_config = LoggerModel.from_config(config=Config())


class Logger:
    """
    Wraps standard Python logging with configuration pulled from the provided config file.
    """

    def __init__(self, *, file_name: str):
        log_formatter = logging.Formatter(master_config.logging.format)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            f"{master_config.logging.path}/{file_name}.log",
            when=master_config.logging.rotation,
            backupCount=master_config.logging.backup_count,
        )
        file_handler.setFormatter(log_formatter)

        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(file_handler)

        if master_config.logging.level.lower() == "debug":
            self._logger.setLevel(logging.DEBUG)
        elif master_config.logging.level.lower() == "warning":
            self._logger.setLevel(logging.WARNING)
        elif master_config.logging.level.lower() == "error":
            self._logger.setLevel(logging.ERROR)
        elif master_config.logging.level.lower() == "critical":
            self._logger.setLevel(logging.CRITICAL)
        else:
            self._logger.setLevel(logging.INFO)

        if master_config.logging.include_terminal:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            self._logger.addHandler(console_handler)

    def critical(self, message: str):
        """
        Log a critical level message.
        """
        self._logger.critical(message)

    def debug(self, message: str):
        """
        Log a debug level message.
        """
        self._logger.debug(message)

    def error(self, message: str):
        """
        Log a error level message.
        """
        self._logger.error(message)

    def info(self, message: str):
        """
        Log a info level message.
        """
        self._logger.info(message)

    def warning(self, message: str):
        """
        Log a warning level message.
        """
        self._logger.warning(message)
