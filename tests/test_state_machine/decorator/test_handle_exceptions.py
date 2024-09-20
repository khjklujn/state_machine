from pprint import pprint

# application imports
import state_machine
from state_machine import BaseState, Transition
from state_machine.decorator import (
    handle_exceptions,
    machine,
    no_exceptions,
    node,
)
from state_machine.result import Failure, Success

# mock imports
from tests.mocks import MockLogger


def test_handle_exceptions():
    @machine
    class Machine(state_machine.AbstractMachine):
        """
        overview:
            Yo.
        """

        @handle_exceptions(on_exception="unhappy")
        @node
        def entry(self) -> Transition:
            """
            overview:
                Yo.

            is_entry: True

            happy_paths:
                - happy
            unhappy_paths:
                - unhappy
            """
            raise Exception("uh oh")

        @no_exceptions
        @node
        def happy(self) -> Transition:
            """
            overview:
                Yo.

            happy_paths:
                - happier
            unhappy_paths:
                - unhappy
            """
            return self.failure(exit_to=self.unhappy, message="uh oh")

        @no_exceptions
        @node
        def happier(self) -> Transition:
            """
            overview:
                Yo.

            is_terminal: True
            """
            return self.exit()

        @no_exceptions
        @node
        def unhappy(self):
            """
            overview:
                Yo.

            happy_paths:
                - report_results
            """
            return self.success(exit_to=self.report_results)

        @property
        def failure_prefix(self) -> str:
            return "Machine"

        @property
        def state(self) -> BaseState:
            return self._state

    logger = MockLogger()

    test_machine = Machine(logger=logger, state=BaseState())
    results = test_machine.execute()

    assert len(results) == 3
    assert isinstance(results[0], Failure)
    assert results[0].node == "Machine.entry"
    assert results[0].message == "Machine unrecognized exception: uh oh"
    assert isinstance(results[1], Success)
    assert results[1].node == "Machine.unhappy"
