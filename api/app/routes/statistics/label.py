from app.constants import (
    DEFAULT_STATISTIC_LABEL_DISTRIBUTION_AGGREGATION_FUNCTION,
    SUPPORTED_AGGREGATION_FUNCTIONS,
    d7validate,
)
from app.decorators import require_role
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from flask import jsonify, make_response, request


@app.get("/statistics/label/progress")
@require_role("administrator")
def get_label_progress():
    result = project.get_statistics().get_label_progress()
    return make_response(jsonify(result), 200)


@app.get("/statistics/label/distributions")
@require_role("administrator")
def get_label_distributions():
    payload = {
        "label_name": request.json.get("label_name", ""),
        "annotator_list": request.json.get("annotator_list", []),
        "aggregation": request.json.get(
            "aggregation", DEFAULT_STATISTIC_LABEL_DISTRIBUTION_AGGREGATION_FUNCTION
        ),
        "include_unlabeled": request.json.get("include_unlabeled", False),
    }
    d7validate(
        {
            "properties": {
                "label_name": {**BaseValidation.string, "minLength": 1},
                "annotator_list": {
                    **BaseValidation.array_or_none,
                    "items": BaseValidation.string,
                },
                "aggregation": {
                    "type": "string",
                    "enum": SUPPORTED_AGGREGATION_FUNCTIONS,
                },
                "include_unlabeled": {"type": "boolean"},
            }
        },
        payload,
    )
    result = project.get_statistics().get_label_distributions(
        label_name=payload["label_name"],
        annotator_list=payload["annotator_list"],
        aggregation=payload["aggregation"],
        include_unlabeled=payload["include_unlabeled"],
    )
    return make_response(jsonify(result), 200)
