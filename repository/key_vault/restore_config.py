# standard library imports
from datetime import datetime, UTC

# third party imports
from azure.keyvault.secrets import SecretClient
from pydantic import SecretStr

# application imports
from constant import restore_config
from state_machine import AbstractRepository, Logger


class RestoreConfig(AbstractRepository):
    """
    Provides access to the client specific configurational information stored in Azure Key Vault.
    """

    def __init__(self, *, logger: Logger, client_name: str, client: SecretClient):
        self.logger = logger
        self.client = client
        self.client_name = client_name

    def execute(self, *, secret_name: str) -> str:
        start_time = datetime.now(UTC)
        self.logger.debug(
            f"  key vault secret {secret_name} from {self.client.vault_url} - Started"
        )

        value = self.client.get_secret(secret_name).value
        if value is None:
            raise Exception(f"{secret_name} not defined in key vault")

        end_time = datetime.now(UTC)
        self.logger.debug(
            f"  key vault secret {secret_name} from {self.client.vault_url} - Completed - Runtime: {end_time - start_time}"
        )

        return value

    @property
    def backup_config_host(self) -> str:
        """The host of the key vault used for the backup config. Used to list secrets."""
        return self.execute(
            secret_name=restore_config.RestoreConfig.BACKUP_CONFIG_HOST.value
        )
