# third party imports
import pytest

# application imports
from state_machine.exception.machine import IllegalTransitionError
import state_machine
from state_machine import BaseState, Transition
from state_machine.decorator import machine, node, no_exceptions

# mock imports
from tests.mocks import MockLogger


def test_no_transition():
    with pytest.raises(IllegalTransitionError):

        @machine
        class Machine(state_machine.AbstractMachine):
            """
            overview:
                Yo.
            """

            @no_exceptions
            @node
            def entry(self) -> Transition:  # pyright: ignore
                """
                overview:
                    Yo.

                is_entry: True

                happy_paths:
                    - happy
                unhappy_paths:
                    - unhappy
                """
                pass

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

        test_machine = Machine(
            logger=logger,
            state=BaseState(),
        )
        test_machine.execute()
