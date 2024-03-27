import re
from cProfile import label

from app.constants import (
    DATABASE_503_RESPONSE,
    DEFAULT_QUERY_LIMIT,
    VALID_SCHEMA_LEVELS,
    d7validate,
)
from app.core.utils import ValueNotExistsError
from app.decorators import require_role
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from flask import abort, jsonify, make_response, request


@app.route("/annotations/<string:record_uuid>", methods=["POST"])
@require_role(["administrator", "contributor", "job"])
def set_annotation_by_uuid(record_uuid):
    try:
        user_id = request.user["user_id"]
        payload = {
            "labels": request.json.get("labels", None),
            "record_uuid": record_uuid,
        }

        d7validate(
            {
                "properties": {
                    "labels": {
                        "type": "object",
                        "properties": {
                            "labels_span": {
                                "type": "array",
                                "items": BaseValidation.label,
                            },
                            "labels_record": {
                                "type": "array",
                                "items": BaseValidation.label,
                            },
                        },
                        "additionalProperties": True,
                    },
                    "record_uuid": BaseValidation.uuid,
                }
            },
            payload,
        )

        annotation_uuid = project.annotate(
            record_uuid=record_uuid, labels=payload["labels"], annotator=user_id
        )
        return make_response(
            {
                "uuid": record_uuid,
                "annotation_uuid": annotation_uuid,
                "labels": payload["labels"],
            },
            200,
        )
    except ValueNotExistsError as ex:
        return make_response(
            f"ValueNotExistsError: {record_uuid} does not exist in the database.", 400
        )
    except KeyError as ex:
        return make_response(f"Bad request: {ex} is missing.", 400)
    except Exception as ex:
        abort(500, ex)


@app.route("/annotations/batch", methods=["POST"])
@require_role(["administrator", "contributor", "job"])
def set_annotation_by_batch_uuid():
    try:
        user_id = request.user["user_id"]
        payload = {
            "annotation_list": request.json.get("annotation_list", None),
        }
        d7validate(
            {
                "properties": {
                    "annotation_list": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "properties": {
                                "labels": {
                                    "type": "object",
                                    "properties": {
                                        "labels_span": {
                                            "type": ["array", "null"],
                                            "items": BaseValidation.label,
                                        },
                                        "labels_record": {
                                            "type": ["array", "null"],
                                            "items": BaseValidation.label,
                                        },
                                    },
                                    "additionalProperties": True,
                                },
                                "record_uuid": BaseValidation.uuid,
                            },
                            "additionalProperties": True,
                        },
                    },
                }
            },
            payload,
        )
        response = project.annotate_batch(
            annotation_list=payload["annotation_list"], annotator=user_id
        )
        return make_response(jsonify(response), 200)

    except ValueNotExistsError as ex:
        return make_response(f"ValueNotExistsError: {ex}", 400)
    except KeyError as ex:
        return make_response(f"Bad request: {ex} is missing.", 400)
    except Exception as ex:
        abort(500, ex)


@app.route("/annotations/<string:record_uuid>/labels", methods=["POST"])
@require_role(["administrator", "contributor"])
def set_annotation_labels_by_uuid(record_uuid):
    try:
        user_id = request.user["user_id"]
        payload = {
            "annotator": request.json.get("annotator", None),
            "labels": request.json.get("labels", None),
            "record_uuid": record_uuid,
        }
        if payload["annotator"] is None or payload["annotator"] != "reconciliation":
            payload["annotator"] = user_id
        d7validate(
            {
                "properties": {
                    "labels": {"type": "array", "items": BaseValidation.label},
                    "record_uuid": BaseValidation.uuid,
                    "annotator": BaseValidation.string,
                }
            },
            payload,
        )
        response = project.label(
            record_uuid=record_uuid,
            labels=payload["labels"],
            annotator=payload["annotator"],
        )
        return make_response(jsonify(response), 200)
    except ValueNotExistsError as ex:
        return make_response(
            f"ValueNotExistsError: {record_uuid} does not exist in the database.", 400
        )
    except KeyError as ex:
        return make_response(f"Bad request: {ex} is missing.", 400)
    except Exception as ex:
        abort(500, ex)


@app.route("/annotations/label_metadata", methods=["POST"])
@require_role(["administrator", "contributor", "job"])
def add_metadata_to_label():
    payload = {
        "label_uuid": str(request.json.get("label_uuid", "")),
        "metadata_list": request.json.get("metadata_list", []),
    }
    d7validate(
        {
            "properties": {
                "label_uuid": BaseValidation.label_uuid,
                "metadata_list": BaseValidation.label_metadata_list,
            }
        },
        payload,
    )
    try:
        ret = project.add_metadata_to_label(
            payload["label_uuid"], payload["metadata_list"]
        )
        return make_response(jsonify(ret), 200)
    except ValueError as ve:
        return make_response(
            "Bad request: Attemping to add label metadata with metadata_name which already exists - {}".format(
                ve
            ),
            400,
        )
    except Exception as ex:
        abort(500, ex)
