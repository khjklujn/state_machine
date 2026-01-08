# application imports
from repository.shell.delimited import SpaceDelimited

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

    @classmethod
    def xjf(cls, *, tarball: str, path: str):
        """
        Untars the tarball specified by *file_name* to the location specified by *path*.  Expects a tarball with bzip compression.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(line=("tar", "-xjf", tarball, "-C", path))

        cls.execute(command=command)
