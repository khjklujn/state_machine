"""
Generate an encryption key.  Will error out if trying to overwrite an existing key.

``` bash
python -m secret.generate_key file_name
```

positional:
    - file_name: Name of the file to place the key in--must not already exist.
"""

# standard library imports
import argparse
import os

# third party imports
from cryptography.fernet import Fernet


def generate_key(file_name: str):
    """
    Generate a Fernet key.
    """
    if os.path.exists(file_name):
        print(f"{file_name} already exists")
        exit(1)
    key = Fernet.generate_key()
    with open(file_name, "w") as file_out:
        file_out.write(key.decode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m secret.generate_key",
        description="Generate a Fernet key for symmetric encrpytion.",
    )
    parser.add_argument(
        "file_name",
        help="Name of the file to place the key in--must not already exist.",
        type=str,
    )

    args = parser.parse_args()

    generate_key(args.file_name)
