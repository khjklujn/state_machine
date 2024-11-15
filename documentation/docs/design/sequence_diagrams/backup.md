# Backups

The prerequisites are:

1. Encrypt Config has been populated
2. File Share for storing files has been created.

The sequence diagram for the happy-path life cycle of a archive job is presented below:

``` mermaid
sequenceDiagram
  autonumber
  Control-M->>Archive End Point: start
  Archive End Point->>Encrypt Config: fetch config info
  Encrypt Config->>Archive End Point: return config info
  Archive End Point->>Archive Service: start
  Archive Service->>File Share: mount file share
  File Share->>Archive Service: mounted
  Archive Service->>File Share: create intermediate directory
  File Share->>Archive Service: directory created
  Archive Service->>Directory: get list of files
  Directory->>Archive Service: return list of files
  loop Each File
    Archive Service->>cp: copy file
    cp->>Archive Service: file copied
    Archive Service->>gpg: is public installed?
    gpg->>Archive Service: no
    Archive Service->>gpg: install public key
    gpg->>Archive Service: key installed
    Archive Service->>gpg: encrypt file
    gpg->>Archive Service: file encrypted
    Archive Service->>File Share: move to long-term storage
    File Share->>Archive Service: encrypted file in long-term storage
    Archive Service->>gpg: delete public key
    gpg->>Archive Service: public key deleted
  end
  Archive Service->>File Share: remove intermediate directory
  File Share->>Archive Service: intermediate directory removed
  intermediate Service->>File Share: unmount file share
  File Share->>Archive Service: file share unmounted
  Archive Service->>Archive End Point: report any failures
  Archive End Point->>Control-M: report any failures
  Control-M->>Alerting: report any failures
```
