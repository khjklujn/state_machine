# Services

The services contain the parts of the code that decide what should be done, and once that decision has been made, they invoke one or more repositories to go out and perform the actions.

The services are built with state-machines using the result pattern (the outcome of trying to do something is either Success or Failure).  A state-machine is just a collection of "nodes" that,
depending on the outcome of the node's action, will transition to a different node to be executed.  That's the machine.

The "state" is a collection of variables that allow the nodes to communicate with each other and make decisions about what to do next.

Visually, a state-machine is depicted in the diagram below (this is the process for backing up and encrypting the backup of a database).  The green arrows represent the "happy path"--what happens if everything processes as expected.  The red arrows are "unhappy paths"--what happens when, for some reason, the action could not be performed.

The reason for explicitly separating the code into happy and unhappy paths is this is an automated system that is intended to run without baby-sitting.  Any time something unexpected happens that prevents execution of the happy path, the system needs to generate an alert to escalate the problem to a human being for investigation.  That behavior is easiest to generalize as follow-an-unhappy-path, generate-an-alert.

Also, what might be apparent in the diagram is that the implementation is quite granular.  Each node is only executing one action that may or may not succeed.

The reason for this level of granularity is that a well built automated system can run for years without any problems.  During that time, _everybody_ will forget the system even exists, so when something does go wrong, there will be a reverse-engineering effort involved in figuring out what happened and what needs to be done about it.  The reverse-engineering effort can be greatly facilitated by failure reports that tell you exactly which step(s) failed, and, by looking at the diagram, you can determine what state the system was left in as a result of the failure(s).

Each service is composed of one or more machines.

![System Diagram](machine_backup_and_encrypt.svg)

The happy-path process for this backup-and-encrypt state-machine is:

1. Create an intermediate working directory in the storage area.
2. Create the directory to dump the SQL files to.
3. Use pgdump to pull a backup of the schema to the intermediate area.
4. Use pgdump to pull a backup of the data to the intermediate area.
5. Use tar to unify, compress and remove the intermediate backup directory.
6. Use gpg to encrypt the tar file.
7. Create the long term storage directory in the storage area.
8. Move the encrypted file to the long term storage directory.
9. Clean up intermediate directory.
10. Report the Success/Failure outcomes back to the where ever it was called from.

Step 9 (starting at remove_encrypted_backup) has been broken into six separate steps to accommodate the unhappy-path behavior in the previous steps. In the event any of them failing, we want to make sure there is no unencrypted data hanging around, and the system is in a state where, if we re-run the backup, there is nothing from the previous run that could interfere with the re-run (the technical term for this is indempodent).

## State Machines

The implementation of a state-machine has three components:

- State: A data object contatining the state variables.
- Dependencies: A data object containing the repositories the state-machine will use to perform actions.
- Machine: A class implementing the nodes that compose a state-machine.

### States

For the state-machine depicted above, the State object is defined as:

```python linenums="1"
# standard library imports
from datetime import datetime, UTC

# third party imports
from pydantic import Field

# repository imports
from repository.key_vault import BackupConfigModel

# application imports
from model.connection.key_vault import ServicePrincipal
from state_machine import BaseState


class StateBackupAndEncrypt(BaseState):
    """
    State variables for MachineBackupAndEncrypt.
    """

    client_name: str = Field(frozen=True)
    """The name of the client being backed up."""

    backup_config: BackupConfigModel = Field(frozen=True)
    """The configuration information from the key vault."""

    eoy_month: int = Field(frozen=True)
    """The numeric representation of the end-of-year month."""

    database: str = Field(frozen=True)
    """The name of the database being backed up."""

    postgresql_host: str = Field(frozen=True)
    """The PostgreSQL instance name that will be reported back in Failures."""

    time_stamp: datetime = Field(default=datetime.now(UTC), frozen=True)
    """The time stamp used for building the dates in the paths.  Default to utc now."""
```

All state classes derive from BaseState.  BaseState simply performs a little bit of configuration for what is allowed to be placed in the data model.

Taking a look at the first entry:

```python linenums="20"
    client_name: str = Field(frozen=True)
    """The name of the client being backed up."""
```

In line 20, "client_name" is the name of the data element, ": str" declares that it is intended to only contain string value, and "= Field(frozen=True) declares that this data element is immutable--after instantiation of the data object, it can't be changed.

Line 21 is a docstring explaining "why this thing exists".

### Dependencies

For the state-machine depicted above, the dependencies object is defined as:

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

The purpose of the dependencies object is to facilitate unit testing.  It provides a handy inventory of what needs to be mocked.  It also provides a way of performing individual mocking behavior.  For example, in this state-machine, the "make_dir_if_not_exists" method is used in the first node, third, and second to last one.  Were we to set up make_dir_if_not_exists directly to fail, the other two nodes could not be tested, because the machine would always fail in the first node, and the machine would follow a failure path that skips the other two nodes.

What's happening here is we are assigning the class methods of the repositories to data elements in the dependency object.  Then, in the machine, we will invoke the data element rather than the repository method directly.

The convention is to prefix the name of the data element with the node name it will be used in.  In this case, there aren't any cases where more than one repository is being used by a node, so the data element names are the same as the node names.

Docstrings are applied to the class name, so the class will be picked up by the documentation system.  However, docstrings are not applied to the data elements.  The IDE is smart enough to disentangle the indirection and provide intellisence hints based on the class method that is being referred to rather than the data element.

For the same reason, static typing is not used for the data elements. Duck typing in this case is sufficient to make sure the parameters and return types match up as according to the class method's signature.

### Machines

For the state-machine depicted above, the machine is defined as:

```python linenums="1"
# application imports
from constant.path import Path
from model.connection.postgresql import ServicePrincipal
from state_machine.decorator import handle_exceptions, machine, node
from state_machine import AbstractMachine, Transition

# local imports
from .state_backup_and_encrypt import StateBackupAndEncrypt
from .dependency_backup_and_encrypt import DependencyBackupAndEncrypt


@machine
class MachineBackupAndEncrypt(AbstractMachine):
    """
    overview: |+
        Database backups need to be pulled and encrypted.

        The steps to perform this are:

        1. Create an intermediate working directory in the storage area.
        2. Create the directory to dump the SQL files to.
        3. Use pgdump to pull a backup of the schema to the intermediate area.
        4. Use pgdump to pull a backup of the data to the intermediate area.
        5. Use tar to unify, compress and remove the intermediate backup directory.
        6. Use gpg to encrypt the tar file.
        7. Create the long term storage directory in the storage area.
        8. Move the encrypted file to the long term storage directory.
        9. Clean up intermediate directory.
        10. Report the Success/Failure outcomes back to the where ever it was called from.
    """

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

    @handle_exceptions(on_exception="report_results")
    @node
    def remove_intermediate_directory(self) -> Transition:
        """
        overview:
            Remove the intermediate directory.

        happy_paths:
            - report_results

        unhappy_paths:
            - report_results
        """
        path = Path.intermediate_backup_base(
            client_name=self.state.client_name, database_name=self.state.database
        )
        DependencyBackupAndEncrypt(logger=self.logger).remove_intermediate_directory(
            path=path
        )

        return self.success(exit_to=self.report_results)

    @handle_exceptions(on_exception="remove_pg_dump_directory")
    @node
    def create_pg_dump_directory(self) -> Transition:
        """
        overview:
            Create the intermediate directory for pg_dump to pull the backup.

        happy_paths:
            - backup_schema

        unhappy_paths:
            - remove_pg_dump_directory
        """
        path = Path.intermediate_backup_directory(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )
        DependencyBackupAndEncrypt(logger=self.logger).create_pg_dump_directory(
            path=path
        )

        return self.success(exit_to=self.backup_schema)

    @handle_exceptions(on_exception="remove_intermediate_directory")
    @node
    def remove_pg_dump_directory(self) -> Transition:
        """
        overview:
            Remove the pg_dump directory.

        happy_paths:
            - remove_intermediate_directory

        unhappy_paths:
            - remove_intermediate_directory
        """
        path = Path.intermediate_backup_directory(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )
        DependencyBackupAndEncrypt(logger=self.logger).remove_pg_dump_directory(
            path=path
        )

        return self.success(exit_to=self.remove_intermediate_directory)

    @handle_exceptions(on_exception="remove_schema_file")
    @node
    def backup_schema(self) -> Transition:
        """
        overview:
            Backup the schema to the intermediate area.

        happy_paths:
            - backup_data

        unhappy_paths:
            - remove_schema_file
        """
        connection_model = ServicePrincipal(
            host=self.state.client_config.postgresql_host,
            port=self.state.client_config.postgresql_port,
            service_principal_id=self.state.client_config.postgresql_service_principal_id,
            client_secret=self.state.client_config.postgresql_secret,
            database=self.state.database,
        )

        path = Path.intermediate_backup_schema_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )

        DependencyBackupAndEncrypt(logger=self.logger).backup_schema(
            connection_model=connection_model, path=path
        )

        return self.success(exit_to=self.backup_data)

    @handle_exceptions(on_exception="remove_pg_dump_directory")
    @node
    def remove_schema_file(self) -> Transition:
        """
        overview:
            Remove the schema file.

        happy_paths:
            - remove_pg_dump_directory

        unhappy_paths:
            - remove_pg_dump_directory
        """
        path = Path.intermediate_backup_schema_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )
        DependencyBackupAndEncrypt(logger=self.logger).remove_schema_file(path=path)

        return self.success(exit_to=self.remove_pg_dump_directory)

    @handle_exceptions(on_exception="remove_data_file")
    @node
    def backup_data(self) -> Transition:
        """
        overview:
            Backup the data to the intermediate area.

        happy_paths:
            - compress

        unhappy_paths:
            - remove_data_file
        """
        connection_model = ServicePrincipal(
            host=self.state.client_config.postgresql_host,
            port=self.state.client_config.postgresql_port,
            service_principal_id=self.state.client_config.postgresql_service_principal_id,
            client_secret=self.state.client_config.postgresql_secret,
            database=self.state.database,
        )

        path = Path.intermediate_backup_data_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )

        DependencyBackupAndEncrypt(logger=self.logger).backup_data(
            connection_model=connection_model, path=path
        )

        return self.success(exit_to=self.compress)

    @handle_exceptions(on_exception="remove_schema_file")
    @node
    def remove_data_file(self) -> Transition:
        """
        overview:
            Remove the data file.

        happy_paths:
            - remove_schema_file

        unhappy_paths:
            - remove_schema_file
        """
        path = Path.intermediate_backup_data_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )
        DependencyBackupAndEncrypt(logger=self.logger).remove_data_file(path=path)

        return self.success(exit_to=self.remove_schema_file)

    @handle_exceptions(on_exception="remove_tarball")
    @node
    def compress(self) -> Transition:
        """
        overview:
            Consolidate, compress, and remove the backup folder.

        happy_paths:
            - encrypt

        unhappy_paths:
            - remove_tarball
        """
        directory_to_run_in = Path.intermediate_backup_base(
            client_name=self.state.client_name, database_name=self.state.database
        )

        directory_to_tar = Path.intermediate_tarball_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )

        tarball = self.state.time_stamp.strftime(Path.TIMESTAMP_FORMAT.value)

        DependencyBackupAndEncrypt(logger=self.logger).compress(
            directory_to_run_in=directory_to_run_in,
            directory_to_tar=directory_to_tar,
            tarball=tarball,
        )

        return self.success(exit_to=self.encrypt)

    @handle_exceptions(on_exception="remove_data_file")
    @node
    def remove_tarball(self) -> Transition:
        """
        overview:
            Remove the tarball.

        happy_paths:
            - remove_data_file

        unhappy_paths:
            - remove_data_file
        """
        path = Path.intermediate_tarball_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )
        DependencyBackupAndEncrypt(logger=self.logger).remove_tarball(path=path)

        return self.success(exit_to=self.remove_data_file)

    @handle_exceptions(on_exception="remove_encrypted_backup")
    @node
    def encrypt(self) -> Transition:
        """
        overview:
            Encrypt the backup.

        happy_paths:
            - create_storage_directory

        unhappy_paths:
            - remove_encrypted_backup
        """
        key_name = self.state.client_config.key_name

        from_file = Path.intermediate_tarball_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
        )

        to_file = Path.intermediate_backup_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
            key_name=self.state.client_config.key_name,
        )

        DependencyBackupAndEncrypt(logger=self.logger).encrypt(
            key_name=key_name, from_file=from_file, to_file=to_file
        )

        return self.success(exit_to=self.create_storage_directory)

    @handle_exceptions(on_exception="remove_tarball")
    @node
    def remove_encrypted_backup(self) -> Transition:
        """
        overview:
            Remove the encrypted backup.

        happy_paths:
            - remove_tarball

        unhappy_paths:
            - remove_tarball
        """
        path = Path.intermediate_backup_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
            key_name=self.state.client_config.key_name,
        )
        DependencyBackupAndEncrypt(logger=self.logger).remove_encrypted_backup(
            path=path
        )

        return self.success(exit_to=self.remove_tarball)

    @handle_exceptions(on_exception="remove_encrypted_backup")
    @node
    def create_storage_directory(self) -> Transition:
        """
        overview:
            Make sure the storage directory exists.

        happy_paths:
            - move_backup

        unhappy_paths:
            - remove_encrypted_backup
        """
        path = Path.long_term_storage_directory(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
            eoy_month=self.state.eoy_month,
        )

        DependencyBackupAndEncrypt(logger=self.logger).create_storage_directory(
            path=path
        )

        return self.success(exit_to=self.move_backup)

    @handle_exceptions(on_exception="remove_encrypted_backup")
    @node
    def move_backup(self) -> Transition:
        """
        overview:
            Move the encrypted backup to long-term-storage area.

        happy_paths:
            - remove_encrypted_backup

        unhappy_paths:
            - remove_encrypted_backup
        """
        from_path = Path.intermediate_backup_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
            key_name=self.state.client_config.key_name,
        )

        to_path = Path.long_term_backup_file(
            client_name=self.state.client_name,
            database_name=self.state.database,
            time_stamp=self.state.time_stamp,
            key_name=self.state.client_config.key_name,
            eoy_month=self.state.eoy_month,
        )

        DependencyBackupAndEncrypt(logger=self.logger).move_backup(
            from_path=from_path, to_path=to_path
        )

        return self.success(exit_to=self.remove_encrypted_backup)

    @property
    def failure_prefix(self) -> str:
        """A message to be prepended to the failure reporting messages."""
        return f"{self.state.client_name} {self.state.postgresql_host} {self.state.database}"

    @property
    def state(self) -> StateBackupAndEncrypt:
        """
        Overrides base functionality of state to return the proper type for this machine.
        """
        return self._state  # pyright: ignore
```

Perhaps one of the things initially notable is there is nearly as much text in the docstrings as there is code implementing what the node does.  The dosctrings describe the design of the state-machine and how the nodes are allowed to flow from one to the next.  They are used to generate the design diagram for the state-machine.  They are required.  There are both compile-time and run-time checks that guarantee the flow between nodes in the implementation matches the documented design of the state-machine.

The approach to building the state-machine is to start with the overview section of the class-level docstring where you sketch out the off-the-top-of-your-head happy-path steps. Then nodes are stubbed out for each of the steps in the happy path, and while building the docstrings for the happy-path nodes, you put some consideration into what happens if the node is doesn't do what it is intended to do, which are the unhappy paths. The nodes are stubbed out for the unhappy paths, and documentation.document_machines is run to render the diagram.

Once you've stared at the diagram for a while and decided the machine would do what you wanted it to, then it is time to implement the behavior of the nodes, which is usually quite trivial, since any individual node isn't supposed to do very much.

Anyway, looking at the code, the first new item to make an appearance is the machine decorator.

```python linenums="12"
@machine
class MachineBackupAndEncrypt(AbstractMachine):
```

Decorators in Python lines that are prefixed with an ampersand "@".  They call their defining function at compile-time.  The defining function will receive the decorated item as a parameter, and can perform processing based on the definition of the item.

The @machine decorator will perform a lot of compile-time validations to make sure the state-machine definition is self-consistent--every path called out in the docstrings for the nodes have a method defined to implement them, all the implemented nodes are reachable, the entrance node is identified, and at least one terminal node is defined.

All state-machines are inherited from AbstractMachine, which will be covered in a later episode.

Next comes the docstring.

```python linenums="14"
    """
    overview: |+
        Database backups need to be pulled and encrypted.

        The steps to perform this are:

        1. Create an intermediate working directory in the storage area.
        2. Create the directory to dump the SQL files to.
        3. Use pgdump to pull a backup of the schema to the intermediate area.
        4. Use pgdump to pull a backup of the data to the intermediate area.
        5. Use tar to unify, compress and remove the intermediate backup directory.
        6. Use gpg to encrypt the tar file.
        7. Create the long term storage directory in the storage area.
        8. Move the encrypted file to the long term storage directory.
        9. Report the Success/Failure outcomes back to the where ever it was called from.
    """
```

The docstring contains a yaml description of the machine that is required to have an "overview:" entry--@machine will raise a NoOverviewError at compile-time if the overview section is not populated.

Next come the node definitions.

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

The @handle_exception decorator wraps the node in a try-block, and the on_exception parameter identifies which node will be transitioned to in the event an exception is raised while executing the code in the node.  All nodes must either be decorated with @handle_exception to define the exception handling path or @no_exceptions when the code will not raise any exceptions.

The @node decorator identifies the method as a node and validates all of the required parts of the node docstring are present.

| Docstring Section | Description                                            | Required                                                                           |
| ----------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| overview          | Why this node is here.                                 | Yes                                                                                |
| is_entry          | Indicates the node is the entry point for the machine. | One per machine                                                                    |
| is_terminal       | Indicates the node is an exit point for the machine.   | At least one per machine (normally provided by return_results from the base class) |
| happy_paths       | A list of the happy-path exits the node can take.      | If the node is not terminal and there are no unhappy_paths.                        |
| unhappy_paths     | A list of the unhappy-path exits the node can take.    | If the node is not terminal and there are no happy_paths.                          |
| invokes_machine   | Another state-machine the node may route to.           | No                                                                                 |

So, the docstring for this node:

```python linenums="35"
        """
        overview:
            Create the intermediate directory for pulling the backup.

        is_entry: True

        happy_paths:
            - create_pg_dump_directory

        unhappy_paths:
            - remove_intermediate_directory
        """
```

Is interpreted as:

- overview: We want to make sure the intermediate directory for processing backups exists.
- is_entry: This node is the entry point for the machine.
- happy_paths: The node can send Success results to create_pg_dump_directory.
- unhappy_paths: The node can send Failure results to remove_intermediate_directory.


Finally, we have the implementation.

```python linenums="47"
        DependencyBackupAndEncrypt(logger=self.logger).create_intermediate_directory(
            path=Path.intermediate_backup_base(
                client_name=self.state.client_name, database_name=self.state.database
            )
        )

        return self.success(exit_to=self.create_pg_dump_directory)
```

"DependencyBackupAndEncrypt(logger=self.logger)" instantiates the DependencyBackupAndEncrypt data object with the system logger so the repository objects can log their messages.

"create_intermediate_directory" calls the method we mapped back in the DependencyBackupAndEncrypt definition.

```python linenums="15"
    create_intermediate_directory = FileManager.make_dir_if_not_exists
```

So, we're executing FileManager.make_dir_if_not_exists with the defined path parameter.

The call to Path.intermediate_backup_base is not considered a "repository" call because it has no dependencies outside the service layer.  It's completely under our control, and the unit tests we built for it guarantee it will behave exactly as expected.
Then we return a Success transition that specifies the next node to be executed.

At the bottom of the class we have two properties defined.

```python linenums="409"
    @property
    def failure_prefix(self) -> str:
        """A message to be prepended to the failure reporting messages."""
        return f"{self.state.client_name} {self.state.postgresql_host} {self.state.database}"

    @property
    def state(self) -> StateBackupAndEncrypt:
        """
        Overrides base functionality of state to return the proper type for this machine.
        """
        return self._state  # pyright: ignore
```

These are the "abstract" portions of the base class. They don't have a default implementation and need to have their implementation defined on a per-machine basis.

The first, "failure_prefix", is a message that will be prepended to any failure messages the machine may generate. The failures reported from a state-machine will include which node the failure occurred in, but for this machine, we would also like to know which client, PostgreSQL instance, and database name the failure is associated with.

The second, "state", just changes the type returned by the state property. In the base class, the type being returned is StateBase, because the data elements for a specific state-machine aren't known by the state-machine library.  The "# pyright: ignore" turns off static type-checking for that line.  In the base class self._state is defined as a StateBase variable, which doesn't match up with the return value of StateBackupAndEncrypt.  However, since we know the machine will be instantiated with a StateBackupAndEncrypt object to be placed into self._state, it's safe to ignore static-typing telling us "this isn't right".