from datetime import datetime

import pydash
from app.database.sqlite import database
from app.database.sqlite.dto.tokenDto import TokenDto
from sqlalchemy import not_


class TokenDao:
    def list_tokens(created_by: str, job: bool, ids: list):
        """
        get a list of access/job tokens for user (created_by) with ids filter
        Parameters
        ----------
        created_by : str
            user id (UUID)
        job : bool
            if true, return job only tokens; otherwise, non-job only tokens
        ids : list
            subset filter for returning user tokens with speicified ids
        """
        return (
            TokenDto.query.filter(
                TokenDto.created_by == created_by,
                TokenDto.id_token != True,
                (
                    TokenDto.user_id.startswith("job_")
                    if job
                    else not_(TokenDto.user_id.startswith("job_"))
                ),
                (
                    TokenDto.id.in_(ids)
                    if pydash.is_list(ids) and not pydash.is_empty(ids)
                    else 1 == 1
                ),
            )
            .order_by(TokenDto.created_on.desc())
            .all()
        )

    def delete_token_by(id: int):
        """
        delete token by id
        Parameters
        ----------
        id : int
            integer (primary key of token table)
        """
        token = TokenDto.query.get(id)
        database.session.delete(token)
        database.session.commit()

    def add(
        user_id: str,
        id_token: bool,
        note: str,
        created_by: str,
        created_on: datetime,
        expires_on: datetime,
        has_expiration: bool,
        session_id: str,
        hash: str,
    ):
        """
        add new token
        Parameters
        ----------
        user_id : str
            the user identity for this token; user_id does not have to be an actual human user (example: ids with "job_" prefix).
        id_token : bool
            if true, it should be expired after 1 hour
        note : str
        created_by : str
            user id of the user who created this token
        created_on : datetime
        expires_on : datetime
        has_expiration : bool
            for convinience; if true, expires_on should be 100 years after the created_on time.
        session_id : str
            secondary unique identifier for token
        hash : str
            hashed value of an encryted token using bcrypt
        """
        token = TokenDto(
            created_by=created_by,
            session_id=session_id,
            user_id=user_id,
            created_on=created_on,
            expires_on=expires_on,
            has_expiration=has_expiration,
            id_token=id_token,
            note=note,
            hash=hash,
        )
        database.session.add(token)
        database.session.commit()
        return token

    def get_token(user_id: str, session_id: str):
        """
        get specific token by user_id and session_id; this is used for token verification process after decrypting client token to extract user_id and session_id information
        Parameters
        ----------
        user_id : str
        session_id : str
        """
        return TokenDto.query.filter(
            TokenDto.user_id == user_id, TokenDto.session_id == session_id
        ).one_or_none()
