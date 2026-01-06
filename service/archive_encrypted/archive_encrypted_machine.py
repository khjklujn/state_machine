# standard library imports
import os

# application imports
from state_machine.decorator import handle_exceptions, machine, node
from state_machine import AbstractMachine, Transition

# local imports
from .state_archive_encrypted import StateArchiveEncrypted
from .dependency_archive_encrypted import DependencyArchiveEncrypted


@machine
class MachineArchiveEncrypted(AbstractMachine):
    """
    overview: |+
        Archive a file by copying it to a staging folder, encrypting it using GPG,
        and moving the encrypted file to an archive folder.

        The steps to perform this are:

        1. Ensure the staging directory exists.
        2. Copy the source file to the staging folder.
        3. Encrypt the file in the staging folder using GPG.
        4. Ensure the archive directory exists.
        5. Move the encrypted file from staging to the archive folder.
        6. Report the Success/Failure outcomes back to where ever it was called from.

        The sequence diagram for the happy-path life cycle is presented below:

        ``` mermaid
        sequenceDiagram
          autonumber
          Caller->>MachineArchiveEncrypted: start
          MachineArchiveEncrypted->>FileManager: ensure_staging_directory
          FileManager->>MachineArchiveEncrypted: directory created
          MachineArchiveEncrypted->>FileManager: copy_to_staging
          FileManager->>MachineArchiveEncrypted: file copied
          MachineArchiveEncrypted->>GPG: encrypt_file
          GPG->>MachineArchiveEncrypted: file encrypted
          MachineArchiveEncrypted->>FileManager: ensure_archive_directory
          FileManager->>MachineArchiveEncrypted: directory created
          MachineArchiveEncrypted->>FileManager: move_to_archive
          FileManager->>MachineArchiveEncrypted: file moved
          MachineArchiveEncrypted->>Caller: report_results
        ```

        The state flow diagram showing all nodes and transitions is presented below:

        ``` mermaid
        stateDiagram-v2
            [*] --> ensure_staging_directory
            ensure_staging_directory --> copy_to_staging: success
            ensure_staging_directory --> report_results: failure
            copy_to_staging --> encrypt_file: success
            copy_to_staging --> remove_copied_file: failure
            encrypt_file --> ensure_archive_directory: success
            encrypt_file --> remove_copied_file: failure
            ensure_archive_directory --> move_to_archive: success
            ensure_archive_directory --> remove_encrypted_file: failure
            move_to_archive --> report_results: success
            move_to_archive --> remove_encrypted_file: failure
            remove_copied_file --> report_results: cleanup complete
            remove_encrypted_file --> remove_copied_file: cleanup complete
            report_results --> [*]

            note right of ensure_staging_directory
                Entry node
            end note

            note right of report_results
                Terminal node
            end note

            note right of remove_copied_file
                Rollback node
            end note

            note right of remove_encrypted_file
                Rollback node
            end note
        ```
    """

    @handle_exceptions(on_exception="report_results")
    @node
    def ensure_staging_directory(self) -> Transition:
        """
        overview:
            Ensure the staging directory exists.

        is_entry: True

        happy_paths:
            - copy_to_staging

        unhappy_paths:
            - report_results
        """
        DependencyArchiveEncrypted(logger=self.logger).ensure_staging_directory(
            path=self.state.staging_folder
        )

        return self.success(exit_to=self.copy_to_staging)

    @handle_exceptions(on_exception="remove_copied_file")
    @node
    def copy_to_staging(self) -> Transition:
        """
        overview:
            Copy the source file to the staging folder.

        happy_paths:
            - encrypt_file

        unhappy_paths:
            - remove_copied_file
        """
        source_filename = os.path.basename(self.state.source_path)
        staging_file_path = os.path.join(self.state.staging_folder, source_filename)

        DependencyArchiveEncrypted(logger=self.logger).copy_to_staging(
            from_path=self.state.source_path, to_path=staging_file_path
        )

        return self.success(exit_to=self.encrypt_file)

    @handle_exceptions(on_exception="remove_copied_file")
    @node
    def encrypt_file(self) -> Transition:
        """
        overview:
            Encrypt the file in the staging folder using GPG.

        happy_paths:
            - ensure_archive_directory

        unhappy_paths:
            - remove_copied_file
        """
        source_filename = os.path.basename(self.state.source_path)
        staging_file_path = os.path.join(self.state.staging_folder, source_filename)
        encrypted_file_path = os.path.join(
            self.state.staging_folder, f"{source_filename}.gpg"
        )

        DependencyArchiveEncrypted(logger=self.logger).encrypt_file(
            key_name=self.state.gpg_key_name,
            from_file=staging_file_path,
            to_file=encrypted_file_path,
        )

        return self.success(exit_to=self.ensure_archive_directory)

    @handle_exceptions(on_exception="remove_encrypted_file")
    @node
    def ensure_archive_directory(self) -> Transition:
        """
        overview:
            Ensure the archive directory exists.

        happy_paths:
            - move_to_archive

        unhappy_paths:
            - remove_encrypted_file
        """
        DependencyArchiveEncrypted(logger=self.logger).ensure_archive_directory(
            path=self.state.archive_folder
        )

        return self.success(exit_to=self.move_to_archive)

    @handle_exceptions(on_exception="remove_encrypted_file")
    @node
    def move_to_archive(self) -> Transition:
        """
        overview:
            Move the encrypted file from staging to the archive folder.

        happy_paths:
            - report_results

        unhappy_paths:
            - remove_encrypted_file
        """
        source_filename = os.path.basename(self.state.source_path)
        encrypted_file_name = f"{source_filename}.gpg"
        staging_encrypted_path = os.path.join(
            self.state.staging_folder, encrypted_file_name
        )
        archive_encrypted_path = os.path.join(
            self.state.archive_folder, encrypted_file_name
        )

        DependencyArchiveEncrypted(logger=self.logger).move_to_archive(
            from_path=staging_encrypted_path, to_path=archive_encrypted_path
        )

        return self.success(exit_to=self.report_results)

    @handle_exceptions(on_exception="report_results")
    @node
    def remove_copied_file(self) -> Transition:
        """
        overview:
            Remove the copied file from staging (on error path after copy or encrypt failure).

        happy_paths:
            - report_results

        unhappy_paths:
            - report_results
        """
        source_filename = os.path.basename(self.state.source_path)
        staging_file_path = os.path.join(self.state.staging_folder, source_filename)

        DependencyArchiveEncrypted(logger=self.logger).remove_copied_file(
            path=staging_file_path
        )

        return self.success(exit_to=self.report_results)

    @handle_exceptions(on_exception="remove_copied_file")
    @node
    def remove_encrypted_file(self) -> Transition:
        """
        overview:
            Remove the encrypted file from staging (on error path after encryption, archive directory, or move failure).

        happy_paths:
            - remove_copied_file

        unhappy_paths:
            - remove_copied_file
        """
        source_filename = os.path.basename(self.state.source_path)
        encrypted_file_path = os.path.join(
            self.state.staging_folder, f"{source_filename}.gpg"
        )
        # Also check if file was partially moved to archive and remove it from there
        archive_encrypted_path = os.path.join(
            self.state.archive_folder, f"{source_filename}.gpg"
        )

        DependencyArchiveEncrypted(logger=self.logger).remove_encrypted_file(
            path=encrypted_file_path
        )
        DependencyArchiveEncrypted(logger=self.logger).remove_from_archive(
            path=archive_encrypted_path
        )

        return self.success(exit_to=self.remove_copied_file)

    @handle_exceptions(on_exception="report_results")
    @node
    def report_results(self) -> Transition:
        """
        overview:
            Report the Success/Failure outcomes.

        is_terminal: True
        """
        return self.success(exit_to=self.exit)
