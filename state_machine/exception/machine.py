class IllegalTransitionError(Exception):
    """
    Raised when a node tries to make a transition the design says it shouldn't.
    """


class MultipleEntryNodeError(Exception):
    """
    Raised when a machine has more than one entry-node.
    """


class NoEntryNodeError(Exception):
    """
    Raised when a machine has no entry-nodes, or the first node to be executed is not an entry-node.
    """


class NoExceptionHandlingError(Exception):
    """
    Raised when a node is not decorated with either @handle_exceptions or @no_exceptions.
    """


class NotANodeError(Exception):
    """
    Raised when a method is decorated with @handle_exceptions but not with @node.
    """


class NoTerminalNodeError(Exception):
    """
    Raised when a machine has no terminal-nodes.
    """


class NotTerminalNodeError(Exception):
    """
    Raised when a node exits with None but is not a terminal-node.
    """


class UndefinedNodeError(Exception):
    """
    Raised when a node in the design specification has no implementation.
    """


class UnreachableNodeError(Exception):
    """
    Raised when a non-entry node is not an exit path for any other nodes.
    """


class OverrideError(Exception):
    """
    Raised when a method name will override functionality in the base class.
    """
