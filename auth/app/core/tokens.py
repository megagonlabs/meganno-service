import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import pydash
from app.database.sqlite.dao.tokenDao import TokenDao
from app.database.sqlite.dto.tokenDto import TokenDto
from cryptography.fernet import Fernet

MEGANNO_ENCRYPTION_KEY = os.getenv("MEGANNO_ENCRYPTION_KEY", None)
if pydash.is_empty(MEGANNO_ENCRYPTION_KEY):
    raise Exception("Missing required envrionment variable: MEGANNO_ENCRYPTION_KEY.")
f = Fernet(MEGANNO_ENCRYPTION_KEY)


def encrypt(string):
    if type(string) is not bytes:
        string = str.encode(string)
    return f.encrypt(string)


def decrypt(string):
    if type(string) is not bytes:
        string = str.encode(string)
    return f.decrypt(string)


def create_token(
    user_id: str,
    id_token: bool = False,
    expiration_duration: int = 14,
    note: str = "",
    job: bool = False,
):
    """
    helper function for creating a token
    Parameters
    ----------
    user_id : str
        user identity associated with this token
    id_token : bool
        if true, expiration time will be forced to 1 hour, and user can use it to create non-id_token tokens
    expiration_duration : int
        default to 14 days. if 0, it turns to 100 years (theoratically no-expiration).
    note : str
    job : bool
        if true, user_id will have prefix: job_; this is only used to create job access tokens
    """
    token = {
        "created_by": user_id,
        "user_id": user_id,
        "created_on": datetime.now(timezone.utc),
        "expires_on": datetime.now(timezone.utc) + timedelta(days=expiration_duration),
        "has_expiration": True,
        "id_token": id_token,
        "note": note,
        "session_id": str(uuid.uuid4().hex),
    }
    if expiration_duration == 0:
        pydash.objects.set_(token, "has_expiration", False)
        pydash.objects.set_(
            token,
            "expires_on",
            datetime.now(timezone.utc) + timedelta(days=365 * 100),
        )
    if job:
        pydash.objects.set_(token, "user_id", f"job_{uuid.uuid1().hex}")
        pydash.objects.set_(
            token, "expires_on", datetime.now(timezone.utc) + timedelta(days=1.5)
        )
    elif id_token:
        pydash.objects.set_(
            token, "expires_on", datetime.now(timezone.utc) + timedelta(hours=1)
        )
    nonce = secrets.token_hex()
    concatenation = ",".join([token["user_id"], token["session_id"], nonce])
    # encrypt token, to give to user
    encrypted_concatenation = encrypt(concatenation)
    # hash the encrypted token
    hashed = bcrypt.hashpw(str.encode(concatenation), bcrypt.gensalt()).decode()
    database_token: TokenDto = TokenDao.add(
        user_id=token["user_id"],
        id_token=token["id_token"],
        note=token["note"],
        created_by=token["created_by"],
        created_on=token["created_on"],
        expires_on=token["expires_on"],
        has_expiration=token["has_expiration"],
        session_id=token["session_id"],
        hash=hashed,
    )
    return {
        "id": database_token.id,
        "token": encrypted_concatenation.decode(),
        "user_id": database_token.user_id,
        "expires_on": database_token.expires_on,
    }


def verify_token(token: str):
    """
    helper function for verifying the validity of a token
    Parameters
    ----------
    token : str
    """
    try:
        decrypted_payload = decrypt(string=token).decode()
        user_id, session_id, nonce = decrypted_payload.split(",")
        token: TokenDto = TokenDao.get_token(user_id=user_id, session_id=session_id)
        if not pydash.is_none(token):
            if token.expires_on.replace(tzinfo=timezone.utc) > datetime.now(
                timezone.utc
            ) and bcrypt.checkpw(str.encode(decrypted_payload), str.encode(token.hash)):
                return {"user_id": token.user_id, "id_token": token.id_token}
    except Exception:
        return None
