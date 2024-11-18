# application imports
from state_machine import Logger
from long_term_storage.service.dynamic_mount import (
    MachineDynamicMount,
    StateDynamicMount,
)

# local imports
from .end_point import EndPoint


class DynamicMountingEndPoint(EndPoint):
    """
    Executes a state machine within a dynamic mounting machine.
    """

    def __init__(
        self,
        *,
        logger: Logger,
        state_dynamic_mount: StateDynamicMount,
    ):
        wrapped_machine = MachineDynamicMount(logger=logger, state=state_dynamic_mount)
        super().__init__(logger=logger, machine=wrapped_machine)
