# standard library imports
import inspect

# third party imports
from ruamel.yaml import YAML

# applicaiton imports
from state_machine.exception.documentation import (
    MissingDocStringError,
    MissingOverviewError,
)

# local imports
from ..result import Success, Failure


def machine(cls: type) -> type:
    """
    Compiles meta information and performs a sanity check on a state-machine definition.

    raises:
        MissingDocStringError: If the docstring is not defined.
        MissingOverviewError: If the overview section of the docstring is missing.
    """

    # confirm doc string exists
    if __debug__ and not cls.__doc__:
        raise MissingDocStringError(f"Missing doc string {cls.__module__}")

    # assign the Success type for the machine
    cls.__Success__ = Success

    # assign the Failure type for the machine
    cls.__Failure__ = Failure

    # the allowable starting nodes for execution
    cls.__entry_nodes__ = []
    cls.__named_entry_nodes__ = []

    # the nodes that represent the end of execution
    cls.__terminal_nodes__ = []
    cls.__named_terminal_nodes__ = []

    # the nodes the machine contains
    cls.__nodes__ = []
    cls.__named_nodes__ = []

    # the state variables the machine contains
    cls.__states__ = []

    # extract the specifications from the doc string
    yaml = YAML()
    doc = yaml.load(cls.__doc__)

    # general description of what the state-machine does
    cls.__overview__ = doc.get("overview", "")
    if __debug__ and not cls.__overview__:
        raise MissingOverviewError(
            f"No overview documentation provided for {cls.__name__}"
        )

    # get any todo notes
    cls.__todo__ = doc.get("todo", "")

    # compile the distribution of the node methods
    for method_name, _ in inspect.getmembers(cls):
        method = getattr(cls, method_name)
        if hasattr(method, "__is_node__"):
            if method.__is_entry__:
                cls.__entry_nodes__.append(method)
                cls.__named_entry_nodes__.append(method.__node_name__)
            if method.__is_terminal__:
                cls.__terminal_nodes__.append(method)
                cls.__named_terminal_nodes__.append(method.__node_name__)
            if not method.__is_entry__ and not method.__is_terminal__:
                cls.__nodes__.append(method)
                cls.__named_nodes__.append(method.__node_name__)

    if __debug__:
        # perform a sanity check on the state-machine definition
        cls.validate()

    return cls
