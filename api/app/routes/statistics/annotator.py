from app.constants import d7validate
from app.decorators import require_role
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from flask import jsonify, make_response, request


@app.get("/statistics/annotator/contributions")
@require_role("administrator")
def get_annotator_contribution():
    payload = {
        "label_name": request.json.get("label_name", ""),
        "annotator_list": request.json.get("annotator_list", []),
    }
    d7validate(
        {
            "properties": {
                "label_name": BaseValidation.string,
                "annotator_list": {
                    **BaseValidation.array_or_none,
                    "items": BaseValidation.string,
                },
            }
        },
        payload,
    )
    result = project.get_statistics().get_annotator_contributions(
        label_name=payload["label_name"], annotator_list=payload["annotator_list"]
    )
    return make_response(jsonify(result), 200)


@app.get("/statistics/annotator/agreements")
@require_role("administrator")
def get_annotator_agreement():
    payload = {
        "label_name": request.json.get("label_name", ""),
        "annotator_list": request.json.get("annotator_list", []),
    }
    d7validate(
        {
            "properties": {
                "label_name": BaseValidation.string,
                "annotator_list": {
                    **BaseValidation.array_or_none,
                    "items": BaseValidation.string,
                },
            }
        },
        payload,
    )
    result = project.get_statistics().get_annotator_agreements(
        label_name=payload["label_name"], annotator_list=payload["annotator_list"]
    )
    return make_response(jsonify(result), 200)
