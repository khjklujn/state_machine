# standard library imports
import os
from typing import Union

# third party imports
from ruamel.yaml import YAML

# local imports
from .encrypted_attribute_dict import EncryptedAttributeDict


class Secrets(EncryptedAttributeDict):
    """
    Persists encrypted configuration definitions.  Defaults to a secrets.yaml files in the project's folder.  It will
    recursively search up the folders and use the first secrets.yaml file it finds in the folder structure.
    """

    filename = "secrets.yaml"

    @classmethod
    def config_file(cls, config_project_path: str = "") -> str:
        """
        Walks up the folder structure searching for the requested secrets.yaml file.
        Will create the file if it does not exists.
        """
        config_path = os.path.join("./", config_project_path)
        config_filename = os.path.join(config_path, cls.filename)

        if os.path.exists(config_filename):
            return config_filename
        elif config_path == "./":
            with open(config_filename, "w"):
                pass
            return config_filename
        else:
            return cls.config_file(os.path.split(config_path)[0])

    def __init__(self, config_path: Union[dict, str] = ""):
        """
        :param config_path: When a string is passed in, it's the path to the secrets.yaml file. When a dictionary is passed in, it's the inital structure.
        """
        yaml = YAML()
        if isinstance(config_path, str):
            self._config_filename = self.config_file(config_path)
            with open(self._config_filename, "r") as file_in:
                configurations = yaml.load(file_in)
        else:
            configurations = config_path

        if configurations is None:
            configurations = {}

        super().__init__(configurations)

    def set(self, section: str, key: str, value: str):
        """
        Adds or overwrites a secret value.
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
        return self._config_filename
