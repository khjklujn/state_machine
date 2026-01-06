# third party imports
from pydantic import Field

# application imports
from state_machine import BaseState


class StateArchiveEncrypted(BaseState):
    """
    State variables for MachineArchiveEncrypted.
    """

    source_path: str = Field(frozen=True)
    """The path to the source file to be archived and encrypted."""

    staging_folder: str = Field(frozen=True)
    """The path to the staging folder where the file will be copied and encrypted."""

    archive_folder: str = Field(frozen=True)
    """The path to the archive folder where the encrypted file will be moved."""

    gpg_key_name: str = Field(frozen=True)
    """The name of the GPG public key to use for encryption."""
