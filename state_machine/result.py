# third party imports
from pydantic import Field, BaseModel


class Result(BaseModel):
    """
    Base class for the results.
    """

    node: str = Field(frozen=True)
    """The node the result was created in."""


class Success(Result):
    """
    Base class for a successful outcome.
    """


class Failure(Result):
    """
    Base class for a failing outcome.
    """

    message: str = Field(frozen=True)
    """The reason for the failure."""
