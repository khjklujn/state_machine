# standard library import
from dataclasses import dataclass
from typing import Any

# local imports
from .abstract_repository import AbstractRepository
from .logger import Logger


@dataclass
class BaseDependency:
    """
    Base class for representing repository dependencies used by machines.
    """

    logger: Logger
    """Access to the logger."""

    def __getattribute__(self, name: str) -> Any:
        """
        Provides introspective magic to inject the logger into a repository at the time
        at the time the repository is accessed.
        """
        attribute = super().__getattribute__(name)
        if hasattr(attribute, "__self__") and issubclass(
            attribute.__self__, AbstractRepository
        ):
            attribute.__self__.logger = self.logger

        return attribute
