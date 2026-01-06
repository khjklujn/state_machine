# standard library
from datetime import datetime, UTC
import os
from shutil import copy2, move
from typing import Any, Callable

# application imports
from state_machine import AbstractRepository


class FileManager(AbstractRepository):
    """
    File manipulations.
    """

    @classmethod
    def execute(cls, function: Callable, *args, **kwargs) -> Any:
        """
        Executes a file management operation.
        """
        start_time = datetime.now(UTC)
        cls.logger.debug(f"  {function.__name__} {args} {kwargs} - Started")

        results = function(*args, **kwargs)

        end_time = datetime.now(UTC)
        cls.logger.debug(
            f"  {function.__name__} {args} {kwargs} - Completed - Runtime: {end_time - start_time}"
        )

        return results

    @classmethod
    def all_files_in_directory(cls, *, path) -> list[str]:
        """
        Recursively walks a directory and compiles a list of all of the files found.
        """
        ret = []
        for root, _, files in cls.execute(os.walk, path):
            for file_name in files:
                ret.append(os.path.join(root, file_name))
        return ret

    @classmethod
    def copy(cls, *, from_path: str, to_path: str):
        """Copy file from *from_path* to *to_path*."""
        cls.execute(copy2, from_path, to_path)

    @classmethod
    def exists(cls, *, path: str) -> bool:
        """Checks for the existence of *path* in the filesystem."""
        return cls.execute(os.path.exists, path)

    @classmethod
    def make_dir_if_not_exists(cls, *, path: str):
        """Creates the full directory *path* if it does not already exist."""
        cls.execute(os.makedirs, path, exist_ok=True)

    @classmethod
    def move(cls, *, from_path: str, to_path: str):
        """Moves file from *from_path* to *to_path*."""
        cls.execute(move, from_path, to_path)

    @classmethod
    def remove_directory_if_exists(cls, *, path: str):
        """
        Remove a file if it exists, otherwise fo nothing.
        """
        if cls.execute(os.path.exists, path):
            cls.execute(os.rmdir, path)

    @classmethod
    def remove_file_if_exists(cls, *, path: str):
        """
        Remove a file if it exists, otherwise do nothing.
        """
        if cls.execute(os.path.exists, path):
            cls.execute(os.remove, path)

    @classmethod
    def modification_time(cls, *, path: str) -> datetime:
        """Returns the modification date for the file in *path*."""
        return datetime.fromtimestamp(cls.execute(os.path.getmtime, path))
