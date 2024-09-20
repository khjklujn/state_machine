# third party imports
import pytest

# application imports
from state_machine.exception.documentation import (
    MissingDocStringError,
    MissingOverviewError,
)
from state_machine.decorator import node, no_exceptions
from state_machine import Exit, Success, Transition


def test_node_entry_node_doc_string():
    @no_exceptions
    @node
    def func() -> Transition:
        """
        overview:
            Yo.

        is_entry: True

        happy_paths:
            - happy
        unhappy_paths:
            - unhappy
        """
        return Exit(result=Success(node="func"))

    assert func.__is_node__
    assert func.__overview__ == "Yo."
    assert func.__is_entry__
    assert not func.__is_terminal__
    assert func.__happy_paths__ == ["happy"]
    assert func.__unhappy_paths__ == ["unhappy"]
    assert func.__exits__ == ["happy", "unhappy"]
    assert func.__invokes_machine__ == ""
    assert func.__node_name__ == "func"


def test_node_missing_doc_string():
    with pytest.raises(MissingDocStringError):

        @no_exceptions
        @node
        def func() -> Transition:
            return Exit(result=Success(node="func"))


def test_node_missing_overview():
    with pytest.raises(MissingOverviewError):

        @no_exceptions
        @node
        def func() -> Transition:
            """
            oops: mispelled
            """
            return Exit(result=Success(node="func"))


def test_node_terminal_node_doc_string():
    @no_exceptions
    @node
    def func() -> Transition:
        """
        overview:
            Yo.

        is_terminal: True

        invokes_machine: next_machine

        happy_paths:
            - happy
        unhappy_paths:
            - unhappy
        """
        return Exit(result=Success(node="func"))

    assert func.__is_node__
    assert func.__overview__ == "Yo."
    assert not func.__is_entry__
    assert func.__is_terminal__
    assert func.__happy_paths__ == ["happy"]
    assert func.__unhappy_paths__ == ["unhappy"]
    assert func.__exits__ == ["happy", "unhappy"]
    assert func.__invokes_machine__ == "next_machine"
    assert func.__node_name__ == "func"
