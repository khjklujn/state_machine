# Unit Tests

Unit testing is based on pytest, which is expected to be executed within the top-level project directory.

``` bash

pytest -s
```

Individual tests can be executed by specifying the tests file name.  Example:

``` bash

pytest tests/state_machine/machine/test_happy_path.py -s
```

The unit tests exercise the parts of the code base that make decisions about what should
be done.  They do not execute the parts of the code base that actually go out and do
something.

Within the tests directory you will find:

* constant: Unit tets of standardized templating behavior based on the constants.
* end_point: Unit tests of the End-Point layer.
* mocks: Code to emulate the parts of the code base that go out and do something.
* service: Unit tests for the code in the Service layer.
* state_machine: Unit tests for the Machine base classes.

The directory structures for the unit tests mirror the directory structure of the long_term_storage code being tested.

pytest discovers tests based on naming convention.  Python files beginning with "test" are considered to be test files that need to be
executed.  Functions within the test files that begin with "test" are considered the test cases.

All of the red and green paths in the diagrams need to be tested.  Additionally, any "if" branches within a node need to be tested.

## Service Layer

The sample state-machine for the testing discussion looks like:

![System Diagram](machine_backup_databases.svg)

The machine:

- Queries the PostgreSQL instance to get a list of databases to be backed up.
- Ensures the correct public key is installed for encryption.
- Invokes MachineBackupAndEncrypt for each of the databases to perform the backup.
- Invokes MachineEomDeletionCandidates to remove end-of-month backups that are beyond their retention period.
- Invokes MachineEoyDeletionCandidates to remove end-of-year backups that are beyond their retention period.

The Service layer tests may contain two convience functions:

* create_machine.py: Instantiates the state-machine being tested.
* inject_machines.py: Creates mocks of other state-machines that may be invoked by the machine being tested.

### create_machine example

```python linenums="1"
# application imports
from service.backup.backup_databases import (
    MachineBackupDatabases,
    StateBackupDatabases,
)

# mocks
from tests.mocks import MockBackupConfigModel, MockLogger


def create_machine(eoy_month: int = 1) -> MachineBackupDatabases:
    """
    Create a machine for testing.
    """
    logger = MockLogger()

    return MachineBackupDatabases(
        logger=logger,
        state=StateBackupDatabases(
            client_name="test_client_name",
            backup_config=MockBackupConfigModel(),
            eoy_month=eoy_month,
        ),
    )
```

create_machine returns an instance of the machine being tested.  This version has been parameterized with eoy_month, which is used for testing a variations of the backup process (end-of-year backups have a different long-term-storage directory than end-of-month backups).

Logger is a mocked to not produce any output. BackupConfigModel is mocked to provide a standard set of return values that would have been pulled from Key Vault.

### inject_machines example

```python linenums="1"
# to be mocked
from service.backup.backup_and_encrypt import MachineBackupAndEncrypt
from service.retention_end_of_month.eom_deletion_candidates import (
    MachineEomDeletionCandidates,
)
from service.retention_end_of_year.eoy_deletion_candidates import (
    MachineEoyDeletionCandidates,
)
from state_machine import Success

# mock imports
from tests.mocks import MockInvokedMachine


def inject_machines(
    patch,
):
    """Mock the nested state machines."""
    patch.setattr(
        MachineBackupAndEncrypt,
        "execute",
        MockInvokedMachine.success(
            Success(
                node="MachineBackupAndEncrypt.report_results",
            )
        ),
    )
    patch.setattr(
        MachineEomDeletionCandidates,
        "execute",
        MockInvokedMachine.success(
            Success(
                node="MachineEomDeletionCandidates.report_results",
            )
        ),
    )
    patch.setattr(
        MachineEoyDeletionCandidates,
        "execute",
        MockInvokedMachine.success(
            Success(
                node="MachineEoyDeletionCandidates.report_results",
            )
        ),
    )
```

The machine being tested invokes three other machines while it is processing.  The machines will be instantiated by the underlying code while testing, but we replace the execute method of the invoked machines to make them behave as though they only had one node that always executed successfully.

### Happy path test example

```python linenums="1"
"""
Test the discovery of databases to be backed up.
"""

# standard library imports
from pprint import pprint

# application import
from service.backup.backup_databases import (
    machine_backup_databases,
    DependencyBackupDatabases,
)
from state_machine import BaseDependency, Success

# import mocks
from tests.mocks import MockBasic, MockPostgreSQL

# testing imports
from tests.service.failure_asserts import failure_asserts

# local imports
from .create_machine import create_machine
from .inject_machines import inject_machines


def get_mocks() -> DependencyBackupDatabases:
    """
    Mock the repository dependencies for the machine.
    """

    class DependencyMock(BaseDependency):
        fetch_databases = MockPostgreSQL.list_databases_four_results
        does_public_key_exist = MockBasic.success
        remove_pre_installed_public_key = MockBasic.success
        install_public_key = MockBasic.success
        trust_public_key = MockBasic.success
        remove_public_key = MockBasic.success

    return DependencyMock  # pyright: ignore


def test_happy_path(monkeypatch):
    """Test the happy path."""
    with monkeypatch.context() as patch:
        inject_machines(patch)
        DependencyMocks = get_mocks()
        patch.setattr(
            machine_backup_databases,
            "DependencyBackupDatabases",
            DependencyMocks,
        )

        machine = create_machine()

        results = machine.execute()

        node_order = []
        for result in results:
            assert isinstance(result, Success)
            node_order.append(result.node)

        assert node_order == [
            "MachineBackupDatabases.fetch_databases",
            "MachineBackupDatabases.does_public_key_exist",
            "MachineBackupDatabases.install_public_key",
            "MachineBackupDatabases.trust_public_key",
            "MachineBackupAndEncrypt.report_results",
            "MachineBackupAndEncrypt.report_results",
            "MachineBackupAndEncrypt.report_results",
            "MachineBackupAndEncrypt.report_results",
            "MachineBackupDatabases.backup_databases",
            "MachineBackupDatabases.remove_public_key",
            "MachineEomDeletionCandidates.report_results",
            "MachineBackupDatabases.end_of_month_retention",
            "MachineEoyDeletionCandidates.report_results",
            "MachineBackupDatabases.end_of_year_retention",
            "MachineBackupDatabases.report_results",
        ]
```

When testing the happy path, we want to confirm that the green paths in the diagram are followed as expected:

- No failures occur--tested in lines 58 and 59.
- The nodes for the testing scenario are executed in the expected order--tested in lines 62 through 78.

The first thing we will look at is the dependency injection.

```python linenums="26"
def get_mocks() -> DependencyBackupDatabases:
    """
    Mock the repository dependencies for the machine.
    """

    class DependencyMock(BaseDependency):
        fetch_databases = MockPostgreSQL.list_databases_four_results
        does_public_key_exist = MockBasic.success
        remove_pre_installed_public_key = MockBasic.success
        install_public_key = MockBasic.success
        trust_public_key = MockBasic.success
        remove_public_key = MockBasic.success

    return DependencyMock  # pyright: ignore
```

Here we are recreating the dependency mapper used by the state-machine to replace the functionality that would go out and change things with functionality that behaves as though that code had been executed successfully.  Most of the Repository calls in this state-machine don't expect a return value, so MockBasic.success is used--a function that does nothing and returns without failure.

The difference is for the fetch_databases node, which does expect databases that need to be backed up to be returned by PostgreSQL. Requesting a backup of a PostgreSQL instance that has no databases to backup is considered a failure condition that needs to be reported back to us.

Looking at the Repository definition of list_databases originally used by the production system:

```python linenums="49"
    @classmethod
    def list_databases(
        cls,
        *,
        connection_model: ServicePrincipal,
        excluding: list[str] = [],
    ) -> list[str]:
        if excluding:
            exclude = [f"'{database}'" for database in excluding]
            statement = f"""
                select
                    datname
                from pg_database
                where
                    datname not in ({",".join(exclude)}) and
                    not datistemplate
            """
        else:
            statement = """
                select
                    datname
                from pg_database
                where
                    not datistemplate
            """

        return [
            record["datname"]
            for record in cls.execute(
                statement=statement,
                connection_model=connection_model,
            )
        ]
```

We see that it is issuing a query that has a single column and will be returned as a list of strings that contain the database names.  To mock this behavior, we create a method that returns a set of expected results.

```python linenums="14"
    @classmethod
    def list_databases_four_results(cls, **kwargs) -> Any:
        """Returns a list of four databases."""
        return [
            "test_database_1",
            "test_database_2",
            "test_database_3",
            "test_database_4",
        ]
```

Instead of querying a PostgreSQL instance, the unit test will continue processing as though it had queried a PostgreSQL instance and PostgreSQL reported there were four databases to be backed up.

Looking at the definition of the happy path test:

```python linenums="42"
def test_happy_path(monkeypatch):
    """Test the happy path."""
    with monkeypatch.context() as patch:
```

We see the function defining the test takes a single parameter: monkeypatch.  monkeypatch is then used in a "with" statement, which is known as a "context generator".  Context generators say "this block of code will share the context provided by 'with ...'".

In this case, the provided context is "patch".

"monkeypatch" provides the dependency injection functionality.  Within the monkeypatch context, "patched" items will use the alternative behavior when the test is executed.  The reason for doing it this way is to isolate the dependency injection to just the code being tested.  Say we had a situation where the code is using the datetime.now(UTC) function to get the current time, but we needed to the test to always take place at a fixed point in time, so we override the behavior of utctime to return a fixed time.  Doing that outside of a monkeypatch context would interfere with the test framework, which also needs to be able use datetime.now(UTC) to determine what time it is.

Moving on to the dependency injection:

```python linenums="45"
        inject_machines(patch)
        DependencyMocks = get_mocks()
        patch.setattr(
            machine_backup_databases,
            "DependencyBackupDatabases",
            DependencyMocks,
        )
```

Line 45 sets up mocks of the state-machines that will be invoked by this one.

Line 46 fetches a copy of out mock definitions.

Lines 47 through 51 inject the mocks into the original code base.  The first parameter of setattr identifies the target of the injection.  In this case, it's the module the state-machine was defined in.  The second parameter identifies the name of the item that will be substituted.  The third parameter is what should be used instead of the original definition.  What this statement says is, "For every usage of DependencyBackupDatabases in the machine_backup_databases module, use DependencyMocks instead".

We then create the machine, execute the machine, and gather the results.

```python linenums="53"
        machine = create_machine()

        results = machine.execute()
```

Now that the machine has been executed, we are ready to confirm it behaved as expected.  Our first expectation is that it only followed green paths in the diagram, so we examine each of the results to confirm there were no Failures.

```python linenums="57"
        node_order = []
        for result in results:
            assert isinstance(result, Success)
            node_order.append(result.node)
```

While we are checking the results, we also gather a list of the node names that were executed in the order they were executed.  That list is used in the final statement to confirm the flow through the nodes matches what we expected to happen.

```python linenums="62"
        assert node_order == [
            "MachineBackupDatabases.fetch_databases",
            "MachineBackupDatabases.does_public_key_exist",
            "MachineBackupDatabases.install_public_key",
            "MachineBackupDatabases.trust_public_key",
            "MachineBackupAndEncrypt.report_results",
            "MachineBackupAndEncrypt.report_results",
            "MachineBackupAndEncrypt.report_results",
            "MachineBackupAndEncrypt.report_results",
            "MachineBackupDatabases.backup_databases",
            "MachineBackupDatabases.remove_public_key",
            "MachineEomDeletionCandidates.report_results",
            "MachineBackupDatabases.end_of_month_retention",
            "MachineEoyDeletionCandidates.report_results",
            "MachineBackupDatabases.end_of_year_retention",
            "MachineBackupDatabases.report_results",
        ]
```

That's as far as the unit test is taken.  We are only interested in confirming that the business logic will make the decisions we expect it to make.

### Failure path test example

Failure testing has been generalized into a convenience function called failure_asserts.

```python linenums="1"
"""
Convience function for testing failure paths.
"""

# standard library imports
from pprint import pprint
from typing import Callable

# application imports
from state_machine import AbstractMachine, Failure


def failure_asserts(
    create_machine: Callable[..., AbstractMachine],
    result_count: int,
    failing_node: int,
    with_message: str,
):
    """
    Function for testing failure paths.

    parameters:
        create_machine (Callable): The function to create an instance of the machine.
        result_count (int): The number of success/failure results that are expected to be generated under the testing conditions.
        failing_node (int): The location of the node that was configured to fail.
        with_message (str): The expected failure message.
    """
    machine = create_machine()

    results = machine.execute()

    pprint(results)
    print()
    print(len(results))
    print(results[failing_node].__class__.__name__, results[failing_node])

    assert len(results) == result_count
    assert isinstance(results[failing_node], Failure)
    assert with_message in results[failing_node].message  # pyright: ignore
```

failure_asserts creates the machine, executes the machine, prints some useful debugging information in case the test fails, and asserts:

- The count of success/failure results matches what was expected based on the failure scenario that was set up.
- The node that was configured to fail did indeed fail.
- The failure message that will be reported in an alert is what would be expected for the failure condition.

Looking at the first node that needs to be tested:

```python linenums="67"
    @handle_exceptions(on_exception="end_of_month_retention")
    @node
    def fetch_databases(self) -> Transition:
        """
        overview:
            Retrieve a list of the databases to be backed up.

        is_entry: True

        happy_paths:
            - does_public_key_exist

        unhappy_paths:
            - end_of_month_retention
        """
        # The name of the database instance used in failure reporting is
        # stored separately from the client_config in case there are connection
        # problems with client_config, which could result in an exception in
        # the exception handler.
        self.state.postgresql_url = self.state.client_config.postgresql_host

        # Bundle up the information needed to authenticate and connect to the database.
        connection_model = ServicePrincipal(
            host=self.state.client_config.postgresql_host,
            port=self.state.client_config.postgresql_port,
            service_principal_id=self.state.client_config.postgresql_service_principal_id,
            client_secret=self.state.client_config.postgresql_secret,
        )

        # Collect the list of databases not to be backed up.
        excluding = (
            master_config.machine_backup_databases.exclude_everywhere
            + self.state.client_config.exclude_databases
        )

        # Fetch the databases to be backed up.
        self.state.databases = [
            record["datname"]
            for record in DependencyBackupDatabases(logger=self.logger).fetch_databases(
                connection_model=connection_model, excluding=excluding
            )
        ]

        # If there are databases, proceed with backing them up.
        if self.state.databases:
            return self.success(exit_to=self.does_public_key_exist)
        # Otherwise, inform us that we requested a backup of a PostgreSQL instance that has no databases to backup.
        else:
            return self.failure(
                exit_to=self.end_of_month_retention,
                message=f"no databases to backup",
            )
```

The first thing to note is that we have a @handle_exceptions decorator.  This indicates that unrecoverable failures can occur while trying to process this node.  This node is querying the database, which may be unreachable or somebody removed the backup user.  It doesn't really matter why we might not be able to query the database.  If we can't query the database server, we can't continue with trying to back it up.

So we want to test what happens in the Service layer under these circumstances.

```python linenums="101"
def test_fetch_databases_failed(monkeypatch):
    """Test when querying for list of databases fails."""
    with monkeypatch.context() as patch:
        inject_machines(patch)
        DependencyMocks = get_mocks()
        DependencyMocks.fetch_databases = MockBasic.failure
        patch.setattr(
            machine_backup_databases,
            "DependencyBackupDatabases",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=6,
            failing_node=0,
            with_message="test_client_name test_postgresql_url.rest.of.url unrecognized exception: unit test failure",
        )
```

Setting up the patching context is the same as for the happy path.  But we have one change we want to make for the dependency injections.  After we have fetched the mocks in line 105, we change the behavior of fetch_databases in line 106.  Instead of returning a set of database records that would allow the state-machine to continue processing, we rasie an exception to simulate a connection failure when trying to query the database.

We then call failure_asserts to validate that the machine behaved as expected under these conditions.

```python linenums="113"
        failure_asserts(
            create_machine=create_machine,
            result_count=6,
            failing_node=0,
            with_message="test_client_name test_postgresql_url.rest.of.url unrecognized exception: unit test failure",
        )
```

The parameters for failure_assert are:

- create_machine: The function used to create a test state-machine.
- result_count: The number of success/failure messages we expect to be executed under these circumstances. The failure path for fetch_databases has four nodes in the design, however, two of those nodes invoke outside state-machines, which back in inject_machines we set up to just return one success result.  So the four nodes from this machine plus the two from the mocked state-machines gives us 6 results we expect to find in the result list.
- failing_node: The result in the list we expect to be the failure we provoked in this machine.  This test is causing the first node to fail, so we expect the first result in the list to be the failure.
- with_message: The message we expect the machine to generate as a result of this kind of failure.

The nodes are expected to return either self.success or self.failure.  These are convenience methods in AbstractMachine that perform the appropriate logging and build the Transition object in a consistent manner.  They are also useful for determining paths that need to be tested, since any place we see "return self.failure(...)" needs to be tested.

Reviewing the implementation of fetch_databases, we also see that line 115 also contains a "return self.failure(...)".  The condition that allows us to get to that failure path is if we successfully query the PostgreSQL instance, but it reported back that there are no databases to backup.

So we want to test that path as well.

```python linenums="81"
def test_fetch_databases_empty(monkeypatch):
    """Test when no databases to backup."""
    with monkeypatch.context() as patch:
        inject_machines(patch)
        DependencyMocks = get_mocks()
        DependencyMocks.fetch_databases = MockBasic.empty_list
        patch.setattr(
            machine_backup_databases,
            "DependencyBackupDatabases",
            DependencyMocks,
        )

        failure_asserts(
            create_machine=create_machine,
            result_count=6,
            failing_node=0,
            with_message="test_client_name test_postgresql_url.rest.of.url no databases to backup",
        )
```

The difference in the mocking behavior is in line 86, where instead of returning a list of databases to be backed up, it returns an empty list.

The difference in the failure_asserts test is in with_message. We're still failing in the first node, and the machine is designed to follow the same paths in this situation, but the message that will be reported back in the failure report is different.
