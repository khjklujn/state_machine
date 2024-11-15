# standard library imports
from datetime import datetime
from typing import Callable

# third party imports
from gnupg import GenKey, GPG
from pydantic import SecretStr

# application imports
from state_machine import AbstractRepository

# local imports
from .gpg_key_model import GpgKeyModel


class Gpg(AbstractRepository):
    """
    Interactions with gpg.
    """

    @classmethod
    def execute(cls, function: Callable, *args, **kwargs):
        """Executes the gpg action."""
        start_time = datetime.utcnow()
        cls.logger.debug(f"  {function.__name__} - Started")

        results = function(*args, **kwargs)

        end_time = datetime.utcnow()
        cls.logger.debug(
            f"  {function.__name__} - Completed - Runtime: {end_time - start_time}"
        )

        return results

    @classmethod
    def decrypt(cls, *, from_file: str, to_file: str, passphrase: SecretStr):
        """
        Decrypt file *from_file* to *to_file*.
        """
        gpg = GPG(verbose=True)
        with open(from_file, "rb") as file_in:
            results = cls.execute(
                gpg.decrypt_file,
                file_in,
                passphrase=passphrase.get_secret_value(),
                output=to_file,
                always_trust=True,
            )
            if not results.ok:
                raise Exception(f"encryption failed: {results.message}")

    @classmethod
    def encrypt(cls, *, key_name: str, from_file: str, to_file: str):
        """
        Encrypt file *from_file* to *to_file* using the public key *key_name*.
        """
        gpg = GPG()
        with open(from_file, "rb") as file_in:
            results = cls.execute(gpg.encrypt_file, file_in, key_name, output=to_file)
        if not results.ok:
            raise Exception(f"encryption failed: {results}")

    @classmethod
    def list_public_keys(cls) -> list[GpgKeyModel]:
        """
        Retrieve a list of the public keys.
        """
        gpg = GPG()
        return [GpgKeyModel(**record) for record in cls.execute(gpg.list_keys)]

    @classmethod
    def list_private_keys(cls) -> list[GpgKeyModel]:
        """
        Retrieve a list of the private keys.
        """
        gpg = GPG()
        return [GpgKeyModel(**record) for record in cls.execute(gpg.list_keys, True)]

    @classmethod
    def create_key(cls, *, key_name: str, passphrase: SecretStr) -> GenKey:
        """
        Create private and public keys.
        """
        gpg = GPG()
        input_data = gpg.gen_key_input(
            name_real=key_name,
            passphrase=passphrase.get_secret_value(),
            name_email=f"{key_name}@finastra.com",
        )
        return cls.execute(gpg.gen_key, input_data)

    @classmethod
    def delete_public_key(cls, *, key_name: str):
        """
        Delete a public key.
        """
        finger_prints = [
            key.fingerprint
            for key in cls.list_public_keys()
            if key.uids[0].split(" ")[0] == key_name
        ]
        if len(finger_prints) == 0:
            raise Exception(f"{key_name} not found")
        elif len(finger_prints) == 1:
            gpg = GPG()
            cls.execute(gpg.delete_keys, finger_prints[0])
        else:
            raise Exception(f"multiple {key_name} found")

    @classmethod
    def delete_private_key(cls, *, key_name: str, passphrase: SecretStr):
        """
        Delete a private key.
        """
        finger_prints = [
            key.fingerprint
            for key in cls.list_public_keys()
            if key.uids[0].split(" ")[0] == key_name
        ]
        if len(finger_prints) == 0:
            raise Exception(f"{key_name} not found")
        elif len(finger_prints) == 1:
            gpg = GPG()
            cls.execute(
                gpg.delete_keys,
                finger_prints[0],
                secret=True,
                passphrase=passphrase.get_secret_value(),
            )
        else:
            raise Exception(f"multiple {key_name} found")

    @classmethod
    def get_public_key(cls, *, key_name: str) -> str:
        """
        Retrieve the base64 definition of the public key.
        """
        gpg = GPG()
        return cls.execute(gpg.export_keys, key_name)

    @classmethod
    def get_private_key(cls, *, key_name: str, passphrase: SecretStr) -> SecretStr:
        """
        Retrieve the base64 definition of the private key.
        """
        gpg = GPG()
        return SecretStr(
            secret_value=cls.execute(
                gpg.export_keys,
                key_name,
                secret=True,
                passphrase=passphrase.get_secret_value(),
            )
        )

    @classmethod
    def import_public_key(cls, *, base64: str):
        """
        Install a public key.
        """
        gpg = GPG()
        result = cls.execute(gpg.import_keys, base64)
        if result.count == 0:
            raise Exception("No keys imported")

    @classmethod
    def import_private_key(cls, *, base64: SecretStr, passphrase: SecretStr):
        """
        Install a public key.
        """
        gpg = GPG()
        result = cls.execute(
            gpg.import_keys,
            base64.get_secret_value(),
            passphrase=passphrase.get_secret_value(),
        )
        if result.count == 0:
            raise Exception("No keys imported")

    @classmethod
    def private_key_exists(cls, *, key_name: str) -> bool:
        """Check whether the private key is installed."""
        finger_prints = [
            key.fingerprint
            for key in cls.list_private_keys()
            if key.uids[0].split(" ")[0] == key_name
        ]
        if len(finger_prints) == 0:
            return False
        else:
            return True

    @classmethod
    def public_key_exists(cls, *, key_name: str) -> bool:
        """Check whether the public key is installed."""
        finger_prints = [
            key.fingerprint
            for key in cls.list_public_keys()
            if key.uids[0].split(" ")[0] == key_name
        ]
        if len(finger_prints) == 0:
            return False
        else:
            return True

    @classmethod
    def trust_key(cls, *, key_name: str, trust_level: str = "TRUST_ULTIMATE"):
        """
        Trust a public key.
        """
        finger_prints = [
            key.fingerprint
            for key in cls.list_public_keys()
            if key.uids[0].split(" ")[0] == key_name
        ]
        if len(finger_prints) == 0:
            raise Exception(f"{key_name} not found")
        elif len(finger_prints) == 1:
            gpg = GPG()
            cls.execute(gpg.trust_keys, finger_prints[0], trust_level)
        else:
            raise Exception(f"multiple {key_name} found")
