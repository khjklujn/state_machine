class MissingDocStringError(Exception):
    """
    Raised when a node or machine is missing a docstring.
    """


class MissingOverviewError(Exception):
    """
    Raised when a node or machine is missing the overview section in the docstring.
    """


class MissingProcessError(Exception):
    """
    Raised when a node is missing the process section in the docstring.
    """
