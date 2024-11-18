# Restore

The prerequisites are:

1. Encrypt Config has been populated
2. Decrypt Config has been populated
2. File Share for storing backups has been created.
3. Archive file to be restored exists.

The sequence diagram for the happy-path life cycle of a restore job is presented below:

``` mermaid
sequenceDiagram
  autonumber
  Authorized Person->>Restore End Point: start
  Restore End Point->>Encrypt Config: fetch config info
  Encrypt Config->>Restore End Point: return config info
  Restore End Point->>Backup Config: fetch config info
  Backup Config->>Restore End Point: return config info
  Restore End Point->>Restore Service: start
  Restore Service->>File Share: mount file share
  File Share->>Restore Service: mounted

  Restore Service->>File Share: requested archive file exists?
  File Share->>Restore Service: yes
  Restore Service->>gpg: private key installed?
  gpg->>Restore Service: no
  Restore Service->>gpg: install private key
  gpg->>Restore Service: private key installed
  Restore Service->>File Share: create restore directory
  File Share->>Restore Service: directory created
  Restore Service->>File Share: copy encrypted archive to restore directory
  File Share->>Restore Service: file copied
  Restore Service->>gpg: decrypt file
  gpg->>Restore Service: file decrypted

  Restore Service->>File Share: unmount file share
  File Share->>Restore Service: file share unmounted
  Restore Service->>Restore End Point: report any failures
  Restore End Point->>Authenticated Person: report any failures
```
