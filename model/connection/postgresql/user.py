# third party imports
from pydantic import Field, BaseModel, SecretStr


class User(BaseModel):
    """
    Information to connect to PostgreSQL using PostgreSQL password authentication.
    """

    host: str
    """The url for connecting to the PostgreSQL instance."""

    port: int
    """The port for connecting to the PostgreSQL instance."""

    username: str
    """The PostgreSQL user name."""

    password: SecretStr
    """The PostgreSQL password."""

    database: str = Field(default="postgres")
    """The name of the database."""
