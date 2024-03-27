import time
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

import pydash
from app.constants import d7validate
from app.database.sqlite.dao.invitationDao import InvitationDao
from app.database.sqlite.dao.roleDao import RoleDao
from app.database.sqlite.dto.invitationDto import InvitationDto
from app.database.sqlite.dto.roleDto import RoleDto
from app.decorators import require_role
from app.flask_app import app
from app.json_validation.base import BaseValidation
from flask import jsonify, make_response, request


@app.get("/invitations")
@require_role("administrator")
def get_invitations():
    payload = {"active": request.json.get("active", None)}
    d7validate({"properties": {"active": BaseValidation.boolean_or_none}}, payload)
    invitations: list[InvitationDto] = InvitationDao.get_invitations(
        active=payload["active"]
    )
    result = []
    role_id_to_code = {}
    for invitation in invitations:
        if (
            not pydash.is_none(invitation.role_id)
            and invitation.role_id not in role_id_to_code
        ):
            role_id_to_code[invitation.role_id] = pydash.objects.get(
                RoleDao.get_role_by_id(id=invitation.role_id), "code", None
            )
        result.append(
            {
                "id": invitation.id,
                "note": invitation.note,
                "single_use": invitation.single_use,
                "invitation_code": invitation.invitation_code,
                "created_on": invitation.created_on,
                "expires_on": invitation.expires_on,
                "role_code": role_id_to_code[invitation.role_id],
            }
        )
    return make_response(jsonify(result))


@app.get("/invitations/<invitation_code>")
@require_role("administrator")
def get_invitation_by_invitation_code(invitation_code):
    payload = {"invitation_code": invitation_code}
    d7validate({"properties": {"invitation_code": BaseValidation.string}}, payload)
    invitation: InvitationDto = InvitationDao.get_invitation_by_invitation_code(
        payload["invitation_code"]
    )
    if pydash.is_none(invitation):
        return make_response("Invalid invitation code.", 400)
    return make_response(
        jsonify(
            {
                "id": invitation.id,
                "note": invitation.note,
                "single_use": invitation.single_use,
                "invitation_code": invitation.invitation_code,
                "created_on": invitation.created_on,
                "expires_on": invitation.expires_on,
                "role_code": pydash.objects.get(
                    RoleDao.get_role_by_id(id=invitation.role_id), "code", None
                ),
            }
        ),
        200,
    )


@app.post("/invitations")
@require_role("administrator")
def create_invitation():
    payload = {
        "code": request.json.get("code", ""),
        "single_use": request.json.get("single_use", True),
        "note": request.json.get("note", ""),
        "role_code": request.json.get("role_code", ""),
    }
    d7validate(
        {
            "properties": {
                "code": BaseValidation.string_or_none,
                "single_use": BaseValidation.boolean,
                "note": BaseValidation.string,
                "role_code": BaseValidation.string,
            }
        },
        payload,
    )
    try:
        prefix = str(int(time.time())) + "."
        # 10 characters (12 chars minus "==")
        code = token_urlsafe(7)
        if not pydash.is_empty(payload["code"]):
            # check for duplicate custom code
            database_invitation = InvitationDao.get_invitation_by_code(
                code=payload["code"]
            )
            if not pydash.is_none(database_invitation):
                return make_response("Duplicate custom code.", 400)
            code = payload["code"]
            prefix = ""
        role: RoleDto = RoleDao.get_role_by_code(payload["role_code"])
        invitation: InvitationDto = InvitationDao.add(
            code=code,
            invitation_code=prefix + code,
            single_use=payload["single_use"],
            note=payload["note"],
            created_on=datetime.now(timezone.utc),
            expires_on=datetime.now(timezone.utc) + timedelta(days=7),
            role_id=pydash.objects.get(role, "id", None),
        )
        return make_response(
            jsonify(
                {
                    "id": invitation.id,
                    "note": invitation.note,
                    "single_use": invitation.single_use,
                    "invitation_code": invitation.invitation_code,
                    "created_on": invitation.created_on,
                    "expires_on": invitation.expires_on,
                    "role_code": pydash.objects.get(
                        RoleDao.get_role_by_id(id=invitation.role_id), "code", None
                    ),
                }
            ),
            200,
        )
    except ValueError as ex:
        return make_response(str(ex), 400)


@app.put("/invitations")
@require_role("administrator")
def renew_invitation():
    # extend the expiration time by 1 week
    payload = {"id": request.json.get("id", "")}
    d7validate(
        {"properties": {"id": BaseValidation.string}},
        payload,
    )
    if not pydash.is_empty(payload["id"]):
        InvitationDao.update_invitation_by_id(
            id=payload["id"],
            fields={"expires_on": datetime.now(timezone.utc) + timedelta(days=7)},
        )
    return make_response(jsonify({}), 200)


@app.delete("/invitations")
@require_role("administrator")
def invalidate_invitation():
    # does not allow update of invitation once created
    # only allow invalidation by marking it as expired
    payload = {"id": request.json.get("id", "")}
    d7validate(
        {"properties": {"id": BaseValidation.string}},
        payload,
    )
    if not pydash.is_empty(payload["id"]):
        InvitationDao.update_invitation_by_id(
            id=payload["id"], fields={"expires_on": datetime.now(timezone.utc)}
        )
    return make_response(jsonify({}), 200)
