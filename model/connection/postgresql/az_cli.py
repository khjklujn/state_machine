# third party imports
from azure.identity import DefaultAzureCredential
from pydantic import Field, BaseModel, SecretStr


class AzCli(BaseModel):
    """
    Connection information for connecting to PostgreSQL using a token where Entra Id authentication
    was performed locally using Azure CLI.
    """

    host: str
    """
    The url for connecting to PostgreSQL.
    """

    port: int
    """
    The port for connecting to PostgreSQL.
    """

    username: str
    """
    The user name that was used when authenticating with Entra Id.
    """

    database: str = Field(default="postgres")
    """
    The name of the database to connect to.
    """

    token_host: str = Field(
        default="https://ossrdbms-aad.database.windows.net/.default"
    )
    """
    The url used to fetch a PostgreSQL token from Entra Id.
    """

    @property
    def token(self) -> SecretStr:
        """
        Fetches the authentication token with the assumption the user has authenticated
        with Azure CLI.
        """
        credential = DefaultAzureCredential()
        token = credential.get_token(self.token_host)

        return SecretStr(secret_value=token.token)
