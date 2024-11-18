# standard library imports
from datetime import datetime

# third party imports
from azure.keyvault.secrets import SecretClient

# application imports
from long_term_storage.model.connection.key_vault import ServicePrincipal
from state_machine import AbstractRepository


class KeyVault(AbstractRepository):
    """
    Interactions with Azure Key Vault.
    """

    @classmethod
    def execute(
        cls,
        *,
        connection_model: ServicePrincipal,
    ) -> SecretClient:
        start_time = datetime.utcnow()
        cls.logger.debug(
            f"  key vault client {connection_model.keyvault_host} - Started"
        )

        results = connection_model.client

        end_time = datetime.utcnow()
        cls.logger.debug(
            f"  key vault client {connection_model.keyvault_host} - Completed - Runtime: {end_time - start_time}"
        )

        return results
