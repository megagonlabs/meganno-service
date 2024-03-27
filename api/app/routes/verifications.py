import pydash
from app.constants import d7validate
from app.core.subset import Subset
from app.core.utils import ValueNotExistsError
from app.decorators import require_role
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from flask import abort, jsonify, make_response, request


@app.route("/verifications/<string:record_uuid>/labels", methods=["POST"])
@require_role(["administrator", "contributor"])
def set_verification_data(record_uuid):
    try:
        payload = {
            "labels": request.json.get("labels", None),
            "label_name": request.json.get("label_name", None),
            "label_level": request.json.get("label_level", None),
            "annotator_id": request.json.get("annotator_id", None),
        }
        if payload["label_level"] != "record":
            return make_response(
                "Bad request: only supporting 'label_level=record'.", 400
            )
        d7validate(
            {
                "properties": {
                    "labels": {"type": "array", "items": BaseValidation.label},
                    "label_name": BaseValidation.string,
                    "label_level": BaseValidation.label_level,
                    "annotator_id": BaseValidation.string,
                }
            },
            payload,
        )
        if any([pydash.is_none(l["label_value"]) for l in payload["labels"]]):
            return make_response("Bad request: 'label_value' is missing.", 400)

        response_payload = {"uuid": record_uuid}
        if payload["label_level"].startswith("record"):
            verifier = request.user["user_id"]
            project.verify(
                record_uuid=record_uuid,
                annotator_id=payload["annotator_id"],
                verified_by=verifier,
                label_name=payload["label_name"],
                label_level=payload["label_level"],
                labels=payload["labels"],
            )
            return make_response(jsonify(response_payload), 200)
    except ValueNotExistsError as ex:
        return make_response(
            f"ValueNotExistsError: {record_uuid} does not exist in the database.", 400
        )
    except KeyError as ex:
        return make_response(f"Bad request: {ex} is missing.", 400)
    except Exception as ex:
        abort(500, ex)
