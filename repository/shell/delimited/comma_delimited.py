# standard library imports
from typing import Sequence, Union

# third party imports
from pydantic import SecretStr

# local imports
from .equal_delimited import EqualDelimited


class CommaDelimited:
    """
    Represents a sequence of strings that are rendered as comma delimited.  When used as a normal string,
    the secret values will be masked.
    """

    def __init__(self, *, line: Sequence[Union[str, SecretStr, EqualDelimited]]):
        self._line = line

    def get_secret_value(self) -> str:
        """
        Performs the rendering including the unmasking of secret values.
        """
        return ",".join(
            [
                (
                    item.get_secret_value()
                    if isinstance(item, EqualDelimited) or isinstance(item, SecretStr)
                    else item
                )
                for item in self._line
            ]
        )

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return ",".join([str(item) for item in self._line])
