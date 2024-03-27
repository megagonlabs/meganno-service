import json

from app.constants import DATABASE_503_RESPONSE, d7validate
from app.decorators import require_role
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from app.routes.json_validation.schema import SchemaValidation
from flask import jsonify, make_response, request


@app.route("/schemas", methods=["GET"])
@require_role(["administrator", "contributor", "job"])
def get_schema():
    payload = {"active": request.json.get("active", None)}
    d7validate({"properties": {"active": BaseValidation.boolean}}, payload)
    result = project.get_schemas().get_values(active=payload["active"])
    schema_list = []
    for schema in result:
        temp = {}
        temp["uuid"] = schema["uuid"]
        temp["schemas"] = json.loads(schema["obj_str"])
        temp["active"] = True if schema["active"] else False
        temp["created_on"] = schema["created_on"]
        schema_list.append(temp)
    return make_response(jsonify(schema_list), 200)


@app.route("/schemas", methods=["POST"])
@require_role("administrator")
def update_schema():
    payload = request.json.get("schemas", {})
    d7validate(
        SchemaValidation.task_schema,
        payload,
    )
    result = project.get_schemas().set_values(schemas=payload)
    result_type = type(result)
    if result_type is list:
        return make_response(jsonify(result), 400)
    elif result_type is dict:
        return make_response(jsonify(result), 200)
    elif result_type is bool:
        return DATABASE_503_RESPONSE
