# standard library imports
from typing import Callable

# application imports
from state_machine.exception.machine import NotANodeError

# local imports
from ..transition import Transition


def no_exceptions(func: Callable) -> Callable[..., Transition]:
    """
    Indicates the node will not raise exceptions.

    raises:
        NotANodeError: If the function has not been decorated with @node.
    """
    if not hasattr(func, "__is_node__"):
        raise NotANodeError(
            f"{func.__module__.split('.')[-1]}.{func.__name__} is not decorated with @node"
        )

    func.__has_exception_handling__ = False

    return func
