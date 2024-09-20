# standard library imports
from typing import Any, Callable

# application imports
from state_machine.exception.machine import NotANodeError

# local imports
from ..transition import Transition


def handle_exceptions(*, on_exception: str) -> Callable:
    """
    Wraps a node that may raise exceptions in a try block with the failure exiting
    to the node specified in *on_exception*.

    raises:
        NotANodeError: If the function has not been decorated with @node.
    """

    def wrapper(func: Callable[..., Transition]) -> Callable[..., Transition]:
        if not hasattr(func, "__is_node__"):
            raise NotANodeError(
                f"{func.__module__.split('.')[-1]}.{func.__name__} is not decorated with @node"
            )

        def try_(self: Any) -> Transition:
            try:
                return func(self)
            except Exception as exception:
                exit_to = getattr(self, on_exception)
                return self.exception(
                    exit_to=exit_to,
                    exception=exception,
                )

        # Copy documentation and validation information to the wrapping function.
        try_.__node_name__ = func.__node_name__
        try_.__is_node__ = func.__is_node__
        try_.__is_entry__ = func.__is_entry__
        try_.__is_terminal__ = func.__is_terminal__
        try_.__overview__ = func.__overview__
        try_.__happy_paths__ = func.__happy_paths__
        try_.__unhappy_paths__ = func.__unhappy_paths__
        try_.__exits__ = func.__exits__
        try_.__invokes_machine__ = func.__invokes_machine__
        try_.__on_exception__ = on_exception
        try_.__has_exception_handling__ = True

        return try_

    return wrapper
