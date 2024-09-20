"""
Sets a secret value in the master secrets.yaml file.

Command line usage:

``` bash
python -m secret.set
```

prompts:
    - Category: The group the secret belongs to.
    - Name: The name of the secret.
    - Secret: The value of the secret.
"""

# standard library imports
from getpass import getpass

# application imports
from state_machine.config import Config


def set():
    """
    Sets an encrypted value in the secrets config file.
    """
    category = input("Category: ")
    name = input("Name: ")
    secret = getpass("Secret: ")

    config = Config()
    config.secrets.set(category, name, secret)


if __name__ == "__main__":
    set()
