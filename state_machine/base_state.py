# third party imports
from pydantic import BaseModel, ConfigDict


class BaseState(BaseModel):
    """The base class for keeping track of the data state within a machine."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
