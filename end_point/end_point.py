# standard library imports
from traceback import format_exc

# application imports
from state_machine import Logger
from state_machine import Failure, AbstractMachine

# local imports
from .dependency_end_point import DependencyEndPoint


class EndPoint:
    """
    Wrapper around a state machine to execute the machine and report failures to stdout.
    """

    def __init__(
        self,
        *,
        logger: Logger,
        machine: AbstractMachine,
    ):
        self._logger = logger
        self._machine = machine

    def execute(self):
        """
        Executes the machine, filters any failures, reports failures on stdout, and exits with the status of the number of failures.
        """
        try:
            self._results = self.machine.execute()

            self._failures = [
                result for result in self._results if isinstance(result, Failure)
            ]

            for failure in self._failures:
                self.logger.error(f"Failure: {failure}")
                DependencyEndPoint(logger=self.logger).execute_write_to_stdout(
                    content=f"Failure: {failure}"
                )

            DependencyEndPoint(logger=self.logger).execute_exit(
                result=len(self._failures)
            )
        except Exception as exception:
            self.logger.critical(f"Critical exception: {format_exc()}")
            DependencyEndPoint(logger=self.logger).execute_write_to_stdout(
                content=f"Critical failure: {exception}"
            )
            DependencyEndPoint(logger=self.logger).execute_exit(result=1)

    @property
    def logger(self):
        return self._logger

    @property
    def machine(self):
        return self._machine
