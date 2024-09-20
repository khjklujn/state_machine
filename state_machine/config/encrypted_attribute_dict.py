# standard library imports
import os
from typing import Any, Optional

# third pary imports
from cryptography.fernet import Fernet


class EncryptedAttributeDict:
    """
    Encrypted, nestable key-value pairs that are accessible as either attributes or key-indexes (like a javacript object).
    """

    FERNET_KEY = None

    def __init__(self, init_value: Optional[dict] = None):
        self._attributes = {}
        if init_value is not None:
            for name, value in init_value.items():
                self.add_attribute(name, value)

    def add_attribute(self, name: str, value: Any):
        """
        Add attributes.

        :param name: The name of the attribute.
        :param value: Either a scalar value or a dictionary. Scalar values will be encrypted.
        """
        if isinstance(value, dict):
            self._attributes[name] = EncryptedAttributeDict(value)
        else:
            self._attributes[name] = self.encrypt(value)

    def as_dict(self) -> dict:
        """
        Converts the attribute structure to a dictionary containing the encrypted values.
        """
        ret = {}
        for name, value in self._attributes.items():
            if isinstance(value, EncryptedAttributeDict):
                ret[name] = value.as_dict()
            else:
                ret[name] = value

        return ret

    def decrypt(self, value: Any) -> Any:
        """
        Returns the unencrypted value.
        """
        if not isinstance(value, str) or not value.startswith(":ENC:"):
            return value

        value = value[5:]

        fernet = Fernet(self.fernet_key())
        return fernet.decrypt(value.encode("utf-8")).decode("utf-8")

    def encrypt(self, value: str) -> str:
        """
        Returns the encrypted value.
        """
        if value.startswith(":ENC:"):
            return value

        fernet = Fernet(self.fernet_key())
        return f":ENC:{fernet.encrypt(value.encode('utf-8')).decode('utf-8')}"

    def fernet_key(self) -> str:
        """
        Reads and returns the encryption key.
        """
        if not self.FERNET_KEY:
            with open(os.path.join("/etc", "fernet.key"), "r") as file_in:
                self.FERNET_KEY = file_in.read()
        return self.FERNET_KEY

    def __contains__(self, name: str):
        return name in self._attributes

    def __getattribute__(self, name: str) -> Any:
        if (
            name != "_attributes"
            and hasattr(self, "_attributes")
            and name in self._attributes
        ):
            return self.decrypt(self._attributes[name])
        else:
            return super().__getattribute__(name)

    def __getitem__(self, name: str):
        return self.decrypt(self._attributes[name])

    def __setitem__(self, name: str, value: Any):
        self.add_attribute(name, value)
