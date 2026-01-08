# third party imports
from pydantic import SecretStr

# repository imports
from repository.shell.delimited import (
    CommaDelimited,
    EqualDelimited,
    SpaceDelimited,
)

# local imports
from .command import Command


class FileSystem(Command):
    """
    Commonly used file system commands.
    """

    @classmethod
    def chown(cls, *, path: str, user: str, group: str):
        """
        Change ownership of *path* for *user*:*group*.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=("sudo", "-S", "chown", "-R", f"{user}:{group}", path)
        )

        cls.execute(command=command)

    @classmethod
    def is_mounted(cls, *, path: str) -> bool:
        """
        Determine whether the path is mounted to a file share.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(line=("findmnt", "-T", path))

        result = cls.execute(command=command)

        lines = result.stdout.split("\n")
        source_start = lines[0].find("SOURCE")

        return lines[1][source_start:].startswith("//")

    @classmethod
    def mount_storage(
        cls,
        *,
        unc: str,
        mount_path: str,
        account_name: str,
        account_key: SecretStr,
        user_id: str,
        actimeo: int = 30,
    ):
        """
        Mount a file share on a storage account.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "sudo",
                "-S",
                "mount",
                "-t",
                "cifs",
                unc,
                mount_path,
                "-o",
                CommaDelimited(
                    line=(
                        EqualDelimited(left="username", right=account_name),
                        EqualDelimited(left="password", right=account_key),
                        "serverino",
                        "nosharesock",
                        EqualDelimited(left="actimeo", right=str(actimeo)),
                        "mfsymlinks",
                        EqualDelimited(left="uid", right=user_id),
                        EqualDelimited(left="gid", right=user_id),
                    )
                ),
            )
        )

        cls.execute(command=command)

    @classmethod
    def unmount_storage(cls, *, mount_path: str):
        """
        Unmount a storage account.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(line=("sudo", "-S", "umount", "-l", mount_path))

        cls.execute(command=command)

    @classmethod
    def user_id(cls) -> str:
        """
        Fetch the id of the current user.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(line=("id", "-u"))

        result = cls.execute(command=command)

        return result.stdout.strip()

    @classmethod
    def what_is_mounted(cls, *, path: str) -> str:
        """
        Report what a path is mounted to.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(line=("findmnt", "-T", path))

        result = cls.execute(command=command)

        lines = result.stdout.split("\n")
        source_start = lines[0].find("SOURCE")
        source_end = lines[0].find("FSTYPE")

        return lines[1][source_start:source_end].strip()
