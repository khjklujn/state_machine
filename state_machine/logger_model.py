# third party imports
from pydantic import BaseModel

# application imports
from state_machine.config import Config


class Logging(BaseModel):
    """Configurations for logging."""

    level: str
    """The log level."""

    format: str
    """The line format of the log entries."""

    include_terminal: bool
    """Indicates whether log output should display in the executing shell."""

    rotation: str
    """The frequency for rotating the log files."""

    backup_count: int
    """The number of log rotations to keep prior to deleting them."""

    path: str
    """The path to the location the logs are stored."""


class LoggerModel(BaseModel):
    """Configurations in the Master Config file."""

    @classmethod
    def from_config(cls, *, config: Config):
        master_config = {}
        for config_item in cls.model_fields:
            master_config[config_item] = config[config_item].as_dict()

        return cls(**master_config)

    logging: Logging
    """Configuration for logging."""
