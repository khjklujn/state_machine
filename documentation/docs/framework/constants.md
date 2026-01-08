# Constants

One egregiouly bad practice in coding is the usage of "magic" values:  hard-coded strings and numbers.  These values should be provided by a config file in cases where the actual values are different in different environments, or constants, where the values are known and not expected to change.

Usage of "magic" values in the code is another source of copy-and-pasting functionality, where things that are supposed to be the same across the code base can drift in the implementation.

There should always be a single-source-of-truth for known values, and the definitions of known values should have a well known location as to where they are going to live in the code base.

In this framework, that location is the constant package.

So, let's take a look a relatively simple set of constants.

```python linenums="1"
from enum import unique, Enum


@unique
class BackupConfig(Enum):
    """
    Names of secrets in the Backup Config Key Vault.
    """

    CLIENT_NAME = "client-name"
    """The client's system-wide identifier. Used to validate backup requests."""

    POSTGRESQL_HOST = "postgresql-host"
    """The connection host for the PostgreSQL instance."""

    POSTGRESQL_PORT = "postgresql-port"
    """The connection port for the PostgreSQL instance."""

    POSTGRESQL_SERVICE_PRINCIPAL_ID = "postgresql-service-principal-id"
    """The application id of the service principal user used to perform the backups."""

    POSTGRESQL_SECRET = "postgresql-secret"
    """The secret used to get an authentication token for PostgreSQL from Entra Id."""

    KEY_NAME = "key-name"
    """The name of the key to use for encryption."""

    PUBLIC_KEY = "public-key"
    """The base64 definition of the public key to use for encryption."""

    EXCLUDE_DATABASES = "exclude-databases"
    """A comma delimited list of databases to exclude from backing up (*None* means nothing to exclude)."""

    STORAGE_UNC = "storage-unc"
    """The remote mount path for the file share (url of the storage area excluding "https:"--keep the "//"). Used to mount file share."""

    STORAGE_NAME = "storage-name"
    """The Azure name of the storage account. Used to mount file share"""

    STORAGE_KEY = "storage-key"
    """The key to authenticate with the storage account. Used to mount file share."""

    END_OF_MONTH_RETENTION = "end-of-month-retention"
    """The number of days to retain the end-of-month backups."""

    END_OF_YEAR_RETENTION = "end-of-year-retention"
    """The number of days to retain the end-of-year backups."""
```

This contains the names to use when fetching the secret values from the Backup Config key vault.  Some kind of translation between the names in Python and the names in Key Vault is needed, because hyphens are not allowed in Python names, and underscores are not allowed in Key Vault.

We're using Enum objects to represent constants.  They are immutable (can't be changed by the code), and they fit the naming convention very well.  In pretty much all languages, the naming convention for constants is ALL_CAPS.

Looking at an example of where they are used:

```python linenums="1"
# standard library imports
from datetime import datetime, UTC

# third party imports
from azure.keyvault.secrets import SecretClient
from pydantic import SecretStr

# application imports
from constant import backup_config
from state_machine import AbstractRepository, Logger


class BackupConfig(AbstractRepository):
    """
    Provides access to the client specific configurational information stored in Azure Key Vault.
    """

    def __init__(self, logger: Logger, client: SecretClient):
        self.logger = logger
        self.client = client

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
    def client_name(self) -> str:
        """The client name."""
        return self.execute(secret_name=backup_config.BackupConfig.CLIENT_NAME.value)

    @property
    def postgresql_host(self) -> str:
        """The PostgreSQL connection host."""
        return self.execute(
            secret_name=backup_config.BackupConfig.POSTGRESQL_HOST.value
        )

    @property
    def postgresql_port(self) -> int:
        """The PostgreSQL connection port."""
        return int(
            self.execute(
                secret_name=backup_config.BackupConfig.POSTGRESQL_PORT.value,
            )
        )

    @property
    def postgresql_service_principal_id(self) -> str:
        """The object id of the PostgreSQL service principal to perform the backups."""
        return self.execute(
            secret_name=backup_config.BackupConfig.POSTGRESQL_SERVICE_PRINCIPAL_ID.value
        )

    @property
    def postgresql_secret(self) -> SecretStr:
        """The Service Principal secret to use for retrieving a token to connect to the PostgreSQL instance."""
        return SecretStr(
            secret_value=self.execute(
                secret_name=backup_config.BackupConfig.POSTGRESQL_SECRET.value,
            )
        )

    @property
    def key_name(self) -> str:
        """The name of the encryption key."""
        return self.execute(secret_name=backup_config.BackupConfig.KEY_NAME.value)

    @property
    def public_key(self) -> str:
        """A base64 definition of the encryption key."""
        return self.execute(secret_name=backup_config.BackupConfig.PUBLIC_KEY.value)

    @property
    def exclude_databases(self) -> list[str]:
        """A comma delimited list of databases to exclude from backup."""
        exclude = self.execute(
            secret_name=backup_config.BackupConfig.EXCLUDE_DATABASES.value,
        )
        if exclude:
            return [database.strip() for database in exclude.split(",")]
        return []

    @property
    def storage_unc(self) -> str:
        """The remote mount path for the storage account (url of the storage account excluding "https:"--keep the "//")."""
        return self.execute(secret_name=backup_config.BackupConfig.STORAGE_UNC.value)

    @property
    def storage_name(self) -> str:
        """The Azure name of the storage account."""
        return self.execute(secret_name=backup_config.BackupConfig.STORAGE_NAME.value)

    @property
    def storage_key(self) -> SecretStr:
        """The connection key for the storage account."""
        return SecretStr(
            secret_value=self.execute(
                secret_name=backup_config.BackupConfig.STORAGE_KEY.value
            )
        )

    @property
    def end_of_month_retention(self) -> int:
        """The number of days to retain the end-of-month backups."""
        return int(
            self.execute(
                secret_name=backup_config.BackupConfig.END_OF_MONTH_RETENTION.value,
            )
        )

    @property
    def end_of_year_retention(self) -> int:
        """The number of days to retain the end-of-year backups."""
        return int(
            self.execute(
                secret_name=backup_config.BackupConfig.END_OF_YEAR_RETENTION.value,
            )
        )
```

This is the Repository we use to fetch secrets from a key vault.

In line 42, we _could_ have implemented

```python
return self.execute(secret_name=client_config.ClientConfig.CLIENT_NAME.value)
```

as

```python
return self.execute(secret_name="client-name")
```

However, we don't do that, because "client-name" is a "magic" value, and, in principal, magic values are bad.  If we needed to use the value of "client-name" somewhere else in the code base, we would have no way of determining it was defined the same way in both places, or even determining that it should be the same thing in both places.
