# standard library imports
import os

# third party imports
from azure.identity import EnvironmentCredential
from pydantic import Field, BaseModel, SecretStr, UUID1, HttpUrl


class ServicePrincipal(BaseModel):
    """
    Connection information to PostgreSQL for authenticating with a service principal.
    """

    host: str
    """The url for connecting to the PostgreSQL instance."""

    port: int
    """The port for connecting to the PostgreSQL instance."""

    service_principal_id: str
    """The service principal object id."""

    client_secret: SecretStr
    """The client secret to fetch a PostgreSQL token from Entra Id."""

    database: str = Field(default="postgres")
    """The name of the database."""

    tenant_id: UUID1 = Field(default="e17e2402-2a40-42ce-ad75-5848b8d4f6b6")
    """The tenant for authentication."""

    authority_host: HttpUrl = Field(default="https://login.microsoftonline.com")
    """The authority host for authentication."""

    token_host: HttpUrl = Field(
        default="https://ossrdbms-aad.database.windows.net/.default"
    )
    """The Entra Id end-point for retrieving the PostgreSQL authentication token."""

    @property
    def token(self) -> SecretStr:
        """
        Returns a token to be used as the password for connecting to PostgreSQL.
        """
        os.environ["AZURE_TENANT_ID"] = str(self.tenant_id)
        os.environ["AZURE_CLIENT_ID"] = self.service_principal_id
        os.environ["AZURE_CLIENT_SECRET"] = self.client_secret.get_secret_value()
        os.environ["AZURE_AUTHORITY_HOST"] = str(self.authority_host)

        credential = EnvironmentCredential()
        token = credential.get_token(str(self.token_host))

        return SecretStr(secret_value=token.token)
