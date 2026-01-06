# repository imports
from long_term_storage.repository.process import Process

# application imports
from state_machine import BaseDependency


class DependencyEndPoint(BaseDependency):
    """The repository dependencies for executing an end-point."""

    execute_write_to_stdout = Process.write_to_stdout
    execute_exit = Process.exit
