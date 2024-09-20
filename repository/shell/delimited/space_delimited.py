# standard library imports
from typing import Sequence, Union

# standard library imports
from pydantic import SecretStr

# local imports
from .comma_delimited import CommaDelimited
from .equal_delimited import EqualDelimited


class SpaceDelimited:
    """
    Represents a sequence of space delimited strings.  When used as a normal string, secret vlaues
    will be masked.
    """

    def __init__(
        self, *, line: Sequence[Union[str, SecretStr, CommaDelimited, EqualDelimited]]
    ):
        self._line = line

    def get_secret_value(self) -> list[str]:
        """
        Renders space delimited items as a list rather than a single string.  Secret values will be unmasked.
        """
        return [
            (
                item.get_secret_value()
                if isinstance(item, CommaDelimited)
                or isinstance(item, EqualDelimited)
                or isinstance(item, SecretStr)
                else item
            )
            for item in self._line
        ]

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return " ".join([str(item) for item in self._line])
