# third party imports
import pytest

# application imports
from state_machine.exception.documentation import (
    MissingDocStringError,
    MissingOverviewError,
)
from state_machine.exception.machine import (
    NoEntryNodeError,
    NotTerminalNodeError,
    UndefinedNodeError,
    UnreachableNodeError,
)
import state_machine
from state_machine import Transition
from state_machine.decorator import machine, no_exceptions, node


def test_machine_doc_string():
    @machine
    class Machine(state_machine.AbstractMachine):
        """
        overview:
            Yo.
        """

        @no_exceptions
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
            return self.success(exit_to=self.happy)

        @no_exceptions
        @node
        def happy(self) -> Transition:
            """
            overview:
                Yo.

            happy_paths:
                - report_results
            """
            return self.success(exit_to=self.report_results)

        @no_exceptions
        @node
        def unhappy(self) -> Transition:
            """
            overview:
                Yo.

            happy_paths:
                - report_results
            """
            return self.success(exit_to=self.report_results)

    assert Machine.__overview__ == "Yo."


def test_machine_missing_doc_string():
    with pytest.raises(MissingDocStringError):

        @machine
        class Machine(state_machine.AbstractMachine):
            @no_exceptions
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
                return self.success(exit_to=self.happy)

            @no_exceptions
            @node
            def happy(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - report_results
                """
                return self.success(exit_to=self.report_results)

            @no_exceptions
            @node
            def unhappy(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - report_results
                """
                return self.success(exit_to=self.report_results)


def test_machine_missing_overview():
    with pytest.raises(MissingOverviewError):

        @machine
        class Machine(state_machine.AbstractMachine):
            """
            oops: mispelled
            """

            @no_exceptions
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
                return self.success(exit_to=self.happy)

            @no_exceptions
            @node
            def happy(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - report_results
                """
                return self.success(exit_to=self.report_results)

            @no_exceptions
            @node
            def unhappy(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - report_results
                """
                return self.success(exit_to=self.report_results)


def test_machine_not_terminal_node():
    with pytest.raises(NotTerminalNodeError):

        @machine
        class Machine(state_machine.AbstractMachine):
            """
            overview:
                Yo.
            """

            @no_exceptions
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
                return self.success(exit_to=self.happy)

            @no_exceptions
            @node
            def happy(self) -> Transition:
                """
                overview:
                    Yo.

                is_terminal: True

                unhappy_paths:
                    - unhappy
                """
                return self.success(exit_to=self.unhappy)

            @no_exceptions
            @node
            def unhappy(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - report_results
                """
                return self.success(exit_to=self.report_results)


def test_machine_undefined_node():
    with pytest.raises(UndefinedNodeError):

        @machine
        class Machine(state_machine.AbstractMachine):
            """
            overview:
                Yo.
            """

            @no_exceptions
            @node
            def entry(self) -> Transition:
                """
                overview:
                    Yo.

                is_entry: True

                happy_paths:
                    - bob
                unhappy_paths:
                    - unhappy
                """
                return self.success(exit_to=self.happy)

            @no_exceptions
            @node
            def happy(self) -> Transition:
                """
                overview:
                    Yo.

                is_terminal: True
                """
                return self.success(exit_to=self.report_results)

            @no_exceptions
            @node
            def unhappy(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - report_results
                """
                return self.success(exit_to=self.report_results)


def test_machine_unreachable_node():
    with pytest.raises(UnreachableNodeError):

        @machine
        class Machine(state_machine.AbstractMachine):
            """
            overview:
                Yo.
            """

            @no_exceptions
            @node
            def entry(self) -> Transition:
                """
                overview:
                    Yo.

                is_entry: True

                unhappy_paths:
                    - unhappy
                """
                return self.failure(exit_to=self.unhappy, message="uh oh")

            @no_exceptions
            @node
            def happy(self) -> Transition:
                """
                overview:
                    Yo.

                is_terminal: True
                """
                return self.success(exit_to=self.report_results)

            @no_exceptions
            @node
            def unhappy(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - report_results
                """
                return self.success(exit_to=self.report_results)


def test_machine_validation_missing_entry_node():
    with pytest.raises(NoEntryNodeError):

        @machine
        class Machine(state_machine.AbstractMachine):
            """
            overview:
                Yo.
            """

            @no_exceptions
            @node
            def entry(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - happy
                unhappy_paths:
                    - unhappy
                """
                return self.success(exit_to=self.happy)

            @no_exceptions
            @node
            def happy(self) -> Transition:
                """
                overview:
                    Yo.

                is_terminal: True
                """
                return self.success(exit_to=self.report_results)

            @no_exceptions
            @node
            def unhappy(self) -> Transition:
                """
                overview:
                    Yo.

                happy_paths:
                    - report_results
                """
                return self.success(exit_to=self.report_results)
