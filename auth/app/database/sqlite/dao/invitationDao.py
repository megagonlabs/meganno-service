from datetime import datetime, timezone

import pydash
from app.database.sqlite import database
from app.database.sqlite.dto.invitationDto import InvitationDto


class InvitationDao:
    def add(
        code: str,
        invitation_code: str,
        single_use: bool,
        note: str,
        created_on: datetime,
        expires_on: datetime,
        role_id: int,
    ):
        """
        add invitation
        Parameters
        ----------
        code :str
            either same as invitation_code or leading/tailing substring of invitation code (for duplicate check)
        invitation_code : str
            complete/full invitation code for user registration
        single_use : bool
            if true, invalidate after 1 use; otherwise, can be used multiple times to register different account (no limit).
        note : str
        created_on : datetime
        expires_on : datetime
        rold_id : int
            rold id for the registered user
        """
        invitation = InvitationDto(
            code=code,
            invitation_code=invitation_code,
            single_use=single_use,
            created_on=created_on,
            expires_on=expires_on,
            note=note,
            role_id=role_id,
        )
        database.session.add(invitation)
        database.session.commit()
        return invitation

    def get_invitation_by_code(code: str):
        """
        retrieve invitation by code column
        Parameters
        ----------
        code : str
        """
        return InvitationDto.query.filter(InvitationDto.code == code).one_or_none()

    def get_invitations(active: bool):
        """
        Get all invitations based on filter: active
        None: all invitations
        True: only active invitations
        False: only expired invitations

        Parameters
        ----------
        active : bool
        """
        if pydash.is_none(active):
            return (
                InvitationDto.query.filter()
                .order_by(InvitationDto.created_on.desc())
                .all()
            )
        return (
            InvitationDto.query.filter(
                InvitationDto.expires_on > datetime.now(timezone.utc)
                if active
                else InvitationDto.expires_on <= datetime.now(timezone.utc)
            )
            .order_by(InvitationDto.created_on.desc())
            .all()
        )

    def get_invitation_by_invitation_code(invitation_code: str):
        """
        retrieve invitation by invitation_code column
        Parameters
        ----------
        invitation_code : str
        """
        return InvitationDto.query.filter(
            InvitationDto.invitation_code == invitation_code
        ).one_or_none()

    def update_invitation_by_id(id: str, fields: dict):
        """
        update invitation with passed in fields
        Parameters
        ----------
        fields : dict
            dictionary object with key/value pair being column_name/column_value
        """
        InvitationDto.query.filter(InvitationDto.id == id).update(fields)
        database.session.commit()
