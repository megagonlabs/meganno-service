from app.constants import (DATABASE_503_RESPONSE, DEFAULT_QUERY_LIMIT,
                           MAX_QUERY_LIMIT, d7validate)
from app.core.subset import Subset
from app.decorators import require_role
from app.enums.search_mode import VerificationSearchMode
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from flask import abort, jsonify, make_response, request
from neo4j.exceptions import CypherSyntaxError


@app.route("/data/search", methods=["GET"])
def search():
    d7validate(
        {
            "properties": {
                "limit": {"type": ["integer", "null"]},
                "skip": {"type": ["integer", "null"]},
            }
        },
        {
            "limit": request.json.get("limit"),
            "skip": request.json.get("skip"),
        },
    )

    payload = {
        "limit": int(request.json.get("limit", DEFAULT_QUERY_LIMIT)),
        "skip": int(request.json.get("skip", 0)),
        "uuid_list": request.json.get("uuid_list", None),
        "keyword": request.json.get("keyword", None),
        "regex": request.json.get("regex", None),
        "record_metadata_condition": request.json.get(
            "record_metadata_condition", None
        ),
        "annotator_list": request.json.get("annotator_list", None),
        "label_condition": request.json.get("label_condition", None),
        "label_metadata_condition": request.json.get("label_metadata_condition", None),
        "verification_condition": request.json.get("verification_condition", None),
    }
    d7validate(
        {
            "properties": {
                "limit": BaseValidation.limit,
                "skip": BaseValidation.skip,
                "uuid_list": {**BaseValidation.uuid_list, "type": ["array", "null"]},
                "keyword": {**BaseValidation.string, "type": ["string", "null"]},
                "regex": {**BaseValidation.string, "type": ["string", "null"]},
                "record_metadata_condition": {
                    "type": ["object", "null"],
                    "properties": {
                        "name": BaseValidation.string,
                        "operator": BaseValidation.operator,
                        "value": {"type": ["string", "number", "null"]},
                    },
                },
                "annotator_list": {
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
                "label_condition": {
                    "type": ["object", "null"],
                    "properties": {
                        "name": BaseValidation.string,
                        "operator": BaseValidation.label_operator,
                        "value": {
                            "type": ["array", "string", "number", "null"],
                        },
                    },
                },
                "label_metadata_condition": {
                    "type": ["object", "null"],
                    "properties": {
                        "label_name": BaseValidation.string,
                        "name": BaseValidation.string,
                        "operator": BaseValidation.operator,
                        "value": {"type": ["string", "number", "null"]},
                    },
                },
                "verification_condition": {
                    "type": ["object", "null"],
                    "properties": {
                        "label_name": BaseValidation.string,
                        "search_mode": BaseValidation.verified_status,
                    },
                },
            }
        },
        payload,
    )
    try:
        subset_uuids_list = project.search(
            limit=payload["limit"],
            skip=payload["skip"],
            uuid_list=payload["uuid_list"],
            keyword=payload["keyword"],
            regex=payload["regex"],
            record_metadata_condition=payload["record_metadata_condition"],
            annotator_list=payload["annotator_list"],
            label_condition=payload["label_condition"],
            label_metadata_condition=payload["label_metadata_condition"],
            verification_condition=payload["verification_condition"],
        )
        return make_response(jsonify(subset_uuids_list), 200)
    except KeyError as ex:

        abort(400, ex)
    except Exception as ex:
        abort(500, ex)


@app.route("/data", methods=["POST"])
@require_role("administrator")
def import_data():
    payload = {
        "url": request.json.get("url", None),
        "file_type": request.json.get("file_type", None),
        # json representation of dataframe
        "df_dict": request.json.get("df_dict", None),
        "column_mapping": request.json.get("column_mapping", {}),
    }
    if payload["file_type"] is not None:
        payload["file_type"] = payload["file_type"].upper()
    errors = verify_import_payload(url=payload["url"], file_type=payload["file_type"])
    if len(errors) != 0:
        return make_response("\n".join(errors), 400)
    d7validate(
        {
            "properties": {
                "url": {**BaseValidation.string_or_none},
                "file_type": BaseValidation.file_type,
                "df_dict": {**BaseValidation.array_or_none},
                "column_mapping": BaseValidation.column_mapping,
                "metadata": {"type": ["string", "null"]},
            }
        },
        payload,
    )
    try:
        count = 0
        if payload["file_type"].upper() == "CSV":
            count = project.import_data(
                url=payload["url"],
                file_type=payload["file_type"],
                column_mapping=payload["column_mapping"],
            )
        if payload["file_type"].upper() == "DF":
            count = project.import_data(
                url=None,
                file_type=payload["file_type"],
                df_dict=payload["df_dict"],
                column_mapping=payload["column_mapping"],
            )
        return make_response(
            f"{count} data record{'s are' if count > 1 else ' is'} imported into database.",
            200,
        )
    except Exception as ex:
        abort(500, ex)


@app.route("/data/export", methods=["GET"])
@require_role(["administrator", "contributor"])
def export_data():
    try:
        ret = project.export_data()
        return make_response(jsonify(ret), 200)
    except CypherSyntaxError:
        return DATABASE_503_RESPONSE
    except Exception as ex:
        abort(500, ex)


@app.route("/data/metadata", methods=["POST"])
@require_role("administrator")
def batch_update_metadata():
    payload = {
        "record_meta_name": str(request.json.get("record_meta_name", "")),
        "metadata_list": request.json.get("metadata_list", []),
    }
    d7validate(
        {
            "properties": {
                "record_meta_name": BaseValidation.string,
                "metadata_list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "uuid": BaseValidation.uuid,
                            "value": {"type": ["string", "array", "integer", "number"]},
                        },
                    },
                },
            }
        },
        payload,
    )
    try:
        ret = project.batch_update_metadata(
            payload["record_meta_name"], payload["metadata_list"]
        )
        return make_response(jsonify(ret), 200)
    except Exception as ex:
        abort(500, ex)


@app.route("/data/suggest_similar", methods=["GET"])
@require_role(["administrator", "contributor"])
def suggest_similar():

    payload = {
        "subset_uuids_list": request.json.get("uuid_list", []),
        "record_meta_name": request.json.get("record_meta_name", None),
        "limit": int(request.json.get("limit", DEFAULT_QUERY_LIMIT)),
    }
    d7validate(
        {
            "properties": {
                "subset_uuids_list": BaseValidation.uuid_list,
                "limit": BaseValidation.limit,
                "record_meta_name": BaseValidation.string,
            }
        },
        payload,
    )
    try:
        result = Subset(
            project=project, data_uuids=payload["subset_uuids_list"]
        ).suggest_similar(payload["record_meta_name"], payload["limit"])
    except Exception as ex:
        abort(500, ex)
    return make_response(jsonify(result), 200)


def verify_import_payload(url: str, file_type: str):
    errors = []
    if file_type.upper() == "CSV":
        if url is None or len(url.strip()) == 0:
            errors.append("'url' cannot be None/empty for CSV file type.")
    if file_type.upper() == "DF":
        if url is not None:
            errors.append("not taking url for direct dataframe import")
    return errors
