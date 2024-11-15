# standard library imports
from os import environ, _Environ
import json
from typing import Any, Optional


# repository imports
from long_term_storage.repository.shell.delimited import SpaceDelimited

# local import
from ..command import Command


class Az(Command):
    """
    Interactions with Azure using Azure CLI.
    """

    @classmethod
    def execute(
        cls,
        *,
        command: SpaceDelimited,
        cwd: Optional[str] = None,
        env: _Environ = environ,
        start_new_session: bool = False,
        input: Optional[str] = None,
    ) -> Any:
        """
        Executes an Azure CLI command.

        raises:
            Exception: If exit code is not zero.
        """

        result = super().execute(
            command=command,
            cwd=cwd,
            env=env,
            start_new_session=start_new_session,
            input=input,
        )

        return json.loads(result.stdout)
