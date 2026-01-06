# standard library imports
import os

# third party imports
from azure.identity import EnvironmentCredential
from azure.keyvault.secrets import SecretClient
from pydantic import Field, BaseModel, SecretStr


class ServicePrincipal(BaseModel):
    """Connection information to a key vault for authenticating a service principal."""

    keyvault_host: str
    """The host of the key vault."""

    service_principal_id: str
    """The application id of the service principal."""

    client_secret: SecretStr
    """The client secret fo authenticating the service principal."""

    tenant_id: str = Field(default="e17e2402-2a40-42ce-ad75-5848b8d4f6b6")
    """The tenant for authentication."""

    authority_host: str = Field(default="https://login.microsoftonline.com")
    """The authority host for authentication."""

    @property
    def client(self) -> SecretClient:
        """
        Returns a client for interacting with key vault.
        """
        os.environ["AZURE_TENANT_ID"] = self.tenant_id
        os.environ["AZURE_CLIENT_ID"] = self.service_principal_id
        os.environ["AZURE_CLIENT_SECRET"] = self.client_secret.get_secret_value()
        os.environ["AZURE_AUTHORITY_HOST"] = self.authority_host

        credential = EnvironmentCredential()

        return SecretClient(vault_url=self.keyvault_host, credential=credential)
