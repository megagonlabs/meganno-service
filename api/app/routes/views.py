from app.constants import d7validate
from app.core.subset import Subset
from app.decorators import require_role
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from flask import abort, jsonify, make_response, request


def merge_views(view1, view2):
    """
    Utility function to merge two views of the same
    subset.
    Parameters
    -------------
    view1: list of object
    view2: list of object
        both views are list of objects where there's
        a mandatory field 'uuid' representing record_uuid
        The order of records should match.
    Return: a single list of objects, each item being one record
        and its views.
    """
    result = []
    for i, j in zip(view1, view2):
        assert i["uuid"] == j["uuid"]
        result.append({**i, **j})
    return result


@app.route("/annotations", methods=["GET"])
@require_role(["administrator", "contributor", "job"])
def get_annotation_list():
    payload = {
        "record_id": request.json.get("record_id", False),
        "record_content": request.json.get("record_content", True),
        "record_meta_names": request.json.get("record_meta_names", None),
        "uuid_list": request.json.get("uuid_list", None),
        "annotator_list": request.json.get("annotator_list", None),
        "label_names": request.json.get("label_names", None),
        "label_meta_names": request.json.get("label_meta_names", None),
    }

    d7validate(
        {
            "properties": {
                "record_id": BaseValidation.boolean,
                "record_content": BaseValidation.boolean,
                "record_meta_names": {
                    "type": ["array", "null"],
                    "items": {"type": BaseValidation.string},
                },
                "uuid_list": {**BaseValidation.uuid_list, "type": ["array", "null"]},
                "annotator_list": {
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
                "label_names": {
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
                "label_meta_names": {
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
            }
        },
        payload,
    )
    subset = Subset(project=project, data_uuids=payload["uuid_list"])
    view1 = subset.get_view_record(
        record_id=payload["record_id"],
        record_content=payload["record_content"],
        record_meta_names=payload["record_meta_names"],
    )

    view2 = subset.get_view_annotation(
        annotator_list=payload["annotator_list"],
        label_names=payload["label_names"],
        label_meta_names=payload["label_meta_names"],
    )
    result = merge_views(view1, view2)

    return make_response(jsonify(result), 200)


@app.route("/view/record", methods=["GET"])
@require_role(["administrator", "contributor", "job"])
def get_view_record():
    payload = {
        "record_id": request.json.get("record_id", False),
        "record_content": request.json.get("record_content", True),
        "record_meta_names": request.json.get("record_meta_names", None),
        "uuid_list": request.json.get("uuid_list", None),
    }

    d7validate(
        {
            "properties": {
                "record_id": BaseValidation.boolean,
                "record_content": BaseValidation.boolean,
                "record_meta_names": {
                    "type": ["array", "null"],
                    "items": {"type": BaseValidation.string},
                },
                "uuid_list": {**BaseValidation.uuid_list, "type": ["array", "null"]},
            }
        },
        payload,
    )

    result = Subset(project=project, data_uuids=payload["uuid_list"]).get_view_record(
        record_id=payload["record_id"],
        record_content=payload["record_content"],
        record_meta_names=payload["record_meta_names"],
    )
    return make_response(jsonify(result), 200)


@app.route("/view/annotation", methods=["GET"])
@require_role(["administrator", "contributor", "job"])
def get_view_annotation():
    payload = {
        "annotator_list": request.json.get("annotator_list", None),
        "label_names": request.json.get("label_names", None),
        "label_meta_names": request.json.get("label_meta_names", None),
        "uuid_list": request.json.get("uuid_list", None),
    }

    d7validate(
        {
            "properties": {
                "annotator_list": {
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
                "label_names": {
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
                "label_meta_names": {
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
                "uuid_list": {**BaseValidation.uuid_list, "type": ["array", "null"]},
            }
        },
        payload,
    )

    result = Subset(
        project=project, data_uuids=payload["uuid_list"]
    ).get_view_annotation(
        annotator_list=payload["annotator_list"],
        label_names=payload["label_names"],
        label_meta_names=payload["label_meta_names"],
    )
    return make_response(jsonify(result), 200)


@app.route("/view/verifications", methods=["GET"])
@require_role(["administrator", "contributor", "job"])
def get_view_verifications():
    payload = {
        "label_name": request.json.get("label_name", None),
        "label_level": request.json.get("label_level", None),
        "annotator": request.json.get("annotator", request.user["user_id"]),
        "verifier_filter": request.json.get("verifier_filter", None),
        "status_filter": request.json.get("status_filter", None),
        "uuid_list": request.json.get("uuid_list", None),
    }

    d7validate(
        {
            "properties": {
                "label_name": BaseValidation.string,
                "label_level": BaseValidation.string,
                "annotator": BaseValidation.string,
                "verifier_filter": {
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
                "status_filter": {
                    **BaseValidation.verified_type,
                    "type": ["string", "null"]
                },
                "uuid_list": {**BaseValidation.uuid_list, "type": ["array", "null"]},
            }
        },
        payload,
    )

    try:
        result = Subset(
            project=project, data_uuids=payload["uuid_list"]
        ).get_view_verification(
            label_name=payload["label_name"],
            label_level=payload["label_level"],
            annotator=payload["annotator"],
            verifier_filter=payload["verifier_filter"],
            status_filter=payload["status_filter"],
        )
        return make_response(jsonify(result), 200)
    except Exception as ex:
        abort(500, ex)


@app.route("/reconciliations", methods=["GET"])
@require_role(["administrator", "contributor"])
def get_reconciliation_data():
    payload = {"uuid_list": request.json.get("uuid_list", None)}
    d7validate({"properties": {"uuid_list": BaseValidation.uuid_list}}, payload)

    subset = Subset(project=project, data_uuids=payload["uuid_list"])

    view1 = subset.get_view_record()
    view2 = subset.get_view_annotation()
    result = merge_views(view1, view2)
    return make_response(jsonify(result), 200)


@app.route("/view/veranno", methods=["GET"])
def get_view_verified_annotations():
    pass
