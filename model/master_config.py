# third party imports
from pydantic import BaseModel

# application imports
from state_machine import LoggerModel


class MachineBackupDatabasesModel(BaseModel):
    """Configurations for MachineBackupDatabases."""

    worker_pool_size: int
    """The size of the worker pool for backing up databases in parallel."""


class DeletionCandidatesModel(BaseModel):
    """Configurations for deletion candidate machines."""

    worker_pool_size: int
    """The number of workers for deleting files in parallel."""


class MasterConfigModel(LoggerModel):
    """Configurations in the Master Config file."""

    machine_backup_databases: MachineBackupDatabasesModel
    """Configurations for MachineBackupDatabases."""

    machine_eom_deletion_candidates: DeletionCandidatesModel
    """Configurations for MachineEomDeletionCandidates."""

    machine_eoy_deletion_candidates: DeletionCandidatesModel
    """Configurations for MachineEoyDeletionCandidates."""
