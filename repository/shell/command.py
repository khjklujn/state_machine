# standard library imports
from datetime import datetime, UTC
from os import environ, _Environ
import subprocess
from typing import Optional


# repository imports
from state_machine import AbstractRepository
from repository.shell.delimited import SpaceDelimited


class Command(AbstractRepository):
    """
    Base class for executing command line actions.
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
    ) -> subprocess.CompletedProcess[str]:
        """
        Executes the command line action.

        raises:
            Exception: If exit code is not zero.
        """
        start_time = datetime.now(UTC)
        cls.logger.debug(f"  {command} - Started")

        result = subprocess.run(
            command.get_secret_value(),
            capture_output=True,
            env=env,
            cwd=cwd,
            text=True,
            start_new_session=start_new_session,
            input=input,
        )

        end_time = datetime.now(UTC)
        if result.returncode != 0:
            cls.logger.debug(
                f"  {command} - Error: {result.returncode} - Runtime: {end_time - start_time}"
            )
            raise Exception(result.stderr)

        cls.logger.debug(f"  {command} - Completed - Runtime: {end_time - start_time}")

        return result
