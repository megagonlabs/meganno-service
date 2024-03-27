import pydash
from app.constants import d7validate
from app.core.tokens import create_token
from app.database.sqlite.dao.tokenDao import TokenDao
from app.database.sqlite.dto.tokenDto import TokenDto
from app.decorators import require_id_token, require_role
from app.flask_app import app
from app.json_validation.base import BaseValidation
from flask import abort, jsonify, make_response, request


@app.get("/tokens")
@require_id_token()
@require_role(["administrator", "contributor"])
def get_tokens():
    payload = {"job": request.json.get("job", False)}
    d7validate(
        {"properties": {"job": BaseValidation.boolean}},
        payload,
    )
    # retrieve all (job) tokens
    tokens: list[TokenDto] = TokenDao.list_tokens(
        request.user["user_id"], payload["job"], []
    )
    return make_response(
        jsonify(
            [
                {
                    "created_by": token.created_by,
                    "created_on": token.created_on,
                    "expires_on": token.expires_on,
                    "has_expiration": token.has_expiration,
                    "id": token.id,
                    "note": token.note,
                    "user_id": token.user_id,
                }
                for token in tokens
            ]
        ),
        200,
    )


@app.post("/tokens")
@require_role(["administrator", "contributor"])
def generate_token():
    payload = {
        "expiration_duration": request.json.get("expiration_duration", 14),
        "note": request.json.get("note", ""),
        "job": request.json.get("job", False),
    }
    d7validate(
        {
            "properties": {
                "expiration_duration": BaseValidation.integer,
                "note": BaseValidation.string,
                "job": BaseValidation.boolean,
            }
        },
        payload,
    )
    #  non id_token if job is True
    if request.user["id_token"] or payload["job"]:
        token = create_token(
            request.user["user_id"],
            False,
            expiration_duration=payload["expiration_duration"],
            note=payload["note"],
            job=payload["job"],
        )
        return make_response(jsonify(token), 200)
    abort(401, "Invalid token.")


@app.delete("/tokens")
@require_id_token()
@require_role(["administrator", "contributor"])
def delete_tokens():
    payload = {"ids": request.json.get("ids", [])}
    d7validate(
        {"properties": {"ids": {"type": "array", "items": BaseValidation.string}}},
        payload,
    )
    if not pydash.is_empty(payload["ids"]):
        tokens: list[TokenDto] = TokenDao.list_tokens(
            request.user["user_id"], False, payload["ids"]
        )
        for token in tokens:
            TokenDao.delete_token_by(token.id)
    return make_response(jsonify(payload["ids"]), 200)
