"""
Tests for the archive encrypted machine.
"""

# application imports
import service.archive_encrypted.archive_encrypted_machine as archive_encrypted_machine
from service.archive_encrypted.archive_encrypted_machine import (
    MachineArchiveEncrypted,
)
from service.archive_encrypted.dependency_archive_encrypted import (
    DependencyArchiveEncrypted,
)
from service.archive_encrypted.state_archive_encrypted import StateArchiveEncrypted
from state_machine import BaseDependency, Success, Failure

# mock imports
from tests.mocks import MockLogger


class MockBasic:
    """
    Basic mock utilities for testing.
    """

    @classmethod
    def success(cls, **kwargs):
        """The mocked function succeeded and had nothing to return."""
        pass

    @classmethod
    def failure(cls, **kwargs):
        """The mocked function failed."""
        raise Exception("unit test failure")


def create_machine(
    source_path: str = "/source/file.txt",
    staging_folder: str = "/staging",
    archive_folder: str = "/archive",
    gpg_key_name: str = "test_key",
) -> MachineArchiveEncrypted:
    """
    Create a machine for testing.
    """
    logger = MockLogger()

    return MachineArchiveEncrypted(
        logger=logger,
        state=StateArchiveEncrypted(
            source_path=source_path,
            staging_folder=staging_folder,
            archive_folder=archive_folder,
            gpg_key_name=gpg_key_name,
        ),
    )


def get_mocks() -> DependencyArchiveEncrypted:
    """
    Mock the repository dependencies for the machine.
    """

    class DependencyMocks(BaseDependency):
        ensure_staging_directory = MockBasic.success
        copy_to_staging = MockBasic.success
        encrypt_file = MockBasic.success
        remove_copied_file = MockBasic.success
        remove_encrypted_file = MockBasic.success
        ensure_archive_directory = MockBasic.success
        move_to_archive = MockBasic.success
        remove_from_archive = MockBasic.success

    return DependencyMocks  # pyright: ignore


def test_happy_path(monkeypatch):
    """Test the happy path."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        patch.setattr(
            archive_encrypted_machine,
            "DependencyArchiveEncrypted",
            DependencyMocks,
        )

        machine = create_machine()
        results = machine.execute()

        node_order = []
        for result in results:
            assert isinstance(result, Success)
            node_order.append(result.node)

        assert node_order == [
            "MachineArchiveEncrypted.ensure_staging_directory",
            "MachineArchiveEncrypted.copy_to_staging",
            "MachineArchiveEncrypted.encrypt_file",
            "MachineArchiveEncrypted.ensure_archive_directory",
            "MachineArchiveEncrypted.move_to_archive",
            "MachineArchiveEncrypted.report_results",
        ]


def test_ensure_staging_directory_failure(monkeypatch):
    """Test when creation of staging directory fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.ensure_staging_directory = MockBasic.failure
        patch.setattr(
            archive_encrypted_machine,
            "DependencyArchiveEncrypted",
            DependencyMocks,
        )

        machine = create_machine()
        results = machine.execute()

        assert len(results) == 2
        assert isinstance(results[0], Failure)
        assert results[0].node == "MachineArchiveEncrypted.ensure_staging_directory"
        assert isinstance(results[1], Success)
        assert results[1].node == "MachineArchiveEncrypted.report_results"


def test_copy_to_staging_failure(monkeypatch):
    """Test when copying file to staging fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.copy_to_staging = MockBasic.failure
        patch.setattr(
            archive_encrypted_machine,
            "DependencyArchiveEncrypted",
            DependencyMocks,
        )

        machine = create_machine()
        results = machine.execute()

        assert len(results) == 3
        assert isinstance(results[0], Success)
        assert results[0].node == "MachineArchiveEncrypted.ensure_staging_directory"
        assert isinstance(results[1], Failure)
        assert results[1].node == "MachineArchiveEncrypted.copy_to_staging"
        assert isinstance(results[2], Success)
        assert results[2].node == "MachineArchiveEncrypted.remove_copied_file"
        # Should continue to report_results
        assert len(results) >= 3


def test_encrypt_file_failure(monkeypatch):
    """Test when encryption fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.encrypt_file = MockBasic.failure
        patch.setattr(
            archive_encrypted_machine,
            "DependencyArchiveEncrypted",
            DependencyMocks,
        )

        machine = create_machine()
        results = machine.execute()

        node_order = []
        for result in results:
            node_order.append(result.node)

        assert "MachineArchiveEncrypted.ensure_staging_directory" in node_order
        assert "MachineArchiveEncrypted.copy_to_staging" in node_order
        assert "MachineArchiveEncrypted.encrypt_file" in node_order
        # Should rollback
        assert "MachineArchiveEncrypted.remove_copied_file" in node_order
        assert "MachineArchiveEncrypted.report_results" in node_order

        # Check that encrypt_file failed
        failures = [r for r in results if isinstance(r, Failure)]
        assert len(failures) == 1
        assert failures[0].node == "MachineArchiveEncrypted.encrypt_file"


def test_ensure_archive_directory_failure(monkeypatch):
    """Test when creation of archive directory fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.ensure_archive_directory = MockBasic.failure
        patch.setattr(
            archive_encrypted_machine,
            "DependencyArchiveEncrypted",
            DependencyMocks,
        )

        machine = create_machine()
        results = machine.execute()

        node_order = []
        for result in results:
            node_order.append(result.node)

        assert "MachineArchiveEncrypted.ensure_staging_directory" in node_order
        assert "MachineArchiveEncrypted.copy_to_staging" in node_order
        assert "MachineArchiveEncrypted.encrypt_file" in node_order
        assert "MachineArchiveEncrypted.ensure_archive_directory" in node_order
        # Should rollback encrypted and copied files
        assert "MachineArchiveEncrypted.remove_encrypted_file" in node_order
        assert "MachineArchiveEncrypted.remove_copied_file" in node_order
        assert "MachineArchiveEncrypted.report_results" in node_order

        # Check that ensure_archive_directory failed
        failures = [r for r in results if isinstance(r, Failure)]
        assert len(failures) == 1
        assert failures[0].node == "MachineArchiveEncrypted.ensure_archive_directory"


def test_move_to_archive_failure(monkeypatch):
    """Test when moving file to archive fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.move_to_archive = MockBasic.failure
        patch.setattr(
            archive_encrypted_machine,
            "DependencyArchiveEncrypted",
            DependencyMocks,
        )

        machine = create_machine()
        results = machine.execute()

        node_order = []
        for result in results:
            node_order.append(result.node)

        assert "MachineArchiveEncrypted.ensure_staging_directory" in node_order
        assert "MachineArchiveEncrypted.copy_to_staging" in node_order
        assert "MachineArchiveEncrypted.encrypt_file" in node_order
        assert "MachineArchiveEncrypted.ensure_archive_directory" in node_order
        assert "MachineArchiveEncrypted.move_to_archive" in node_order
        # Should rollback encrypted and copied files
        assert "MachineArchiveEncrypted.remove_encrypted_file" in node_order
        assert "MachineArchiveEncrypted.remove_copied_file" in node_order
        assert "MachineArchiveEncrypted.report_results" in node_order

        # Check that move_to_archive failed
        failures = [r for r in results if isinstance(r, Failure)]
        assert len(failures) == 1
        assert failures[0].node == "MachineArchiveEncrypted.move_to_archive"


def test_remove_copied_file_failure(monkeypatch):
    """Test when removing copied file during rollback fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.copy_to_staging = MockBasic.failure
        DependencyMocks.remove_copied_file = MockBasic.failure
        patch.setattr(
            archive_encrypted_machine,
            "DependencyArchiveEncrypted",
            DependencyMocks,
        )

        machine = create_machine()
        results = machine.execute()

        # Should still reach report_results even if cleanup fails
        node_order = [r.node for r in results]
        assert "MachineArchiveEncrypted.report_results" in node_order


def test_remove_encrypted_file_failure(monkeypatch):
    """Test when removing encrypted file during rollback fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.ensure_archive_directory = MockBasic.failure
        DependencyMocks.remove_encrypted_file = MockBasic.failure
        patch.setattr(
            archive_encrypted_machine,
            "DependencyArchiveEncrypted",
            DependencyMocks,
        )

        machine = create_machine()
        results = machine.execute()

        # Should still continue rollback and reach report_results
        node_order = [r.node for r in results]
        assert "MachineArchiveEncrypted.remove_copied_file" in node_order
        assert "MachineArchiveEncrypted.report_results" in node_order
