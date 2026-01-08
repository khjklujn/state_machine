# repository imports
from repository.shell.delimited import SpaceDelimited

# local imports
from .az import Az


class Subscription(Az):
    """
    Interactions with Azure subscriptions.
    """

    @classmethod
    def account_list(cls) -> list[dict]:
        """
        List all subscriptions for the authenticated account.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "list",
            )
        )

        return cls.execute(command=command)

    @classmethod
    def account_show(cls, *, subscription_id: str | None = None) -> dict:
        """
        Show details of the current subscription or a specific subscription.

        Args:
            subscription_id: Optional subscription ID. If not provided, shows current subscription.

        raises:
            Exception: If exit code is not zero.
        """
        if subscription_id:
            command = SpaceDelimited(
                line=(
                    "az",
                    "account",
                    "show",
                    "--subscription",
                    subscription_id,
                )
            )
        else:
            command = SpaceDelimited(
                line=(
                    "az",
                    "account",
                    "show",
                )
            )

        return cls.execute(command=command)

    @classmethod
    def account_set(cls, *, subscription_id: str) -> dict:
        """
        Set the active subscription.

        Args:
            subscription_id: The subscription ID to set as active.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "set",
                "--subscription",
                subscription_id,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def account_get_access_token(
        cls,
        *,
        resource: str | None = None,
        resource_type: str | None = None,
        subscription_id: str | None = None,
    ) -> dict:
        """
        Get an access token for the current account.

        Args:
            resource: Resource to get access token for (e.g., 'https://management.azure.com/').
            resource_type: Type of resource (e.g., 'arm', 'ms-graph').
            subscription_id: Optional subscription ID.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "account", "get-access-token"]
        if resource:
            line.extend(["--resource", resource])
        if resource_type:
            line.extend(["--resource-type", resource_type])
        if subscription_id:
            line.extend(["--subscription", subscription_id])

        command = SpaceDelimited(line=tuple(line))

        return cls.execute(command=command)

    @classmethod
    def subscription_list(cls, *, include_eligible_offers: bool = False) -> list[dict]:
        """
        List all subscriptions in the tenant.

        Args:
            include_eligible_offers: Include eligible offers information.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "account", "subscription", "list"]
        if include_eligible_offers:
            line.append("--include-eligible-offers")

        command = SpaceDelimited(line=tuple(line))

        return cls.execute(command=command)

    @classmethod
    def subscription_show(cls, *, subscription_id: str) -> dict:
        """
        Show details of a specific subscription.

        Args:
            subscription_id: The subscription ID.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "subscription",
                "show",
                "--subscription",
                subscription_id,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def subscription_cancel(cls, *, subscription_id: str, cancel_at_period_end: bool = False) -> dict:
        """
        Cancel a subscription.

        Args:
            subscription_id: The subscription ID to cancel.
            cancel_at_period_end: Cancel at the end of the billing period.

        raises:
            Exception: If exit code is not zero.
        """
        line = [
            "az",
            "account",
            "subscription",
            "cancel",
            "--subscription",
            subscription_id,
        ]
        if cancel_at_period_end:
            line.append("--cancel-at-period-end")

        command = SpaceDelimited(line=tuple(line))

        return cls.execute(command=command)

    @classmethod
    def subscription_rename(cls, *, subscription_id: str, name: str) -> dict:
        """
        Rename a subscription.

        Args:
            subscription_id: The subscription ID to rename.
            name: The new name for the subscription.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "subscription",
                "rename",
                "--subscription",
                subscription_id,
                "--name",
                name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def subscription_enable(cls, *, subscription_id: str) -> dict:
        """
        Enable a subscription.

        Args:
            subscription_id: The subscription ID to enable.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "subscription",
                "enable",
                "--subscription",
                subscription_id,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def management_group_list(cls) -> list[dict]:
        """
        List all management groups.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "management-group",
                "list",
            )
        )

        return cls.execute(command=command)

    @classmethod
    def management_group_show(cls, *, group_id: str) -> dict:
        """
        Show details of a specific management group.

        Args:
            group_id: The management group ID.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "management-group",
                "show",
                "--name",
                group_id,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def management_group_subscription_add(
        cls, *, group_id: str, subscription_id: str
    ) -> dict:
        """
        Add a subscription to a management group.

        Args:
            group_id: The management group ID.
            subscription_id: The subscription ID to add.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "management-group",
                "subscription",
                "add",
                "--name",
                group_id,
                "--subscription",
                subscription_id,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def management_group_subscription_remove(
        cls, *, group_id: str, subscription_id: str
    ) -> dict:
        """
        Remove a subscription from a management group.

        Args:
            group_id: The management group ID.
            subscription_id: The subscription ID to remove.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "account",
                "management-group",
                "subscription",
                "remove",
                "--name",
                group_id,
                "--subscription",
                subscription_id,
            )
        )

        return cls.execute(command=command)
