# Config Secrets

The secrets module provides a couple of scripts for managing secrets in config files.

The primary intention of adding secrets to the config file system was for use in dev environments
where you're trying to figure out how to get something to work, and you quick-and-dirty cram
clear-text credentials into code.  Then you forget about them and check them into the repository.

!!! danger
    Never, never, ever check clear-text credentials into a source-code repository.  Finding them there should
    be treated as a Sev 1 Security Incident that requires changing the credentials immediately.  Source-code
    repositories are considered low-hanging fruit for criminals searching for credentials.  Nobody ever
    runs the level of intrusion-detection monitoring on source-code repositories they would in a prod
    environment.  Once something has been checked into the repository, it's really hard to remove.  The whole
    purpose of a version management system is to keep a history of everything that has changed.

Anyway, the config secrets expect to find an encryption key in /etc/fernet.key.

The key can be generated using:

``` bash
python -m secrets.generate_key fernet.key
```

Then:

``` bash
sudo mv fernet.key /etc
```

Usage within code:

``` python
from from state_machine.config import Config

config = Config()
secret = config.secrets.category_name.secret_name
```

The secrets.yaml file is excluded by gitignore, and it is assumed everybody will generate their own
key and populate their own version of any secret information they need to encrypt.