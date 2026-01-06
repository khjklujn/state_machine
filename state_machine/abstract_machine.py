# standard library imports
from datetime import datetime, UTC
import inspect
from traceback import format_exc
from typing import Callable

# application imports
from state_machine.exception.machine import (
    IllegalTransitionError,
    MultipleEntryNodeError,
    NoEntryNodeError,
    NoExceptionHandlingError,
    NoTerminalNodeError,
    NotTerminalNodeError,
    UndefinedNodeError,
    UnreachableNodeError,
)

# local imports
from .decorator import no_exceptions, node
from .base_state import BaseState
from .config import Config
from .logger import Logger
from .result import Failure, Result, Success
from .transition import Exit, Transition


class AbstractMachine:
    """
    Abstract base class for a state-machine.  Expects to have the failure_message and state properties
    overridden in derived classes.
    """

    __entry_nodes__: list[Callable[..., Transition]] = []
    __entry_node__: Callable[..., Transition]
    __named_entry_nodes__: list[str] = []
    __nodes__: list[Callable[..., Transition]] = []
    __named_nodes__: list[str] = []
    __terminal_nodes__: list[Callable[..., Transition]] = []
    __named_terminal_nodes__: list[str] = []
    __overview__: str = ""
    __todo__: str = ""
    __Success__: type[Result] = Success
    __Failure__: type[Result] = Failure

    @classmethod
    def validate(cls):
        """
        Performs validation that the design documentation outlined in the docstrings for the
        nodes are self-consistent.

        Validations:
            - Has an entry-node.
            - Terminal-nodes don't have an exit path.
            - All node methods are reachable.
            - All paths have an implementing node method.
            - Exception handlers route to a failure path.
            - Exception handling is specified for all nodes.

        raises:
            NoEntryNode: If the machine has no entry nodes defined.
            NoTerminalNode: If the machine has no terminal nodes defined.
            UndefinedNode: If the design spec references a node that has no implementation.
            UnreachableNode: If a node is implemented that is not in the design spec.
            NotTerminalNode: If a terminal node has exit paths in the design spec.
            NoExceptionHandling: If a node does not have a decorator specifying whether it should have exception handling.
            IllegalTransition: If an exception path is not an unhappy path for the node.
        """
        # confirm at least one entry node is defined
        if not cls.__entry_nodes__:
            raise NoEntryNodeError(f"No entry nodes {cls.__module__}")

        # Confirm there is only one entry node.
        if len(cls.__entry_nodes__) > 1:
            raise MultipleEntryNodeError(
                f"More than one entry node defined: {cls.__named_entry_nodes__}"
            )

        cls.__entry_node__ = cls.__entry_nodes__[0]

        # confirm at least one terminal node is defined
        if not cls.__terminal_nodes__:
            raise NoTerminalNodeError(f"No terminal nodes {cls.__module__}")

        # collect the definitions of all of the nodes
        all_nodes = cls.__entry_nodes__ + cls.__nodes__ + cls.__terminal_nodes__

        # compile a list of all of the exit paths
        exits = []
        for node in all_nodes:
            for method_name in node.__exits__:
                if not hasattr(cls, method_name):
                    raise UndefinedNodeError(
                        f"{cls.__module__}.{node.__node_name__} references undefined: {method_name}"
                    )
                else:
                    method = getattr(cls, method_name)
                    exits.append(method.__node_name__)

        # check exception handling specifications
        for node in all_nodes:
            if not hasattr(node, "__has_exception_handling__"):
                raise NoExceptionHandlingError(
                    f"Node {cls.__module__}.{node.__node_name__} has neither @handle_exceptions nor @no_exceptions"
                )
            elif (
                node.__has_exception_handling__
                and node.__on_exception__ not in node.__unhappy_paths__
            ):
                raise IllegalTransitionError(
                    f"{cls.__module__}.{node.__node_name__} exception handler not an allowable exit: {node.__on_exception__}"
                )

        for node in all_nodes:
            # confirm all of the nodes in the machine have a path that reaches them
            if not node.__is_entry__ and node.__node_name__ not in exits:
                raise UnreachableNodeError(
                    f"Unreachable node: {cls.__module__}.{node.__node_name__}"
                )

            # confirm the terminal nodes have no exit paths
            if node.__is_terminal__ and node.__exits__:
                raise NotTerminalNodeError(
                    f"Node {cls.__module__}.{node.__node_name__} not terminal"
                )

    def __init__(self, *, logger: Logger, state: BaseState):
        self.logger = logger
        self._state = state

        self.results = []

    def execute(
        self,
    ) -> list[Result]:
        """
        Executes the state-machine.  When the environment is set to "dev" in the master config file,
        runtime validation that the behavior of the implementation matches the design specification
        in the docstrings will be performed.

        raises:
            NoEntryNode: If the starting node is not an entry-node.
            IllegalTransition: If a transition is made to a node that is not an exit-path of the current node.
            IllegalTransition: If a Success result is sent down an unhappy-path.
            IllegalTransition: If a Failure result is sent down a happy-path.
            IllegalTransition: If no transition is provided and the node is not a terminal-node.
        """
        machine_start_time = datetime.now(UTC)
        self.logger.info(f"{self.__class__.__name__.split('.')[-1]} started")

        # Set the first node to be executed.
        self._current_node = self.__entry_node__

        # Run until a terminal node is executed.
        while True:
            # Record the last node executed.
            previous_node = self._current_node

            # Execute the current node.
            node_start_time = datetime.now(UTC)
            self.logger.debug(
                f"{self.__class__.__name__.split('.')[-1]}.{self._current_node.__node_name__} started"
            )
            transition = self._current_node()
            self.logger.debug(
                f"{self.__class__.__name__.split('.')[-1]}.{self._current_node.__node_name__} completed runtime: {datetime.now(UTC) - node_start_time}"
            )

            # Confirm the node returned a Transition.
            if __debug__ and not isinstance(transition, Transition):
                raise IllegalTransitionError(
                    f"{self._current_node} did not return a Transition: instead returned {type(transition)}"
                )

            # Exit machine if the node is terminal.
            if isinstance(transition, Exit):
                if self._current_node.__exits__:
                    raise NotTerminalNodeError(
                        f"{self.node_name} returned Exit but is not a terminal node."
                    )
                else:
                    self.results.append(transition.result)
                    break

            self._current_node = transition.exit_to

            # Can the transition be made?
            if (
                __debug__
                and previous_node
                and self._current_node.__node_name__ not in previous_node.__exits__
            ):
                raise IllegalTransitionError(
                    f"{previous_node.__node_name__} cannot transition to {self._current_node.__node_name__}"
                )

            # Is a Failure being sent down a happy path?
            if (
                __debug__
                and isinstance(transition.result, Failure)
                and previous_node
                and self._current_node.__node_name__
                not in previous_node.__unhappy_paths__
            ):
                raise IllegalTransitionError(
                    f"{previous_node.__node_name__} made an unhappy transition on the happy path to {self._current_node.__node_name__}"
                )

            # Is a Success being sent down an unhappy path?
            if (
                __debug__
                and isinstance(transition.result, Success)
                and previous_node
                and self._current_node.__node_name__
                not in previous_node.__happy_paths__
            ):
                raise IllegalTransitionError(
                    f"{previous_node.__node_name__} made an happy transition on the unhappy path to {self._current_node.__node_name__}"
                )

            self.results.append(transition.result)

        machine_end_time = datetime.now(UTC)
        machine_run_time = machine_end_time - machine_start_time
        self.logger.info(
            f"{self.__class__.__name__.split('.')[-1]} completed runtime: {machine_run_time}"
        )

        return self.results

    def exception(
        self,
        *,
        exit_to: Callable[..., Transition],
        exception: Exception,
    ) -> Transition:
        """
        Returns a failure Transition to *exit_to*.

        raises:
            IllegalTransition: If *exit_to* is not a node.
        """
        if (
            __debug__
            and not inspect.ismethod(exit_to)
            and not hasattr(exit_to, "__is_node__")
        ):
            raise IllegalTransitionError(f"{exit_to} is not a node")

        self.logger.error(f"{self.node_name} {self.failure_prefix}  {exception}")
        self.logger.error(f"{self.node_name} {self.failure_prefix}  {format_exc()}")

        return Transition(
            result=Failure(
                node=self.node_name,
                message=f"{self.failure_prefix} unrecognized exception: {exception}",
            ),
            exit_to=exit_to,
        )

    def exit(self) -> Transition:
        """
        Exits the state-machine.
        """

        return Exit(result=self.__Success__(node=self.node_name))

    def failure(
        self,
        *,
        exit_to: Callable[..., Transition],
        message: str,
    ) -> Transition:
        """
        Returns a failure Transition to *exit_to*.

        raises:
            IllegalTransition: If *exit_to* is not a bound method.
        """
        if (
            __debug__
            and not inspect.ismethod(exit_to)
            and not hasattr(exit_to, "__is_node__")
        ):
            raise IllegalTransitionError(f"failure transition {exit_to} is not a node")

        self.logger.error(f"{self.node_name} {self.failure_prefix}  {message}")

        return Transition(
            result=Failure(
                node=self.node_name,
                message=f"{self.failure_prefix} {message}",
            ),
            exit_to=exit_to,
        )

    @no_exceptions
    @node
    def report_results(self) -> Transition:
        """
        overview:
            The final exit node for all state-machines.

        is_terminal: True
        """
        return self.exit()

    def success(self, *, exit_to: Callable[..., Transition]) -> Transition:
        """
        Returns a successful Transition to *exit_to*.

        raises:
            - IllegalTransition: If *exit_to* is not a bound method.
        """
        if (
            __debug__
            and not inspect.ismethod(exit_to)
            and not hasattr(exit_to, "__is_node__")
        ):
            raise IllegalTransitionError(f"success transition {exit_to} is not a node")

        return Transition(result=self.__Success__(node=self.node_name), exit_to=exit_to)

    @property
    def failure_prefix(self) -> str:
        """A message to be prepended to the failure reporting messages."""
        raise NotImplementedError()

    @property
    def node_name(self) -> str:
        """The name of the method implementing the node."""
        return f"{self.__class__.__name__.split('.')[-1]}.{self._current_node.__node_name__}"

    @property
    def state(self) -> BaseState:
        """The machine's state object."""
        raise NotImplementedError()
