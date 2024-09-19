"""
Convenience wrappers for performing encryption and decryption actions.
"""

# third party imports
from cryptography.fernet import Fernet


def decrypt(value: str) -> str:
    """
    Decrypt the *value*.  Assumes a key has been installed in /etc/fernet.key
    """
    with open("/etc/fernet.key") as file_in:
        key = file_in.read()

    fernet = Fernet(bytes(key.encode("utf-8")))
    return fernet.decrypt(bytes(value.encode("utf-8"))).decode("utf-8")


def encrypt(value: str) -> str:
    """
    Encrypt the *value*.  Assumes a key has been installed in /etc/fernet.key.
    """
    with open("/etc/fernet.key") as file_in:
        key = file_in.read()

    fernet = Fernet(bytes(key.encode("utf-8")))
    return fernet.encrypt(bytes(value.encode("utf-8"))).decode("utf-8")
