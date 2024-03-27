from app.constants import DATABASE_503_RESPONSE, d7validate
from app.decorators import require_role
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from flask import jsonify, make_response, request


@app.route("/assignments", methods=["GET"])
@require_role(["administrator", "contributor"])
def get_assignment():
    payload = {
        "annotator": request.json.get("annotator", request.user["user_id"]),
        "latest_only": request.json.get("latest_only", False),
    }
    # default to token owner if no annotator ID provided
    if payload["annotator"] is None:
        payload["annotator"] = request.user["user_id"]
    d7validate(
        {
            "properties": {
                "annotator": BaseValidation.string,
                "latest_only": BaseValidation.boolean,
            }
        },
        payload,
    )
    result = project.get_assignment_obj().get_assignment(
        payload["annotator"], payload["latest_only"]
    )

    assignment_list = []
    for assn in result:
        temp = {}
        temp["uuid_list"] = list(assn["data_uuid_list"])
        temp["created_on"] = str(assn["created_on"])
        temp["assigned_by"] = assn["assigned_by"]
        assignment_list.append(temp)
    return make_response(jsonify(assignment_list), 200)


@app.route("/assignments", methods=["POST"])
@require_role("administrator")
def set_assignment():
    payload = {
        "annotator": request.json.get("annotator", request.user["user_id"]),
        "subset": list(request.json.get("subset_uuid_list", [])),
    }
    d7validate(
        {
            "properties": {
                "annotator": BaseValidation.string,
                "subset": BaseValidation.uuid_list,
            }
        },
        payload,
    )
    result = project.get_assignment_obj().set_assignment(
        subset=payload["subset"],
        annotator=payload["annotator"],
        assigned_by=request.user["user_id"],
    )
    result_type = type(result)
    if result_type is dict:
        return make_response(jsonify(result), 200)
    elif result_type is bool:
        return DATABASE_503_RESPONSE
