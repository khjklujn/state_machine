# standard library imports
from datetime import datetime

# third party imports
from pydantic import BaseModel, Field, SecretStr

# application imports
from long_term_storage.model.connection.key_vault import ServicePrincipal
from state_machine import Logger

# local imports
from .backup_config import BackupConfig
from .key_vault import KeyVault


class BackupConfigModel(BaseModel):
    """Connection and encryption information for performing backups."""

    client_name: str = Field(frozen=True)
    """The unique identifier for the PostgreSQL instance being backed up."""

    @classmethod
    def from_keyvault(cls, *, logger: Logger, connection_model: ServicePrincipal):
        """Populates the model from a key vault."""
        KeyVault.logger = logger
        client = KeyVault.execute(connection_model=connection_model)
        backup_config = BackupConfig(logger=logger, client=client)
        return cls(
            client_name=backup_config.client_name,
        )
