import uuid
from datetime import datetime, timezone

import bcrypt
import pydash
from app.constants import d7validate
from app.core.tokens import create_token
from app.database.sqlite.dao.invitationDao import InvitationDao
from app.database.sqlite.dao.userDao import UserDao
from app.database.sqlite.dto.invitationDto import InvitationDto
from app.database.sqlite.dto.userDto import UserDto
from app.flask_app import app
from app.json_validation.base import BaseValidation
from flask import abort, jsonify, make_response, request
from zxcvbn import zxcvbn


@app.get("/users/uids")
def get_users_by_uids():
    payload = {"uids": request.json.get("uids", [])}
    d7validate(
        {
            "properties": {
                "uids": {
                    "type": "array",
                    "items": BaseValidation.string,
                }
            }
        },
        payload,
    )
    users = {}
    for uid in payload["uids"]:
        user = UserDao.get_user_by_user_id(uid)
        users[uid] = pydash.objects.get(user, "username", uid)
    return make_response(jsonify(users), 200)


@app.post("/users/register")
def register():
    errors = {}
    payload = {
        "invitation_code": request.json.get("invitation_code", ""),
        "username": request.json.get("username", ""),
        "password": request.json.get("password", ""),
    }
    d7validate(
        {
            "properties": {
                "invitation_code": BaseValidation.string,
                "username": BaseValidation.string,
                "password": BaseValidation.string,
            }
        },
        payload,
    )
    # validate invitation_code
    invitation: InvitationDto = InvitationDao.get_invitation_by_invitation_code(
        invitation_code=payload["invitation_code"]
    )
    if pydash.is_none(invitation) or invitation.expires_on.replace(
        tzinfo=timezone.utc
    ) <= datetime.now(timezone.utc):
        pydash.objects.set_(
            errors, "invitation_code", f"\"{payload['invitation_code']}\" is invalid."
        )
    # validate username uniqueness
    user = UserDao.get_user_by_username(payload["username"])
    if not pydash.is_none(user):
        pydash.objects.set_(
            errors, "username", f"\"{payload['username']}\" is not available."
        )
    # verify password strength
    if pydash.is_empty(payload["password"]):
        pydash.objects.set_(errors, "password", "Password can not be empty.")
    else:
        password_result = zxcvbn(
            payload["password"],
            user_inputs=[
                "megagon",
                "labs",
                "444",
                "castro",
                "labeler",
                "meganno",
                payload["username"],
            ],
        )
        if password_result["score"] < 3:
            pydash.objects.set_(
                errors,
                "password",
                {
                    "feedback": password_result["feedback"],
                    "score": f'{password_result["score"]} out of 4',
                },
            )
    if len(errors) > 0:
        return make_response(jsonify(errors), 400)
    # create account
    password_hash = bcrypt.hashpw(
        str.encode(payload["password"]), bcrypt.gensalt()
    ).decode()
    UserDao.add(
        username=payload["username"],
        password=password_hash,
        user_id=str(uuid.uuid4().hex),
        role_id=invitation.role_id,
        invitation_id=invitation.id,
    )
    if invitation.single_use:
        InvitationDao.update_invitation_by_id(
            id=invitation.id, fields={"expires_on": datetime.now(timezone.utc)}
        )
    return make_response(jsonify({}), 200)


@app.post("/users/authenticate")
def authenticate():
    return make_response(jsonify(request.user), 200)


@app.post("/users/signin")
def signin():
    payload = {
        "username": request.json.get("username", ""),
        "password": request.json.get("password", ""),
    }
    d7validate(
        {
            "properties": {
                "username": BaseValidation.string,
                "password": BaseValidation.string,
            }
        },
        payload,
    )
    # retrieve user
    user: UserDto = UserDao.get_user_by_username(username=payload["username"])
    if not pydash.is_none(user) and not pydash.objects.get(user, "enabled", False):
        abort(401, "This account is disabled.")
    # password hash matches
    try:
        if not pydash.is_none(user) and bcrypt.checkpw(
            str.encode(payload["password"]),
            str.encode(pydash.objects.get(user, "password", "")),
        ):
            token = create_token(user.user_id, True)
            return make_response(jsonify(token), 200)
    except Exception as ex:
        abort(500, ex)
    abort(
        401,
        "The username and password you entered did not match our record. Please double check and try again.",
    )
