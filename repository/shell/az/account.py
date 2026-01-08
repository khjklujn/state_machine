# repository imports
from repository.shell.delimited import SpaceDelimited

# local imports
from .az import Az


class Account(Az):
    """
    Interactions with Azure accounts.
    """

    @classmethod
    def list_locations(cls, *, subscription_id: str | None = None) -> list[dict]:
        """
        List all available locations for the subscription.

        Args:
            subscription_id: Optional subscription ID. If not provided, uses current subscription.

        raises:
            Exception: If exit code is not zero.
        """
        if subscription_id:
            command = SpaceDelimited(
                line=(
                    "az",
                    "account",
                    "list-locations",
                    "--subscription",
                    subscription_id,
                )
            )
        else:
            command = SpaceDelimited(
                line=(
                    "az",
                    "account",
                    "list-locations",
                )
            )

        return cls.execute(command=command)

    @classmethod
    def alias_list(cls) -> list[dict]:
        """
        List all account aliases.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "alias",
                "list",
            )
        )

        return cls.execute(command=command)

    @classmethod
    def alias_create(cls, *, alias_name: str) -> dict:
        """
        Create an account alias.

        Args:
            alias_name: The name of the alias to create.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "alias",
                "create",
                "--name",
                alias_name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def alias_show(cls, *, alias_name: str) -> dict:
        """
        Show details of an account alias.

        Args:
            alias_name: The name of the alias.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "alias",
                "show",
                "--name",
                alias_name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def alias_delete(cls, *, alias_name: str) -> dict:
        """
        Delete an account alias.

        Args:
            alias_name: The name of the alias to delete.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "alias",
                "delete",
                "--name",
                alias_name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def tenant_list(cls) -> list[dict]:
        """
        List all tenants for the authenticated account.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "tenant",
                "list",
            )
        )

        return cls.execute(command=command)

    @classmethod
    def tenant_show(cls, *, tenant_id: str) -> dict:
        """
        Show details of a specific tenant.

        Args:
            tenant_id: The tenant ID.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "tenant",
                "show",
                "--tenant",
                tenant_id,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def clear(cls) -> None:
        """
        Clear cached credentials and account information.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "clear",
            )
        )

        cls.execute(command=command)
