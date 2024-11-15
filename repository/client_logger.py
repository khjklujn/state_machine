# standard library imports
import logging
import logging.handlers
import os

# application imports
from long_term_storage.model import MasterConfigModel
from state_machine import Logger
from state_machine.config import Config


master_config = MasterConfigModel.from_config(config=Config())


class ClientLogger(Logger):
    """
    Provides logging to per-client directories.
    """

    def __init__(self, *, client_name: str, file_name: str):
        logging_path = os.path.join(master_config.logging.path, client_name)
        os.makedirs(logging_path, exist_ok=True)

        log_formatter = logging.Formatter(master_config.logging.format)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(logging_path, f"{file_name}.log"),
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
