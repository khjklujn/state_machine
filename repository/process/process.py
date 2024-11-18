# standard library imports
from datetime import datetime
from getpass import getpass
import sys
from typing import Any, Callable

# application imports
from state_machine import AbstractRepository


class Process(AbstractRepository):
    """
    Process related things (print, input, exit...) to allow mocking.
    """

    @classmethod
    def execute(cls, function: Callable, *args, **kwargs) -> Any:
        start_time = datetime.utcnow()
        cls.logger.debug(f"  {cls.__name__} - Started")

        result = function(*args, **kwargs)

        end_time = datetime.utcnow()
        cls.logger.debug(
            f"  {cls.__name__} - Completed - Runtime: {end_time - start_time}"
        )

        return result

    @classmethod
    def exit(cls, *, result: int):
        """
        Exits the process with the value in _result_.
        """
        cls.logger.debug(f"Exiting with {result}")
        exit(result)

    @classmethod
    def input(cls, *, prompt: str) -> str:
        """
        Input from the command line.
        """
        return cls.execute(input, prompt)

    @classmethod
    def password(cls, *, prompt: str) -> str:
        """
        Hidden input from the command line.
        """
        return cls.execute(getpass, prompt)

    @classmethod
    def write_to_stderr(cls, *, content: str):
        """
        Outputs to stderr.
        """
        cls.execute(print, content, file=sys.stderr)

    @classmethod
    def write_to_stdout(cls, *, content: str):
        """
        Outputs to stdout.
        """
        cls.execute(print, content)
