# standard library imports
from tempfile import NamedTemporaryFile

# third party imports
from pydantic import SecretStr

# repository imports
from long_term_storage.repository.shell.delimited import SpaceDelimited

# local imports
from .az import Az


class KeyVault(Az):
    """
    Interactions with a key vault.
    """

    @classmethod
    def delete_policy_service_principal(
        cls, *, key_vault_name: str, sevice_principal_name: str
    ) -> dict:
        """
        Removes the access policy for a service principal.

        Raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "keyvault",
                "delete-policy",
                "--name",
                key_vault_name,
                "--object-id",
                sevice_principal_name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def secret_delete(cls, *, vault_name: str, name: str) -> list[dict]:
        """
        Delete a secret from a key vault.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "keyvault",
                "secret",
                "delete",
                "--vault-name",
                vault_name,
                "--name",
                name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def secret_list(cls, *, key_vault_url: str) -> list[str]:
        """
        Fetch a list of the secrets defined in a key vault.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=("az", "keyvault", "secret", "list", "--id", key_vault_url)
        )

        return [record["name"] for record in cls.execute(command=command)]

    @classmethod
    def secret_set(
        cls,
        *,
        vault_name: str,
        secret_name: str,
        value: SecretStr,
        description: str,
        upload: bool = False,
    ) -> dict:
        """
        Set a secret in a key vault.

        raises:
            Exception: If exit code is not zero.
        """
        if not upload:
            command = SpaceDelimited(
                line=(
                    "az",
                    "keyvault",
                    "secret",
                    "set",
                    "--description",
                    description,
                    "--name",
                    secret_name,
                    "--value",
                    value,
                    "--vault-name",
                    vault_name,
                )
            )

            return cls.execute(command=command)
        else:
            with NamedTemporaryFile("w") as file_out:
                file_out.write(value.get_secret_value())
                file_out.flush()
                command = SpaceDelimited(
                    line=(
                        "az",
                        "keyvault",
                        "secret",
                        "set",
                        "--description",
                        description,
                        "--name",
                        secret_name,
                        "--vault-name",
                        vault_name,
                        "--file",
                        file_out.name,
                    )
                )

                return cls.execute(command=command)

    @classmethod
    def secret_set_content_type(
        cls,
        *,
        vault_name: str,
        secret_name: str,
        description: str,
    ) -> dict:
        """
        Set the content type description for a secret in a key vault.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "keyvault",
                "secret",
                "set-attributes",
                "--name",
                secret_name,
                "--vault-name",
                vault_name,
                "--content-type",
                f"'{description}'",
            )
        )

        return cls.execute(command=command)

    @classmethod
    def secret_show(
        cls,
        *,
        vault_name: str,
        secret_name: str,
    ) -> str:
        """
        Retrieves a secret from a key vault.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "keyvault",
                "secret",
                "show",
                "--name",
                secret_name,
                "--vault-name",
                vault_name,
            )
        )

        result = cls.execute(command=command)

        return result["value"]

    @classmethod
    def set_policy_secret_service_principal(
        cls, *, key_vault_name: str, sevice_principal_name: str, permissions: list[str]
    ) -> dict:
        command = SpaceDelimited(
            line=(
                "az",
                "keyvault",
                "set-policy",
                "--name",
                key_vault_name,
                "--secret-permissions",
                " ".join(permissions),
                "--object-id",
                sevice_principal_name,
            )
        )

        return cls.execute(command=command)

    @classmethod
    def show(cls, *, name: str) -> str:
        """
        Returns the vault uri of a key vault.

        raises:
            Exception: If exit code is not zero.

        """
        command = SpaceDelimited(
            line=(
                "az",
                "keyvault",
                "show",
                "--name",
                name
            )
        )

        results = cls.execute(command=command)
        cls.logger.debug(f'{results["properties"]["vaultUri"]}')
        return results["properties"]["vaultUri"]
