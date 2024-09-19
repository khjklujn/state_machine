# standard library imports
import os
from typing import Union

# third party imports
from ruamel.yaml import YAML

# local imports
from .attribute_dict import AttributeDict
from .secrets import Secrets


class Config(AttributeDict):
    """
    Persists configuration definitions.  Defaults to a config.yaml files in the projects folder.  It will
    recursively search up the folders and use the first config.yaml file it finds in the folder structure.

    Encrypted secrets are stored in a separate secrets.yaml file.
    """

    filename = "config.yaml"

    @classmethod
    def config_file(cls, config_project_path: str = "") -> str:
        """
        Walks up the folder structure searching for the requested config.yaml file.
        Will create the file if it does not exists.
        """
        config_path = os.path.join("./", config_project_path)
        config_filename = os.path.join(config_path, cls.filename)

        if os.path.exists(config_filename):
            return config_filename
        elif config_project_path == "" and config_path == "./":
            with open(config_filename, "w"):
                pass
            return config_filename
        elif config_project_path == "":
            return cls.config_file(os.path.split(config_path)[0])
        else:
            with open(config_filename, "w"):
                pass
            return config_filename

    def __init__(self, config_path: Union[dict, str] = ""):
        if isinstance(config_path, str) and not config_path:
            yaml = YAML()
            self._config_filename = self.config_file(config_path)
            with open(self._config_filename, "r") as file_in:
                configurations = yaml.load(file_in)
        elif isinstance(config_path, str):
            yaml = YAML()
            self._config_filename = config_path
            with open(self._config_filename, "r") as file_in:
                configurations = yaml.load(file_in)
        else:
            configurations = config_path

        if configurations is None:
            configurations = {}

        super().__init__(configurations)

        if isinstance(config_path, str):
            self._secrets = Secrets(config_path)
        else:
            self._secrets = Secrets()

    def set(self, section: str, key: str, value: str):
        """
        Adds or overwrites a configuration value.
        """
        if section in self:
            self[section].add_attribute(key, value)
        else:
            self.add_attribute(section, {key: value})

        with open(self._config_filename, "w") as file_out:
            yaml = YAML()
            yaml.dump(self.as_dict(), file_out)

    @property
    def from_file(self) -> str:
        """
        The config.yaml file the configurations were loaded from.
        """
        return self._config_filename

    @property
    def secrets(self) -> Secrets:
        """
        Access to the encrypted secrets.
        """
        return self._secrets
