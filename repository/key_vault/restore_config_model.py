# standard library imports
from datetime import datetime, UTC

# third party imports
from pydantic import BaseModel, Field, SecretStr

# application imports
from model.connection.key_vault import ServicePrincipal
from state_machine import Logger

# local imports
from .restore_config import RestoreConfig
from .key_vault import KeyVault


class RestoreConfigModel(BaseModel):
    """Connection and encryption information for performing restorations."""

    backup_config_host: str = Field(frozen=True)
    """The host of the key vault used for the backup config. Used to list secrets."""

    @classmethod
    def from_keyvault(
        cls, *, logger: Logger, client_name: str, connection_model: ServicePrincipal
    ):
        """Populates the model from a key vault."""
        KeyVault.logger = logger
        client = KeyVault.execute(connection_model=connection_model)
        restore_config = RestoreConfig(
            logger=logger, client_name=client_name, client=client
        )
        return cls(
            backup_config_host=restore_config.backup_config_host,
        )
