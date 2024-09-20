# third party imports
from typing import Callable

# third party imports
from ruamel.yaml import YAML

# applicaiton imports
from state_machine.exception.documentation import (
    MissingDocStringError,
    MissingOverviewError,
)
from state_machine.exception.machine import OverrideError

# local imports
from ..transition import Transition


def node(func: Callable[..., Transition]) -> Callable[..., Transition]:
    """
    Provides meta information neccessary for performing sanity checks on state-machine definitions.

    raises:
        MissingDocStringError: If the docstring is missing from the node.
        MissingOverviewError: If the overview section is not present in the docstring.
        MissingProcessError: If the process section is not present in the docstring.
    """

    # Make sure the name does not override base functionality.
    reserved_method_names = (
        "validate",
        "excetion",
        "exit",
        "failure",
        "execute",
        "success",
        "failure_prefix",
        "logger",
        "master_config",
        "my_config",
        "node_name",
        "state",
    )
    if func.__name__ in reserved_method_names:
        raise OverrideError(
            f"{func.__name__} is a reserved method name and cannot be used as a node name"
        )

    # Confirm doc string exists.
    if not func.__doc__:
        raise MissingDocStringError(f"Missing doc string {func.__name__}")

    # Get the name of the node for convenient future reference.
    func.__node_name__ = func.__name__

    # Label the method as a node.
    func.__is_node__ = True

    # Extract the specifications for the node from the doc string.
    yaml = YAML()
    doc = yaml.load(func.__doc__)

    # Find out whether the node is an entry node.
    func.__is_entry__ = doc.get("is_entry", False)

    # Find out whether the node is a terminal node.
    func.__is_terminal__ = doc.get("is_terminal", False)

    # General description of what the node does.
    func.__overview__ = doc.get("overview", "")
    if not func.__overview__:
        raise MissingOverviewError(
            f"No overview documentation provided for {func.__name__}"
        )

    # Get the happy paths.
    func.__happy_paths__ = doc.get("happy_paths", [])

    # Get the unhappy paths.
    func.__unhappy_paths__ = doc.get("unhappy_paths", [])

    # Compile the allowable exits.
    func.__exits__ = func.__happy_paths__ + func.__unhappy_paths__

    # Record whether the node executes another state-machine.
    func.__invokes_machine__ = doc.get("invokes_machine", "")

    return func
