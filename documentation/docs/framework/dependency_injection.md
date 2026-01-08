# Dependency Injection

When one class depends on functionality provided by another class, that's known as a "dependency".

Dependency Injection[^1] is a way of organizing code such that dependencies between classes are not hard-coded.  The reason for doing this is there are situations where you want the code to behave differently in different runtime settings, and you need a way of changing how the methods behave without changing how the methods are defined.

[^1]:
    Usage of dependency injection in Python code bases predates the term "dependency injection" by about a decade, so within Python projects you will often find references to "monkey patching", because that's what Python people called it before the Java people came up with the term "dependency injection".

Now for the complicating factor.  Not all dependencies between classes should necesarrily be managed using dependency injection.  The purpose of dependency injection is to increase reliability and maintainability of the code base.  However, if you adopt a blanket "all dependencies will be injected" rule, your code base will quickly devolve into unreadability, which will totally destroy the reliability and maintainability you were hoping to achieve.

Within this framework, functionality that relies on systems that are external to the application (Repositories) will be accessed using dependency injection.  If it is functionality that can fail for reasons that are outside the control of the application's code, it should probably be accessed using dependency injection.

Far and away, the biggest use case for dependency injection is unit testing.  The "unit" in unit testing is a single class.  We don't want a unit test to also test all of the class's dependency classes--especially if one of those classes is doing something like "delete database".  The functionality in the dependency classes will be tested with their own unit tests.

To allow us to do this, we provide a mechanism that allows classes to fetch the functionality they need from other classes, but is also convenient for instructing the class to fetch the functionality from a different place.

In this framework, we are using dependency mapping classes.  They are data classes where the properties of the class are methods to be called.

Looking at an example:

```python linenums="1"
# repository imports
from repository.file_manager import FileManager
from repository.gpg import Gpg
from repository.shell import PgDump, Tar

# application imports
from state_machine import BaseDependency


class DependencyBackupAndEncrypt(BaseDependency):
    """
    Repository dependencies for MachineBackupAndEncrypt.
    """

    create_intermediate_directory = FileManager.make_dir_if_not_exists
    remove_intermediate_directory = FileManager.remove_directory_if_exists
    create_pg_dump_directory = FileManager.make_dir_if_not_exists
    remove_pg_dump_directory = FileManager.remove_directory_if_exists
    backup_schema = PgDump.dump_schema
    remove_schema_file = FileManager.remove_file_if_exists
    backup_data = PgDump.dump_data
    remove_data_file = FileManager.remove_file_if_exists
    compress = Tar.cjf_with_removal
    remove_tarball = FileManager.remove_file_if_exists
    encrypt = Gpg.encrypt
    remove_encrypted_backup = FileManager.remove_file_if_exists
    create_storage_directory = FileManager.make_dir_if_not_exists
    move_backup = FileManager.move
```

This dependency mapper is used by the backup-and-encrypt state-machine to access functionality that resides in the Repository layer.

The pattern is:

- Import the Repositories the Service needs.
- For each node in the state-machine, create a property named after the node and assign it the Repository method the node needs to call.

Dependency classes all inherit from BaseDependency.

```python linenums="1"
# standard library import
from dataclasses import dataclass
from typing import Any

# local imports
from .abstract_repository import AbstractRepository
from .config import Config
from .logger import Logger


@dataclass
class BaseDependency:
    """
    Base class for representing repository dependencies used by machines.
    """

    logger: Logger
    """Access to the logger."""

    def __getattribute__(self, name: str) -> Any:
        """
        Provides introspective magic to inject the logger into a repository at the time
        at the time the repository is accessed.
        """
        attribute = super().__getattribute__(name)
        if hasattr(attribute, "__self__") and issubclass(
            attribute.__self__, AbstractRepository
        ):
            attribute.__self__.logger = self.logger

        return attribute
```

A dependency class will be instantiated with the application logger (the @dataclass decorator automagically builds a constructor that will have parameters for populating the instance variables).

The \_\_getattribute\_\_ method is technically called a Nasty Bit Of Hackery.  \_\_getattribute\_\_ is a built-in method for classes that controls the behavior of what happens when a "." is used to fetch something from a class.  In this case, the behavior was overriden to check to see if the attribute value is something that belongs to a class that was derived from AbstractRepository, and, if so, make sure the application logger is available to the class the attribute value belongs to.

Looking at an example of how the dependency mapper is used in the Service layer:

```python linenums="32"
    @handle_exceptions(on_exception="remove_intermediate_directory")
    @node
    def create_intermediate_directory(self) -> Transition:
        """
        overview:
            Create the intermediate directory for pulling the backup.

        is_entry: True

        happy_paths:
            - create_pg_dump_directory

        unhappy_paths:
            - remove_intermediate_directory
        """
        DependencyBackupAndEncrypt(logger=self.logger).create_intermediate_directory(
            path=Path.intermediate_backup_base(
                client_name=self.state.client_name, database_name=self.state.database
            )
        )

        return self.success(exit_to=self.create_pg_dump_directory)
```

Line 47 is where the dependency mapper is being used.  What's happening is:

- We instantiate the DependencyBackupAndEncrypt supplying the application logger as the constructor parameter.
- We fetch the create_intermediate_directory property, which is referring to the FileManager.make_dir_if_not_exists method.
- When the executing code hits the "." between DependencyBackupAndEncrypt and create_intermediate_directory, \_\_getattribute\_\_, inherited from BaseDependency, will be called, and finding that FileManager is a decendent of AbstractRepository, it will inject the logger into FileManager.
- The parenthetical construct following create_intermediate_directory indicates we want to call whatever was returned as a value for create_intermediate_directory (the FileManager.make_dir_if_not_exists method).
- FileManager.make_dir_if_not_exists is called with the provided parameters.

We name the property in the dependency mapper after the node it is used in because that makes it easier to keep track of what should be used where in both the implementation and the tests.

We do not put docstrings on the properties in the dependency mapper.  IDEs are smart enough to recognized this level of indirection, so the hovering on "create_intermediate_directory" in the IDE will display the help information for FileManager.make_dir_if_not_exists.

Now, I know this probably looks terribly convoluted, so let's look at the reason things are structured this way.

Here is the unit test for the backup-and-encrypt state-machine.

```python linenums="1"
"""
Tests the backup and encrypt cod flow.
"""

# application import
from service.backup.backup_and_encrypt import (
    machine_backup_and_encrypt,
    DependencyBackupAndEncrypt,
)
from state_machine import BaseDependency, Success

# mock imports
from tests.mocks import MockBasic

# testing imports
from tests.service.failure_asserts import failure_asserts

# local imports
from .create_machine import create_machine


def get_mocks() -> DependencyBackupAndEncrypt:
    """
    Mock the repository dependencies for the machine.
    """

    class DependencyMocks(BaseDependency):
        create_intermediate_directory = MockBasic.success
        remove_intermediate_directory = MockBasic.success
        create_pg_dump_directory = MockBasic.success
        remove_pg_dump_directory = MockBasic.success
        backup_schema = MockBasic.success
        remove_schema_file = MockBasic.success
        backup_data = MockBasic.success
        remove_data_file = MockBasic.success
        compress = MockBasic.success
        remove_tarball = MockBasic.success
        encrypt = MockBasic.success
        remove_encrypted_backup = MockBasic.success
        create_storage_directory = MockBasic.success
        move_backup = MockBasic.success

    return DependencyMocks  # pyright: ignore


def test_happy_path(monkeypatch):
    """Test the happy path."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        machine = create_machine(2)

        results = machine.execute()

        node_order = []
        for result in results:
            assert isinstance(result, Success)
            node_order.append(result.node)

        assert node_order == [
            "MachineBackupAndEncrypt.create_intermediate_directory",
            "MachineBackupAndEncrypt.create_pg_dump_directory",
            "MachineBackupAndEncrypt.backup_schema",
            "MachineBackupAndEncrypt.backup_data",
            "MachineBackupAndEncrypt.compress",
            "MachineBackupAndEncrypt.encrypt",
            "MachineBackupAndEncrypt.create_storage_directory",
            "MachineBackupAndEncrypt.move_backup",
            "MachineBackupAndEncrypt.remove_encrypted_backup",
            "MachineBackupAndEncrypt.remove_tarball",
            "MachineBackupAndEncrypt.remove_data_file",
            "MachineBackupAndEncrypt.remove_schema_file",
            "MachineBackupAndEncrypt.remove_pg_dump_directory",
            "MachineBackupAndEncrypt.remove_intermediate_directory",
            "MachineBackupAndEncrypt.report_results",
        ]


def test_create_intermedite_failure(monkeypatch):
    """Test when creation of the intermediate directory fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.create_intermediate_directory = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=3,
            failing_node=0,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_create_pg_dump_directory_failure(monkeypatch):
    """Test when the creation of the pg_dump directory fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.create_pg_dump_directory = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=5,
            failing_node=1,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_backup_schema_failure(monkeypatch):
    """Test when backing up the schema fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.backup_schema = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=7,
            failing_node=2,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_backup_data_failure(monkeypatch):
    """Test when backing up the data fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.backup_data = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=9,
            failing_node=3,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_compress_failure(monkeypatch):
    """Test when tarring the backups fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.compress = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=11,
            failing_node=4,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_encrypt_failure(monkeypatch):
    """Test when encrypting the tarball fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.encrypt = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=13,
            failing_node=5,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_create_storage_directory_failure(monkeypatch):
    """Test when creating the long-term storage directory fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.create_storage_directory = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=14,
            failing_node=6,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_move_backup_failure(monkeypatch):
    """Test when moving encrypted file from intermediate to long-term storage fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.move_backup = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=15,
            failing_node=7,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_remove_encrypted_backup_failure(monkeypatch):
    """Test when removing intermediate encrypted backup fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.remove_encrypted_backup = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=15,
            failing_node=8,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_remove_tarball_failure(monkeypatch):
    """Test when removing the tarball fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.remove_tarball = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=15,
            failing_node=9,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_remove_data_file_failure(monkeypatch):
    """Test when removing the data backup file fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.remove_data_file = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=15,
            failing_node=10,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_remove_schema_file_failure(monkeypatch):
    """Test when removing the schema backup file fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.remove_schema_file = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=15,
            failing_node=11,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_remove_pg_dump_directory_failure(monkeypatch):
    """Test when removing the pg_dump directory fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.remove_pg_dump_directory = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=15,
            failing_node=12,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )


def test_remove_intermediate_directory_failure(monkeypatch):
    """Test when removing the intermediate directory fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.remove_intermediate_directory = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=15,
            failing_node=13,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )
```

We will discuss the structuring of unit tests in a later episode, but I have included the entire test here to emphasize that unit tests do not simply test what you intended the implementation of a class to do.  You also have to confirm you have defined behavior for all of the possible ways the implementation could fail while trying to fulfill its intended purpose.

Getting back to dependency injection, the relevant section is:

```python linenums="22"
def get_mocks() -> DependencyBackupAndEncrypt:
    """
    Mock the repository dependencies for the machine.
    """

    class DependencyMocks(BaseDependency):
        create_intermediate_directory = MockBasic.success
        remove_intermediate_directory = MockBasic.success
        create_pg_dump_directory = MockBasic.success
        remove_pg_dump_directory = MockBasic.success
        backup_schema = MockBasic.success
        remove_schema_file = MockBasic.success
        backup_data = MockBasic.success
        remove_data_file = MockBasic.success
        compress = MockBasic.success
        remove_tarball = MockBasic.success
        encrypt = MockBasic.success
        remove_encrypted_backup = MockBasic.success
        create_storage_directory = MockBasic.success
        move_backup = MockBasic.success

    return DependencyMocks  # pyright: ignore
```

What we are doing here is creating "mocks" of the outside functionality the class depends upon.  This function creates a dependency mapper that by default is saying everything will happen as expected.  Then, in the tests, we substitute this dependency mapper for the one the code is supposed to use in a real word scenario.

Looking at the happy-path test where everything runs as expected:

```python linenums="46"
def test_happy_path(monkeypatch):
    """Test the happy path."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        machine = create_machine(2)

        results = machine.execute()

        node_order = []
        for result in results:
            assert isinstance(result, Success)
            node_order.append(result.node)

        assert node_order == [
            "MachineBackupAndEncrypt.create_intermediate_directory",
            "MachineBackupAndEncrypt.create_pg_dump_directory",
            "MachineBackupAndEncrypt.backup_schema",
            "MachineBackupAndEncrypt.backup_data",
            "MachineBackupAndEncrypt.compress",
            "MachineBackupAndEncrypt.encrypt",
            "MachineBackupAndEncrypt.create_storage_directory",
            "MachineBackupAndEncrypt.move_backup",
            "MachineBackupAndEncrypt.remove_encrypted_backup",
            "MachineBackupAndEncrypt.remove_tarball",
            "MachineBackupAndEncrypt.remove_data_file",
            "MachineBackupAndEncrypt.remove_schema_file",
            "MachineBackupAndEncrypt.remove_pg_dump_directory",
            "MachineBackupAndEncrypt.remove_intermediate_directory",
            "MachineBackupAndEncrypt.report_results",
        ]
```

In line 49 we are fetching a copy of our mock dependencies.

In lines 50 through 54, we inject our mock dependencies into the class definition. The setattr function is saying "for the module that the class being tested lives in, machine_backup_and_encrypt, replace DependencyBackupAndEncrypt with DependencyMocks".

We set everything up for default success using MockBasic.success, because none of these calls expect a return value.  MockBasic.success is about as simple a method as you can get.

```python linenums="11"
    @classmethod
    def success(cls, **kwargs) -> Any:
        """The mocked function succeeded and had nothing to return."""
```

It doesn't do anything except return without error.  And that's the behavior we want in the unit test.  We do not want our unit tests to go out and start creating directories in the file system of the machine they are being run on.  We are only testing the functionality that resides within the class being tested.

The magic "***kwargs" says the method accepts whatever named parameters it is called with.  Since we are using named parameters throughout the system, the success method can be used to mock any method where a return value is not expected.

Now we'll take a look at a failure scenario.  Executing "mkdir -p ..." is something that can fail.  Maybe the disk is out of space or you don't have permissions to make the directory where it's trying to be created.  In an automated system, that is an unrecoverable situation that we want reported back to us.  We want to make sure there is defined behavior for handling a failure of "mkdir -p ...", so the program doesn't just die silently.

```python linenums="84"
def test_create_intermedite_failure(monkeypatch):
    """Test when creation of the intermediate directory fails."""
    with monkeypatch.context() as patch:
        DependencyMocks = get_mocks()
        DependencyMocks.create_intermediate_directory = MockBasic.failure
        patch.setattr(
            machine_backup_and_encrypt,
            "DependencyBackupAndEncrypt",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=3,
            failing_node=0,
            with_message="test_client_name test_postgresql.somewhere.in.azure test_database unrecognized exception: unit test failure",
        )
```

In line 87, we fecth our mock dependencies.
In line 88, we change the behavior for create_intermediate_directory from MockBasic.success to MockBasic.failure.
Lines 89 through 93 inject our mock dependencies into the machine_backup_and_encrypt module.

MockBasic.failure, also, is not a complicated function.

```python linenums="15"
    @classmethod
    def failure(cls, **kwargs) -> Any:
        """The mocked function raised an exception."""
        raise Exception("unit test failure")
```

We don't care why "mkdir -p ..." may have failed.  We just want to make sure the class behaved the way it should when it encountered a failure with "mkdir -p ...".

The reason we separate the dependency mapper into per-usage of the dependencies is because the dependencies may be used more than once.  If we look back at the original definition of DependencyBackupAndEncrypt, we will find that create_intermediate_directory, create_pg_dump_directory, and create_storage_directory are all using FileManager.make_dir_if_not_exists.

Without separating them, we would be unable to test failures for create_pg_dump_directory or create_storage_directory.  Were we to set up FileManager.make_dir_if_not_exists to fail directly, the implementation would never reach the usages of create_pg_dump_directory or create_storage_directory, because it would always fail at create_intermediate_directory and bypass the code for the other usages.