# standard library imports
from datetime import datetime

# third party imports
from pydantic import SecretStr

# repository imports
from long_term_storage.repository.shell.delimited import SpaceDelimited

# local imports
from .az import Az


class Ad(Az):
    """
    Interacting with Entra Id.
    """

    @classmethod
    def app_credential_reset(
        cls, *, application_id: str, name: str, end_date: datetime
    ) -> SecretStr:
        """
        Resets the client secret for a service principal.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "ad",
                "app",
                "credential",
                "reset",
                "--id",
                application_id,
                "--display-name",
                name,
                "--end-date",
                end_date.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            )
        )

        return SecretStr(secret_value=cls.execute(command=command)["password"])

    @classmethod
    def sp_list(
        cls, *, service_principal_name: str
    ) -> dict:
        """
        Returns the definition information for a service principal.
        """
        command = SpaceDelimited(
            line=(
                "az",
                "ad",
                "sp",
                "list",
                "--display-name",
                service_principal_name
            ),
        )
        results = cls.execute(command=command)

        return {
            "application_id": results[0]["appId"],
            "object_id": results[0]["id"],
        }
