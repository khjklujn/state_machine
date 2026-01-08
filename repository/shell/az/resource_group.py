# repository imports
from repository.shell.delimited import SpaceDelimited

# local imports
from .az import Az


class ResourceGroup(Az):
    """
    Interactions with Azure resource groups.
    """

    @classmethod
    def create(
        cls,
        *,
        name: str,
        location: str,
        subscription_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict:
        """
        Create a resource group.

        Args:
            name: The name of the resource group.
            location: The location/region for the resource group.
            subscription_id: Optional subscription ID. If not provided, uses current subscription.
            tags: Optional dictionary of tags to apply to the resource group.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "group", "create", "--name", name, "--location", location]
        if subscription_id:
            line.extend(["--subscription", subscription_id])
        if tags:
            tag_string = " ".join([f"{k}={v}" for k, v in tags.items()])
            line.extend(["--tags", tag_string])

        command = SpaceDelimited(line=tuple(line))

        return cls.execute(command=command)

    @classmethod
    def delete(
        cls,
        *,
        name: str,
        subscription_id: str | None = None,
        no_wait: bool = False,
        yes: bool = True,
    ) -> None:
        """
        Delete a resource group.

        Args:
            name: The name of the resource group to delete.
            subscription_id: Optional subscription ID. If not provided, uses current subscription.
            no_wait: Do not wait for the long-running operation to finish.
            yes: Do not prompt for confirmation.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "group", "delete", "--name", name]
        if subscription_id:
            line.extend(["--subscription", subscription_id])
        if no_wait:
            line.append("--no-wait")
        if yes:
            line.append("--yes")

        command = SpaceDelimited(line=tuple(line))

        cls.execute(command=command)

    @classmethod
    def exists(cls, *, name: str, subscription_id: str | None = None) -> bool:
        """
        Check if a resource group exists.

        Args:
            name: The name of the resource group.
            subscription_id: Optional subscription ID. If not provided, uses current subscription.

        raises:
            Exception: If exit code is not zero.
        """
        try:
            cls.show(name=name, subscription_id=subscription_id)
            return True
        except Exception:
            return False

    @classmethod
    def list(
        cls,
        *,
        subscription_id: str | None = None,
        tag: str | None = None,
    ) -> list[dict]:
        """
        List resource groups.

        Args:
            subscription_id: Optional subscription ID. If not provided, uses current subscription.
            tag: Optional tag filter in the format 'key[=value]'.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "group", "list"]
        if subscription_id:
            line.extend(["--subscription", subscription_id])
        if tag:
            line.extend(["--tag", tag])

        command = SpaceDelimited(line=tuple(line))

        return cls.execute(command=command)

    @classmethod
    def show(cls, *, name: str, subscription_id: str | None = None) -> dict:
        """
        Show details of a resource group.

        Args:
            name: The name of the resource group.
            subscription_id: Optional subscription ID. If not provided, uses current subscription.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "group", "show", "--name", name]
        if subscription_id:
            line.extend(["--subscription", subscription_id])

        command = SpaceDelimited(line=tuple(line))

        return cls.execute(command=command)

    @classmethod
    def update(
        cls,
        *,
        name: str,
        subscription_id: str | None = None,
        tags: dict[str, str] | None = None,
        add_tags: dict[str, str] | None = None,
        remove_tags: list[str] | None = None,
    ) -> dict:
        """
        Update a resource group.

        Args:
            name: The name of the resource group.
            subscription_id: Optional subscription ID. If not provided, uses current subscription.
            tags: Optional dictionary of tags to replace all existing tags.
            add_tags: Optional dictionary of tags to add or update.
            remove_tags: Optional list of tag keys to remove.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "group", "update", "--name", name]
        if subscription_id:
            line.extend(["--subscription", subscription_id])
        if tags:
            tag_string = " ".join([f"{k}={v}" for k, v in tags.items()])
            line.extend(["--tags", tag_string])
        if add_tags:
            tag_string = " ".join([f"{k}={v}" for k, v in add_tags.items()])
            line.extend(["--set", f"tags.{tag_string}"])
        if remove_tags:
            for tag_key in remove_tags:
                line.extend(["--remove", f"tags.{tag_key}"])

        command = SpaceDelimited(line=tuple(line))

        return cls.execute(command=command)

    @classmethod
    def export_template(
        cls,
        *,
        name: str,
        include_comments: bool = False,
        include_parameter_default_value: bool = False,
        resource_ids: list[str] | None = None,
    ) -> dict:
        """
        Export the template for a resource group.

        Args:
            name: The name of the resource group.
            include_comments: Include comments in the exported template.
            include_parameter_default_value: Include parameter default value in the exported template.
            resource_ids: Optional list of space-separated resource IDs to filter the export.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "group", "export", "--name", name]
        if include_comments:
            line.append("--include-comments")
        if include_parameter_default_value:
            line.append("--include-parameter-default-value")
        if resource_ids:
            line.extend(["--resource-ids"] + resource_ids)

        command = SpaceDelimited(line=tuple(line))

        return cls.execute(command=command)

    @classmethod
    def wait(
        cls,
        *,
        name: str,
        subscription_id: str | None = None,
        created: bool = False,
        deleted: bool = False,
        updated: bool = False,
        timeout: int | None = None,
    ) -> None:
        """
        Wait for a resource group to satisfy certain conditions.

        Args:
            name: The name of the resource group.
            subscription_id: Optional subscription ID. If not provided, uses current subscription.
            created: Wait until created with 'provisioningState' at 'Succeeded'.
            deleted: Wait until deleted.
            updated: Wait until updated with 'provisioningState' at 'Succeeded'.
            timeout: Maximum wait in seconds. Default is no timeout.

        raises:
            Exception: If exit code is not zero.
        """
        line = ["az", "group", "wait", "--name", name]
        if subscription_id:
            line.extend(["--subscription", subscription_id])
        if created:
            line.append("--created")
        if deleted:
            line.append("--deleted")
        if updated:
            line.append("--updated")
        if timeout:
            line.extend(["--timeout", str(timeout)])

        command = SpaceDelimited(line=tuple(line))

        cls.execute(command=command)
