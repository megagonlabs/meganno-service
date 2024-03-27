from app.constants import DATABASE_503_RESPONSE, d7validate
from app.decorators import require_role
from app.flask_app import agent_manager, app
from app.routes.json_validation.base import BaseValidation
from flask import jsonify, make_response, request


@app.route("/agents", methods=["GET"])
@require_role(["administrator", "contributor"])
def get_agent_list():
    payload = {
        "created_by_filter": request.json.get("created_by_filter", None),
        "provider_filter": request.json.get("provider_filter", None),
        "api_filter": request.json.get("api_filter", None),
        "show_job_list": request.json.get("show_job_list", False),
    }
    d7validate(
        {
            "properties": {
                "created_by_filter": {
                    **BaseValidation.string,
                    "type": ["array", "null"],
                    "items": BaseValidation.string,
                },
                "provider_filter": {
                    **BaseValidation.string,
                    "type": ["string", "null"],
                },
                "api_filter": {
                    **BaseValidation.string,
                    "type": ["string", "null"],
                },
                "show_job_list": {
                    **BaseValidation.boolean,
                    "type": ["boolean", "null"],
                },
            }
        },
        payload,
    )

    result = agent_manager.list_agents(
        created_by_filter=payload["created_by_filter"],
        provider_filter=payload["provider_filter"],
        api_filter=payload["api_filter"],
        show_job_list=payload["show_job_list"],
    )

    return make_response(jsonify(result), 200)


@app.route("/agents/<string:agent_uuid>/jobs", methods=["GET"])
@require_role(["administrator", "contributor"])
def get_agent_jobs(agent_uuid):
    payload = {"details": request.json.get("details", False)}
    d7validate({"properties": {"details": BaseValidation.boolean}}, payload)
    try:
        result = agent_manager.list_jobs(
            filter_by="agent_uuid",
            filter_values=[agent_uuid],
            show_agent_details=payload["details"],
        )
    except NotImplementedError as ex:
        return make_response(ex, 501)
    return make_response(jsonify(result), 200)


@app.route("/agents/jobs", methods=["GET"])
@require_role(["administrator", "contributor"])
def get_jobs_by_agents():
    payload = {
        "details": request.json.get("details", False),
        "filter_by": request.json.get("filter_by", None),
        "filter_values": request.json.get("filter_values", []),
    }
    d7validate(
        {
            "properties": {
                "details": BaseValidation.boolean,
                "filter_by": BaseValidation.filter_by,
                "filter_values": BaseValidation.uuid_list,
            }
        },
        payload,
    )
    try:
        result = agent_manager.list_jobs(
            filter_by=payload["filter_by"],
            filter_values=payload["filter_values"],
            show_agent_details=payload["details"],
        )
    except NotImplementedError as ex:
        return make_response(ex, 501)
    return make_response(jsonify(result), 200)


@app.route("/agents", methods=["POST"])
@require_role(["administrator", "contributor"])
def register_agent():
    payload = {
        "model_config": request.json.get("model_config", {}),
        "prompt_template": request.json.get("prompt_template", ""),
        "provider_api": request.json.get("provider_api", ""),
    }
    d7validate(
        {
            "properties": {
                "model_config": BaseValidation.model_config,
                "prompt_template": BaseValidation.string,
                "provider_api": BaseValidation.string,
            }
        },
        payload,
    )
    agent = agent_manager.register_agent(
        created_by=request.user["user_id"],
        model_config=payload["model_config"],
        prompt_template=payload["prompt_template"],
        provider_api=payload["provider_api"],
    )
    return make_response(jsonify(agent), 200)


@app.route("/agents/<string:agent_uuid>/jobs/<string:job_uuid>", methods=["POST"])
@require_role(["administrator", "contributor", "job"])
def persist_job(agent_uuid, job_uuid):
    payload = {
        "label_name": request.json.get("label_name", None),
        "annotation_uuid_list": request.json.get("annotation_uuid_list", []),
        "agent_uuid": agent_uuid,
        "job_uuid": job_uuid,
    }
    d7validate(
        {
            "properties": {
                "label_name": BaseValidation.string,
                "annotation_uuid_list": BaseValidation.uuid_list,
                "job_uuid": BaseValidation.uuid,
                "agent_uuid": BaseValidation.uuid,
            }
        },
        payload,
    )
    job = agent_manager.persist_job(
        job_uuid=job_uuid,
        agent_uuid=agent_uuid,
        label_name=payload["label_name"],
        issued_by=request.user["user_id"],
        annotation_uuid_list=payload["annotation_uuid_list"],
    )
    if job is False:
        return DATABASE_503_RESPONSE
    return make_response(jsonify(job), 200)
