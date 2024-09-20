# standard library imports
from typing import Any, Optional


class AttributeDict:
    """
    Nestable key-value pairs that are accessible as either attributes or key-indexes (like a javacript object).
    """

    def __init__(self, init_value: Optional[dict] = None):
        self._attributes = {}
        if init_value is not None:
            for name, value in init_value.items():
                self.add_attribute(name, value)

    def add_attribute(self, name: str, value: Any):
        """
        Add attributes.
        """
        if isinstance(value, dict):
            self._attributes[name] = AttributeDict(value)
        else:
            self._attributes[name] = value

    def as_dict(self) -> dict:
        """
        Converts the attribute structure to a dictionary.
        """
        ret = {}
        for name, value in self._attributes.items():
            if isinstance(value, AttributeDict):
                ret[name] = value.as_dict()
            else:
                ret[name] = value

        return ret

    def __contains__(self, name: str):
        return name in self._attributes

    def __getattribute__(self, name: str) -> Any:
        if (
            name != "_attributes"
            and hasattr(self, "_attributes")
            and name in self._attributes
        ):
            return self._attributes[name]
        else:
            return super().__getattribute__(name)

    def __getitem__(self, name: str):
        return self._attributes[name]

    def __setitem__(self, name: str, value: Any):
        self.add_attribute(name, value)
