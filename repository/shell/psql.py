# standard library imports
import os

# third party imports
from azure.identity import EnvironmentCredential

# repository imports
from long_term_storage.model.connection.postgresql import User
from long_term_storage.repository.shell.delimited import SpaceDelimited

# local imports
from .command import Command


class Psql(Command):
    """
    Interactions with psql.
    """

    @classmethod
    def execute(
        cls,
        *,
        command: SpaceDelimited,
        connection_model: User,
    ):
        """
        Executes a psql action.
        """
        env = os.environ
        env["PGSSLMODE"] = "require"

        super().execute(
            command=command,
            env=env,
            start_new_session=True,
            input=connection_model.password.get_secret_value(),
        )

    @classmethod
    def restore(cls, *, connection_model: User, path: str):
        """
        Restores a SQL rendering of a PostgreSQL backup.  Sets PGSSLMODE to "require".  Password is provided by automating the
        response the "Password:" challenge prompt.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "psql",
                "-h",
                connection_model.host,
                "-p",
                str(connection_model.port),
                "-U",
                connection_model.username,
                "-d",
                connection_model.database,
                "--file",
                path,
            )
        )

        cls.execute(command=command, connection_model=connection_model)
