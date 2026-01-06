# repository imports
from repository.file_manager import FileManager
from repository.gpg import Gpg

# application imports
from state_machine import BaseDependency


class DependencyArchiveEncrypted(BaseDependency):
    """
    Repository dependencies for MachineArchiveEncrypted.
    """

    ensure_staging_directory = FileManager.make_dir_if_not_exists
    copy_to_staging = FileManager.copy
    encrypt_file = Gpg.encrypt
    remove_copied_file = FileManager.remove_file_if_exists
    remove_encrypted_file = FileManager.remove_file_if_exists
    ensure_archive_directory = FileManager.make_dir_if_not_exists
    move_to_archive = FileManager.move
    remove_from_archive = FileManager.remove_file_if_exists
