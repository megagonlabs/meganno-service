from app.constants import d7validate
from app.decorators import require_role
from app.flask_app import app, project
from app.routes.json_validation.base import BaseValidation
from flask import abort, jsonify, make_response, request


@app.get("/statistics/embeddings/<embed_type>")
@require_role("administrator")
def get_embeddings(embed_type: str = None):
    payload = {
        "embed_type": embed_type,
        "label_name": request.json.get("label_name", None),
    }
    d7validate(
        {
            "properties": {
                "embed_type": {"type": "string", "minLength": 1},
                "label_name": {**BaseValidation.string, "minLength": 1},
            }
        },
        payload,
    )
    try:
        result = project.get_statistics().get_embedding_aggregated_label(
            label_name=payload["label_name"], embedding_type=payload["embed_type"]
        )
        return make_response(jsonify(result), 200)
    except ValueError as ex:
        return make_response(str(ex), 400)
    except Exception as ex:
        abort(500, ex)
