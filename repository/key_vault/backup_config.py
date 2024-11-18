# standard library imports
from datetime import datetime

# third party imports
from azure.keyvault.secrets import SecretClient
from pydantic import SecretStr

# application imports
from long_term_storage.constant import backup_config
from state_machine import AbstractRepository, Logger


class BackupConfig(AbstractRepository):
    """
    Provides access to the client specific configurational information stored in Azure Key Vault.
    """

    def __init__(self, logger: Logger, client: SecretClient):
        self.logger = logger
        self.client = client

    def execute(self, *, secret_name: str) -> str:
        start_time = datetime.utcnow()
        self.logger.debug(
            f"  key vault secret {secret_name} from {self.client.vault_url} - Started"
        )

        value = self.client.get_secret(secret_name).value
        if value is None:
            raise Exception(f"{secret_name} not defined in key vault")

        end_time = datetime.utcnow()
        self.logger.debug(
            f"  key vault secret {secret_name} from {self.client.vault_url} - Completed - Runtime: {end_time - start_time}"
        )

        return value

    @property
    def client_name(self) -> str:
        """The client name."""
        return self.execute(secret_name=backup_config.BackupConfig.CLIENT_NAME.value)
