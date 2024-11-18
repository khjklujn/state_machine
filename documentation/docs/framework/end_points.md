# End Points

End-points are responsible for invoking the system behavior.

There are two classes defined for processing end-point behavior.  The first defines a class called EndPoint.

```python linenums="1"
# standard library imports
from traceback import format_exc

# application imports
from state_machine import Logger
from state_machine import Failure, AbstractMachine

# local imports
from .dependency_end_point import DependencyEndPoint


class EndPoint:
    """
    Wrapper around a state machine to execute the machine and report failures to stdout.
    """

    def __init__(
        self,
        *,
        logger: Logger,
        machine: AbstractMachine,
    ):
        self._logger = logger
        self._machine = machine

    def execute(self):
        """
        Executes the machine, filters any failures, reports failures on stdout, and exits with the status of the number of failures.
        """
        try:
            self._results = self.machine.execute()

            self._failures = [
                result for result in self._results if isinstance(result, Failure)
            ]

            for failure in self._failures:
                self.logger.error(f"Failure: {failure}")
                DependencyEndPoint(logger=self.logger).execute_write_to_stdout(
                    content=f"Failure: {failure}"
                )

            DependencyEndPoint(logger=self.logger).execute_exit(
                result=len(self._failures)
            )
        except Exception as exception:
            self.logger.critical(f"Critical exception: {format_exc()}")
            DependencyEndPoint(logger=self.logger).execute_write_to_stdout(
                content=f"Critical failure: {exception}"
            )
            DependencyEndPoint(logger=self.logger).execute_exit(result=1)

    @property
    def logger(self):
        return self._logger

    @property
    def machine(self):
        return self._machine
```

The constructor takes two parameters:

- logger is the system logger.
- machine is the state-machine service to be executed.

The execute method runs the state-machine and compiles the the failure reports.

```python linenums="26"
    def execute(self):
        """
        Executes the machine, filters any failures, reports failures on stdout, and exits with the status of the number of failures.
        """
        try:
            self._results = self.machine.execute()

            self._failures = [
                result for result in self._results if isinstance(result, Failure)
            ]

            for failure in self._failures:
                self.logger.error(f"Failure: {failure}")
                DependencyEndPoint(logger=self.logger).execute_write_to_stdout(
                    content=f"Failure: {failure}"
                )

            DependencyEndPoint(logger=self.logger).execute_exit(
                result=len(self._failures)
            )
        except Exception as exception:
            self.logger.critical(f"Critical exception: {format_exc()}")
            DependencyEndPoint(logger=self.logger).execute_write_to_stdout(
                content=f"Critical failure: {exception}"
            )
            DependencyEndPoint(logger=self.logger).execute_exit(result=1)
```

The first thing we are going to do in the try-block, is execute the state-machine, which is going to report the successes and failures back to us.

We then filter out the failures from the results.

For each failure we output a line describing the failure to stdout.  DependencyEndPoint.execute_write_to_stdout is a wrapper Python's builtin print function.  We treat as a Repository for unit testing purposes.

We then exit the process with the count of failures that occurred as the exit-code.  Zero failures means everything was happy.  DependencyEndPoint.execute_exit is a wrapper around Python's builtin exit function.  Calling exit in the middle a unit test stops everything--including the unit test framework.

We setup self._results and self._failures as instance variables, so the outcomes of executing a machine are available in unit testing.

The second type of end-point is a DynamicMountingEndPoint.

```python linenums="1"
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
```

Dynamic mounting/unmounting of the file-shares was tacked on top of existing code that assumed the file-share would be mounted prior to execution.  MachineDynamicMount that takes an arbitrary state-machine as a parameter, mounts the file-share prior to executing the provided machine, and unmounts the file-share following execution of the machine.

DynamicMountingEndPoint overrides the construction of EndPoint to insert MachineDynamicMount as the state-machine to be executed.

The full definition of an "end-point" in this case is a command line script to be executed by the Control-M scheduler.  Taking a look at the definition of the backup script:

```python linenums="1"
"""
Script to execute the backup of a PostgreSQL instance.

usage: python -m backup.run [-h] [--tenant_id TENANT_ID] [--authority_host AUTHORITY_HOST] client_name eoy_month key_vault client_id client_secret

Backup a PostgreSQL instance.

positional arguments:
  client_name           The name of the client to be backed up
  eoy_month             The month that designates the end-of-year (1-12)
  key_vault             The url of the client's key vault
  client_id             The client id for the Service Principal
  client_secret         The secret for the Service Principal

options:
  -h, --help            show this help message and exit
  --tenant_id TENANT_ID
                        The tenant id for the key vault (optional)
  --authority_host AUTHORITY_HOST
                        The authority for authenticating the Service Principal (optional)
"""

# standard library imports
import argparse
from traceback import format_exc

# third party imports
from pydantic import SecretStr

# application imports
from long_term_storage.model.connection.key_vault import ServicePrincipal
from state_machine.config import encryption
from long_term_storage.repository import ClientLogger
from long_term_storage.repository.key_vault import BackupConfigModel
from long_term_storage.end_point.dynamic_mounting_end_point import (
    DynamicMountingEndPoint,
    StateDynamicMount,
)
from long_term_storage.service.backup.backup_databases import (
    MachineBackupDatabases,
    StateBackupDatabases,
)


def run(
    client_name: str,
    eoy_month: int,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    authority_host: str,
    key_vault: str,
):
    """
    Configure and execute the job.
    """
    try:
        # Create the logger.
        logger = ClientLogger(
            client_name=client_name,
            file_name=MachineBackupDatabases.__module__.split(".")[2],
        )

        logger.info("***************")

        # Load connection config from key vault.
        connection_model = ServicePrincipal(
            keyvault_host=key_vault,
            service_principal_id=client_id,
            client_secret=SecretStr(secret_value=encryption.decrypt(client_secret)),
            tenant_id=tenant_id,
            authority_host=authority_host,
        )
        backup_config = BackupConfigModel.from_keyvault(
            logger=logger, connection_model=connection_model
        )

        # Bundle up the model the machine expects and create the machine.
        state = StateBackupDatabases(
            client_name=client_name, backup_config=backup_config, eoy_month=eoy_month
        )
        machine = MachineBackupDatabases(logger=logger, state=state)

        # Use the end-point that wraps the machine with auto-mounting/unmounting
        # of the file share.
        end_point = DynamicMountingEndPoint(
            logger=logger,
            state_dynamic_mount=StateDynamicMount(
                client_name=client_name,
                backup_config=backup_config,
                machine_to_wrap=machine,
            ),
        )
        end_point.execute()

    # If anything goes wrong, dump the traceback to stdout and exit with a failure.
    except Exception as exception:
        print(f"Critical failure: {exception}")
        print(format_exc())
        exit(1)


if __name__ == "__main__":
    # Define the command line arguments.
    parser = argparse.ArgumentParser(
        prog="python -m backup.run", description="Backup a PostgreSQL instance."
    )
    parser.add_argument(
        "client_name", help="The name of the client to be backed up", type=str
    )
    parser.add_argument(
        "eoy_month", help="The month that designates the end-of-year (1-12)", type=int
    )
    parser.add_argument("key_vault", help="The url of the client's key vault", type=str)
    parser.add_argument(
        "client_id", help="The client id for the Service Principal", type=str
    )
    parser.add_argument(
        "client_secret", help="The secret for the Service Principal", type=str
    )
    parser.add_argument(
        "--tenant_id",
        help="The tenant id for the key vault (optional)",
        type=str,
        default="e17e2402-2a40-42ce-ad75-5848b8d4f6b6",
    )
    parser.add_argument(
        "--authority_host",
        help="The authority for authenticating the Service Principal (optional)",
        default="https://login.microsoftonline.com",
    )

    # Parse the command line arguments.
    args = parser.parse_args()

    # Execute the job.
    run(
        client_name=args.client_name,
        eoy_month=args.eoy_month,
        tenant_id=args.tenant_id,
        client_id=args.client_id,
        client_secret=args.client_secret,
        authority_host=args.authority_host,
        key_vault=args.key_vault,
    )
```

The script starts at the bottom-ish of the file in the part following line 98.

```python linenums="105"
if __name__ == "__main__":
```

This is a magic incantation in Python that determines whether the module was invoked directly from the command line or has been imported by another module.  When the module is executed from the command line, the builtin value of \_\_name\_\_ will contain "\_\_main\_\_".  When imported, \_\_name\_\_ will contain a module namespace value that is not "\_\_main\_\_", so when importing, the part after the "if" statement will not be executed.

The first thing the script does is defined the command line parameters.

```python linenums="106"
    # Define the command line arguments.
    parser = argparse.ArgumentParser(
        prog="python -m backup.run", description="Backup a PostgreSQL instance."
    )
    parser.add_argument(
        "client_name", help="The name of the client to be backed up", type=str
    )
    parser.add_argument(
        "eoy_month", help="The month that designates the end-of-year (1-12)", type=int
    )
    parser.add_argument("key_vault", help="The url of the client's key vault", type=str)
    parser.add_argument(
        "client_id", help="The client id for the Service Principal", type=str
    )
    parser.add_argument(
        "client_secret", help="The secret for the Service Principal", type=str
    )
    parser.add_argument(
        "--tenant_id",
        help="The tenant id for the key vault (optional)",
        type=str,
        default="e17e2402-2a40-42ce-ad75-5848b8d4f6b6",
    )
    parser.add_argument(
        "--authority_host",
        help="The authority for authenticating the Service Principal (optional)",
        default="https://login.microsoftonline.com",
    )
```

We instantiate an ArgumentParser object, and define each of the command line arguments.

We then compile the definition of the ArgumentParser, which will take care of reading the arguments from the command line and providing the usage/help info for the script when run from the command line.

```python linenums="136"
    args = parser.parse_args()
```

This exposes the command line arguments as named properties on the "args" variable.

Finally, we call the run function set up the EndPoint layer and execute the Service layer.

```python linenums="139"
    # Execute the job.
    run(
        client_name=args.client_name,
        eoy_month=args.eoy_month,
        tenant_id=args.tenant_id,
        client_id=args.client_id,
        client_secret=args.client_secret,
        authority_host=args.authority_host,
        key_vault=args.key_vault,
    )
```

Now, we'll look at the definition of the run function.

```python linenums="47"
def run(
    client_name: str,
    eoy_month: int,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    authority_host: str,
    key_vault: str,
):
    """
    Configure and execute the job.
    """
    try:
        # Create the logger.
        logger = ClientLogger(
            client_name=client_name,
            file_name=MachineBackupDatabases.__module__.split(".")[2],
        )

        logger.info("***************")

        # Get acces to the key vault containing the client config.
        KeyVault.logger = logger
        connection_model = ServicePrincipal(
            keyvault_host=key_vault,
            service_principal_id=client_id,
            client_secret=SecretStr(secret_value=encryption.decrypt(client_secret)),
            tenant_id=tenant_id,
            authority_host=authority_host,
        )
        key_vault_client = KeyVault().execute(connection_model=connection_model)
        backup_config = ClientConfig(logger, key_vault_client)

        # Bundle up the model the machine expects and create the machine.
        state = StateBackupDatabases(
            client_name=client_name, backup_config=backup_config, eoy_month=eoy_month
        )
        machine = MachineBackupDatabases(logger=logger, state=state)

        # Use the end-point that wraps the machine with auto-mounting/unmounting
        # of the file share.
        end_point = DynamicMountingEndPoint(
            logger=logger,
            state_dynamic_mount=StateDynamicMount(
                client_name=client_name,
                backup_config=backup_config,
                machine_to_wrap=machine,
            ),
        )
        end_point.execute()

    # If anything goes wrong, dump the traceback to stdout and exit with a failure.
    except Exception as exception:
        print(f"Critical failure: {exception}")
        print(format_exc())
        exit(1)
```

We wrap it in a try-block.  While there should be no unhadled exceptions in the End-Point or Service layers, if one does occur, we want to receive an alert.

The first thing we are doing is setting up the logger.

```python linenums="61"
        # Create the logger.
        logger = ClientLogger(
            client_name=client_name,
            file_name=MachineBackupDatabases.__module__.split(".")[2],
        )
```

This is an atypical way of logging in Python.  Normally, the logger would just be exposed as a "global" variable within each module's definition, and Python's logging system is smart enough to disentangle the multiple definitions.  In this case, however, we wanted the logs to be organized as one directory per client--information that isn't available in the "global" module namespace, so we've built a little wrapper around the logging system to make sure logs are routed to the correct directory.

The parameters for ClientLogger are:

- client_name is the name of the client directory the log file should appear in.
- file_name is the name of the log file.  MachineBackupDatabases.\_\_module\_\_.split(".")[2] is some introspective magic.  \_\_module\_\_ is a value every class has that identifies the full namespace path to the class.  For the MachineBackupDatabases class, the value would be "long_term_storage.services.backup.backup_databases.machine_backup_databases.MachineBackupDatabases".  The best name for the log file is the overall service name, which is the third element in the module name "backup".  So we split the string on "." and take the third element (lists are zero-indexed).

The next thing we do is log a bunch of asterisks.  This is just an easily searchable string that means "start of run".

Next, we're going to load information from the Azure Key Vault where the connection information and secrets needed to perform the backup live.  The information necessary to connect to this key vault was provided in the command line arguments.

```python linenums="68"
        # Load connection config from key vault.
        connection_model = ServicePrincipal(
            keyvault_host=key_vault,
            service_principal_id=client_id,
            client_secret=SecretStr(secret_value=encryption.decrypt(client_secret)),
            tenant_id=tenant_id,
            authority_host=authority_host,
        )
        backup_config = BackupConfigModel.from_keyvault(
            logger=logger, connection_model=connection_model
        )
```

Lines 69 through 75 are populating a data model that provides the information necessary for a Service Principal to access a key vault.

The primary weirdness here is in populating client_secret.  The client_secret for the Service Principal is not a value we want to expose, but since it needs to be provided as a command line argument, and all command line arguments are visible in clear text while a process is running, the command line parameter containing the value had to be encrypted prior to submitting the job.  So, we have to decrypt that value.  The encryption.decrypt function provides the clear-text, decrypted value, but we still want masking rules to apply to it, so it has to be provided to the connection model as a SecretStr.

Line 76 fetches the config information from the key vault.

Next, we instantiate the state-machine that will do the work.

```python linenums="80"
        # Bundle up the model the machine expects and create the machine.
        state = StateBackupDatabases(
            client_name=client_name, backup_config=backup_config, eoy_month=eoy_month
        )
        machine = MachineBackupDatabases(logger=logger, state=state)
```

We build the state object, StateBackupDatabases, which contains:

- client_name is the name of the client being backed up.
- backup_config the config information from the key vault.
- eoy_month is a numeric value indicating which month is considered to be the client's end-of-year month.

We then instantiate MachineBackupDatabases with the application logger and its defining state object.

Next we instantiate an End-Point object.

```python linenums="86"
        # Use the end-point that wraps the machine with auto-mounting/unmounting
        # of the file share.
        end_point = DynamicMountingEndPoint(
            logger=logger,
            state_dynamic_mount=StateDynamicMount(
                client_name=client_name,
                backup_config=backup_config,
                machine_to_wrap=machine,
            ),
        )
```

In this case, we are using dynamic mounting of the file-share, so we use the DynamicMountingEndPoint.  As parameters, it expects:

- logger is the application logger.
- state_dynamic_mount is a state object for MachineDynamicMount, which expects:
    - client_name is the name of the client being backed up.
    - backup_config is the config information from the key vault.
    - machine_to_wrap is the instance of the state-machine to execute inbetween mounting and unmounting of the file-share.

Finally, we execute the end-point which, in turn, will execute the service.

```python linenums="96"
        end_point.execute()
```
