# application imports
from state_machine import Logger


class MockLogger(Logger):
    """
    Mocks the logger.
    """

    def __init__(self):
        pass

    def critical(self, message: str):
        pass

    def debug(self, message: str):
        pass

    def error(self, message: str):
        pass

    def info(self, message: str):
        pass

    def warn(self, message: str):
        pass
