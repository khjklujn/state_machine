# third party imports
from pydantic import SecretStr

# repository imports
from repository.shell.delimited import SpaceDelimited

# local imports
from .az import Az


class StorageAccount(Az):
    """
    Interactions with an Azure Storage Account.
    """

    @classmethod
    def list_keys(
        cls,
        *,
        account_name: str,
    ) -> list[SecretStr]:
        """
        Retrieve keys from a storage account.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "storage",
                "account",
                "keys",
                "list",
                "--account-name",
                account_name,
            )
        )

        return [
            SecretStr(secret_value=record["value"])
            for record in cls.execute(command=command)
        ]

    @classmethod
    def primary_key(
        cls,
        *,
        account_name: str,
    ) -> SecretStr:
        """
        Retrieve primary key from a storage account.

        raises:
            Exception: If exit code is not zero.
        """
        keys = cls.list_keys(account_name=account_name)

        return keys[0]

    @classmethod
    def show(
        cls,
        *,
        account_name: str,
    ) -> dict:
        """
        Retrieve definitional information from a storage account.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "storage",
                "account",
                "show",
                "--name",
                account_name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def share_create(
        cls, *, account_key: SecretStr, account_name: str, share_name: str
    ) -> bool:
        """
        Create a file share.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "storage",
                "share",
                "create",
                "--account-key",
                account_key,
                "--account-name",
                account_name,
                "--name",
                share_name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def share_exists(
        cls, *, account_key: SecretStr, account_name: str, share_name: str
    ) -> bool:
        """
        Check for the existence of a file share.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "storage",
                "share",
                "exists",
                "--account-key",
                account_key,
                "--account-name",
                account_name,
                "--name",
                share_name,
            )
        )

        results = cls.execute(command=command)

        return results["exists"]

    @classmethod
    def share_list(cls, *, account_key: SecretStr, account_name: str) -> list[dict]:
        """
        List the file shares in the storage account.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "storage",
                "share",
                "list",
                "--account-key",
                account_key,
                "--account-name",
                account_name,
            )
        )

        return cls.execute(command=command)
