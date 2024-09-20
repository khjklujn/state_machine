# standard library imports
from typing import Union

# third party imports
from pydantic import SecretStr


class EqualDelimited:
    """
    Represents a pair of strings that are delimited using an equals sign.  When used as a normal string,
    secret values will be masked.
    """

    def __init__(self, *, left: str, right: Union[str, SecretStr]):
        self._left = left
        self._right = right

    def get_secret_value(self) -> str:
        """
        Renders an equals delimited string with secret values unmasked.
        """
        return "=".join(
            (
                self._left,
                (
                    self._right.get_secret_value()
                    if isinstance(self._right, SecretStr)
                    else self._right
                ),
            )
        )

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return "=".join((self._left, str(self._right)))
