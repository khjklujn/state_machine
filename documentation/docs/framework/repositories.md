# Repositories

One of the key organizational elements in a code base is differentiating between code whose behavior is completely under your control and the code that depends on external systems, which may or may not do what you want them to.

External systems are anything that can fail for reasons unrelated to your code:  File systems, calls across a network, databases, APIs...

Interactions with external systems are placed in the Repository layer.  The reason for doing this is testability.  You cannot setup a testing environment where you could test all of the possible ways a network connection could fail, so you isolate the code that depends on interacting with things across a network, and in the unit tests, you simulate networking failures through what is known as "mocking".  In the tests, the Repository layer code is replaced with code that simulates both successful interactions and failing interactions with the external system.

Code in the repository layer is stupid in the sense that it does not make any decisions.  It simply receives a request, forwards the request to the external system, and returns the results.  It doesn't attempt to interpret what is going on.  All of the meaningful interpretations of the interactions with the external system and decisions about what to do next take place in the Service layer.

Looking at an example:

```python linenums="1"
# standard library imports
import os
import subprocess

# application imports
from long_term_storage.repository.shell.delimited import SpaceDelimited

# local imports
from .command import Command


class Tar(Command):
    """
    Interations with tar.
    """

    @classmethod
    def cjf_with_removal(
        cls, *, directory_to_run_in: str, directory_to_tar: str, tarball: str
    ):
        """
        Tars the directory specified by *directory_to_tar* located in *intermediate_path* to the tarball specified by *tarball*.
        Uses bzip compression and removes *directory_to_tar* when complete.  Runs in the working directory specified by
        *directory_to_run_in*.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=("tar", "-cjf", directory_to_tar, tarball, "--remove-files")
        )

        cls.execute(command=command, cwd=directory_to_run_in)

    @classmethod
    def xjf(cls, *, tarball: str, path: str):
        """
        Untars the tarball specified by *file_name* to the location specified by *path*.  Expects a tarball with bzip compression.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(line=("tar", "-xjf", tarball, "-C", path))

        cls.execute(command=command)
```

This is a Repository for interacting with the tar command line tool.  The first thing we see is "class Tar(Command)" is inheriting the Command class, so we'll take a look at the definition of Command.

```python linenums="1"
# standard library imports
from datetime import datetime, UTC
from os import environ, _Environ
import subprocess


# repository imports
from state_machine import AbstractRepository
from long_term_storage.repository.shell.delimited import SpaceDelimited


class Command(AbstractRepository):
    """
    Base class for executing command line actions.
    """

    @classmethod
    def execute(
        cls,
        *,
        command: SpaceDelimited,
        cwd: str | None = None,
        env: _Environ = environ,
        text: bool = True,
        start_new_session: bool = False,
        input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        Executes the command line action.

        raises:
            Exception: If exit code is not zero.
        """
        start_time = datetime.now(UTC)
        cls.logger.debug(f"  {command} - Started")

        result = subprocess.run(
            command.get_secret_value(),
            capture_output=True,
            env=env,
            cwd=cwd,
            text=text,
            start_new_session=start_new_session,
            input=input,
        )

        end_time = datetime.now(UTC)
        if result.returncode != 0:
            cls.logger.debug(
                f"  {command} - Error: {result.returncode} - Runtime: {end_time - start_time}"
            )
            raise Exception(result.stderr)

        cls.logger.debug(f"  {command} - Completed - Runtime: {end_time - start_time}")

        return result
```

The Command class is inheriting AbstractRepository, we'll take a quick look at that as well.

```python linenums="1"
# standard library imports
from typing import Any

# local imports
from .logger import Logger


class AbstractRepository:
    """
    Abstract base class for repositories.

    *logger* will be injected when accessing a repository action from a Dependency set of repositories for a machine.
    """

    logger: Logger

    @classmethod
    def execute(cls) -> Any:
        """
        Needs to be overriden in subclasses.  All actions taken by a repository should be executed in this method as
        this is the assumed mocking point for unit tests.
        """
        raise NotImplementedError()
```

AbstractRepository is the base class for all Repositories.  It has three purposes:

- Make sure a Repository has access to the application's logger.
- Centralizes the "go do something" code in the execute method (gives us a place to standardize the debug logging for a Repository).
- Allows for identification of a Repository class as implementing a Repository, because there is some run-time dependency injection we will want to do for Repositories (covered in the Dependency Injection section).

To serve these purposes, it provides a logger property and an abstract method called execute.

Also, another thing to note is that we are using classmethods to implement the Respositories.  The Repository classes do not need to be instantiated.  The only encapsulated contextual item they contain is the logger, which should be they same for any given application.

Moving back to the Command class, the execute method has been given a concrete implementation of the abstract method inherited from AbstractRepository.

```python linenums="17"
    @classmethod
    def execute(
        cls,
        *,
        command: SpaceDelimited,
        cwd: str | None = None,
        env: _Environ = environ,
        start_new_session: bool = False,
        input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        Executes the command line action.

        raises:
            Exception: If exit code is not zero.
        """
        start_time = datetime.now(UTC)
        cls.logger.debug(f"  {command} - Started")

        result = subprocess.run(
            command.get_secret_value(),
            capture_output=True,
            env=env,
            cwd=cwd,
            start_new_session=start_new_session,
            input=input,
        )

        end_time = datetime.now(UTC)
        if result.returncode != 0:
            cls.logger.debug(
                f"  {command} - Error: {result.returncode} - Runtime: {end_time - start_time}"
            )
            raise Exception(result.stderr)

        cls.logger.debug(f"  {command} - Completed - Runtime: {end_time - start_time}")

        return result
```

The execute method generalizes interacting with command line tools and standardizes the debug logging for such interactions.  It has a number of parameters that are needed to support the different needs of different tools.

- command is the only required parameter, and it expects to receive a SpaceDelimited object.
- env is the set of environmental variables that will be available to the command line tool. Defaults to the same environment the calling process has.
- cwd is the working directory for executing the command line tool. Defaults to the same working directory of the calling process.
- start_new_session is a flag indicating whether execution should take place as a background process (putting "&" at the end of a command line call). Default to no.
- input is a value to be used should the command line tool prompt for more information. Placing secret information in command line parameters should be avoided if possible--all command line parameters are readable in clear text while the process is running. This parameter can sometimes be used to answer password prompts. Defaults to None.

The first thing done is to record the start time of the action. When a system is experiencing weirdness, the ability to look at the log files and quickly determine "that looks like it's taking too much or too little time" without having to do calculations based on the time stamps of the entries greatly speeds up the diagnosis. Computers are good at computing, so let's just go ahead and have the computer do the calculations and report the how long things took to execute in the log.

Next we use Python's subprocess.run function to submit the request to the OS, which bypasses the need to worry about the escaping, quoting, and all of the other nastiness encountered when trying to craft dynamic bash commands.

We check the exit code, and if it isn't zero, we raise and exception with the contents of stderr as the message.  This is not appropriate behavior for _all_ command line tools.  Some are not posix compliant and have non-zero exit-codes that actually succeeded.  It's also possible that some may place sensitive information in stderr that should not be logged.  If a command line tool is found that exhibits either of these behaviors, the execute method will need to be overriden in the Repository class to accommodate the unexpected behavior ot the command line tool.

Finally, we log the runtime and return the result, which will include the contents of stdout.

So, moving back to our original Repository example, the Tar class, let's take a look at the first method.

```python linenums="17"
    @classmethod
    def cjf_with_removal(
        cls, *, directory_to_run_in: str, directory_to_tar: str, tarball: str
    ):
        """
        Tars the directory specified by *directory_to_tar* located in *directory_to_run_in* to the tarball specified by *tarball*.
        Uses bzip compression and removes *directory_to_tar* when complete.  Runs in the working directory specified by
        *directory_to_run_in*.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=("tar", "-cjf", directory_to_tar, tarball, "--remove-files")
        )

        cls.execute(command=command, cwd=directory_to_run_in)
```

The parameters are:

- directory_to_run_in: tar records the full path of what is being tarred, and since when we use this file in a restore process, we want it to untar to a different directory path than where it was during the backup, the only thing we want in the tarball path is just the directory that is being tarred.  To accomplish that, tar will need to be executed in the directory the directory being tarred lives in.  This parameter provides the working directory to use when invoking tar.
- directory_to_tar is the name of the directory we will be tarring.
- tarball is the name of the resulting tarball file.

The command line that will be executed is something like:

```bash
tar -cjf some-directory-that-is-being-tarred tarball.tbz --remove-files
```

The cjf parameter means:

- c: We're creating a tarball.
- j: Use bzip for compression.
- f: The next parameter will be what wer are tarring.

The --remove-files tells tar to remove the directory that was tarred after tarring has completed.

We then call the execute method supplying the command line definition and setting cwd for the process to the directory we want tar to think it's running in.

The second method is for untarring.

```python linenums="36"
    @classmethod
    def xjf(cls, *, tarball: str, path: str):
        """
        Untars the tarball specified by *file_name* to the location specified by *path*.  Expects a tarball with bzip compression.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(line=("tar", "-xjf", tarball, "-C", path))

        cls.execute(command=command)
```

The parameters are:

- tarball is the name of the tar file to be untarred.
- path is directory the untarred results should live in.

The command line that will be executed is something like:

```bash
tar -xjf tarball.tbz -C /path/to/some/location
```

The parameters for tar are:

- x: We're extracting contenets from a tarball.
- j: The tarball was compressed using bzip.
- f: The next parameter will be the name of the tarball.
- C: We will be untarring to a different location than it was originally tarred from.

