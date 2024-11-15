# third party imports
from pydantic import BaseModel


class GpgKeyModel(BaseModel):
    algo: str
    cap: str
    compliance: str
    date: str
    dummy: str
    expires: str
    fingerprint: str
    flag: str
    hash: str
    issuer: str
    keygrip: str
    keyid: str
    length: str
    origin: str
    ownertrust: str
    sig: str
    sigs: list[str]
    subkeys: list[str]
    token: str
    trust: str
    type: str
    uids: list[str]
    updated: str
