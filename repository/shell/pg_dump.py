# standard library imports
import os

# repository imports
from repository.shell.delimited import SpaceDelimited

# application imports
from model.connection.postgresql import ServicePrincipal

# local imports
from .command import Command


class PgDump(Command):
    """
    Interacting with pg_dump.
    """

    @classmethod
    def dump_data(cls, *, connection_model: ServicePrincipal, path: str):
        """
        Pulls a SQL rendering of the data in the database to path.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "pg_dump",
                "-h",
                connection_model.host,
                "-p",
                str(connection_model.port),
                "-U",
                connection_model.service_principal_id,
                "--no-owner",
                "--data-only",
                connection_model.database,
                "--file",
                path,
            )
        )

        cls.execute(command=command, connection_model=connection_model)

    @classmethod
    def dump_roles(cls, *, connection_model: ServicePrincipal, path: str):
        """
        Pulls a SQL rendering of the roles in the database to path.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "pg_dumpall",
                "-h",
                connection_model.host,
                "-p",
                str(connection_model.port),
                "-U",
                connection_model.service_principal_id,
                "--quote-all-identifiers",
                "--no-role-passwords",
                "--roles-only",
                "--file",
                path,
            )
        )

        cls.execute(command=command, connection_model=connection_model)

    @classmethod
    def dump_schema(cls, *, connection_model: ServicePrincipal, path: str):
        """
        Pulls a SQL rendering of the schema for the database to path.  Ownership is not backed up.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "pg_dump",
                "-h",
                connection_model.host,
                "-p",
                str(connection_model.port),
                "-U",
                connection_model.service_principal_id,
                "--no-owner",
                "--schema-only",
                connection_model.database,
                "--file",
                path,
            )
        )

        cls.execute(command=command, connection_model=connection_model)

    @classmethod
    def execute(cls, *, command: SpaceDelimited, connection_model: ServicePrincipal):
        """
        Executes a pg_dump statement.
        """
        env = os.environ
        env["PGSSLMODE"] = "require"
        env["PGPASSWORD"] = connection_model.token.get_secret_value()

        super().execute(
            command=command,
            env=env,
        )
