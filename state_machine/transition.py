# standard library imports
from typing import Callable, Optional

# third party imports
from pydantic import Field, BaseModel

# local imports
from .result import Result


class Transition(BaseModel):
    """The expected return type from a node."""

    result: Result = Field(frozen=True)
    """The result of the node's actions."""

    exit_to: Callable[..., "Transition"] = Field(frozen=True)
    """The next node to be executed."""


class Exit(Transition):
    """The expected return type of a terminal node.  *result* and *exit* will be ignored."""

    result: Result = Field(frozen=True)
    """The result of the node's actions."""

    exit_to: Optional[Callable[..., "Transition"]] = Field(default=None, frozen=True) # type: ignore
    """The next node to be executed."""
