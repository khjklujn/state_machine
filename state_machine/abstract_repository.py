# standard library imports
from typing import Any

# local imports
from .logger import Logger


class AbstractRepository:
    """
    Abstract base class for repositories.

    *logger* will be injected when accessing a repository action from a Dependency set of repositories for a machine.
    """

    logger: Logger

    @classmethod
    def execute(cls) -> Any:
        """
        Needs to be overriden in subclasses.  All actions taken by a repository should be executed in this method as
        this is the assumed mocking point for unit tests.
        """
        raise NotImplementedError()
