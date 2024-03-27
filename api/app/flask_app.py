import json
import logging

import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
import datetime
import logging.handlers as handlers
import os

import boto3
import pydash
from app.constants import DATABASE_503_RESPONSE, InvalidRequestJson, bcolors
from app.core.agent_manager import AgentManager
from app.core.database import Database
from app.core.project import Project
from app.prefixMiddleware import PrefixMiddleware
from flask import Flask, Response, abort, jsonify, make_response, request
from flask_cors import CORS

from . import version

app = Flask(__name__)
APP_ENVIRONMENT = os.getenv("MEGANNO_FLASK_ENV", "production")
print(f"{bcolors.HEADER}APP_ENVIRONMENT: {APP_ENVIRONMENT}{bcolors.ENDC}")
MEGANNO_LOGGING = os.getenv("MEGANNO_LOGGING", "False").lower() == "true"
error_logger = None
traffic_logger = None
if MEGANNO_LOGGING:
    # logging
    TRAFFIC_LOG_FILE = "./logs/traffic.log"
    ERROR_LOG_FILE = "./logs/error.log"
    os.makedirs(os.path.dirname(TRAFFIC_LOG_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(ERROR_LOG_FILE), exist_ok=True)
    traffic_logger = logging.getLogger("traffic")
    traffic_logger.setLevel(logging.INFO)
    error_logger = logging.getLogger("error")
    error_logger.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    trafficLogHandler = handlers.TimedRotatingFileHandler(
        TRAFFIC_LOG_FILE, when="midnight", interval=1, backupCount=0, utc=True
    )
    trafficLogHandler.setFormatter(formatter)
    errorLogHandler = handlers.RotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=5000, backupCount=0
    )
    errorLogHandler.setFormatter(formatter)
    traffic_logger.addHandler(trafficLogHandler)
    error_logger.addHandler(errorLogHandler)
MEGANNO_NEO4J_HOST = os.getenv("MEGANNO_NEO4J_HOST", None)
MEGANNO_NEO4J_PORT = os.getenv("MEGANNO_NEO4J_PORT", 7687)
MEGANNO_AUTH_HOST = os.getenv("MEGANNO_AUTH_HOST", None)
MEGANNO_AUTH_PORT = os.getenv("MEGANNO_AUTH_PORT", None)
if pydash.is_empty(MEGANNO_AUTH_HOST):
    raise Exception("Missing required envrionment variable: MEGANNO_AUTH_HOST.")
if pydash.is_empty(MEGANNO_AUTH_PORT):
    raise Exception("Missing required envrionment variable: MEGANNO_AUTH_PORT.")
AUTH_PATH = f"{MEGANNO_AUTH_HOST}:{MEGANNO_AUTH_PORT}"
app.config["ENV"] = APP_ENVIRONMENT
CORS(app)
database_username = "neo4j"
database_password = os.getenv("MEGANNO_NEO4J_PASSWORD", None)
database_host = None
database = None
project_name = os.getenv("MEGANNO_PROJECT_NAME", None)
ecs = None
health_check = {}
try:
    if pydash.is_empty(pydash.trim(project_name)):
        raise Exception("Missing required envrionment variable: MEGANNO_PROJECT_NAME.")
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=f"/{project_name}")
    aws = boto3.Session(region_name="us-east-1")
    if aws.get_credentials() is not None:
        labeler_cluster_ARN = os.getenv("MEGANNO_CLUSTER_ARN", None)
        ecs = aws.client("ecs", region_name="us-east-1")
    if pydash.is_empty(pydash.trim(MEGANNO_NEO4J_HOST)):
        task_list = ecs.list_tasks(
            cluster=labeler_cluster_ARN,
            serviceName=("neo4j-" + project_name),
            desiredStatus="RUNNING",
            launchType="FARGATE",
        )
        task_ARNs = task_list.get("taskArns", [])
        print(f"task_ARNs {task_ARNs}")
        task_description = ecs.describe_tasks(
            cluster=labeler_cluster_ARN, tasks=task_ARNs
        )
        task_description_list = task_description.get("tasks")
        task = task_description_list[0]
        container = task.get("containers")[0]
        network_interface = pydash.objects.get(
            task, ["containers", 0, "networkInterfaces", 0], {}
        )
        private_ip = network_interface["privateIpv4Address"]
        attachmentId = network_interface["attachmentId"]
        database_host = private_ip
    else:
        database_host = MEGANNO_NEO4J_HOST
    print(f"database_host {database_host}")
    database = Database(
        uri=f"{database_host}:{MEGANNO_NEO4J_PORT}",
        username=database_username,
        password=database_password,
    )
except Exception as ex:
    raise Exception("Failed to initialize database connection", ex)
project = Project(database=database, project_name=project_name)
agent_manager = AgentManager(project=project)


@app.errorhandler(404)
def not_found_error(error):
    message = str(error)
    return Response(response=message, status=404)


@app.errorhandler(401)
def authorization_error(error):
    message = str(error)
    return Response(response=message, status=401)


@app.errorhandler(Exception)
def exception_handler(error):
    message = "There was an error with the server. Please try again later."
    if not pydash.is_equal(APP_ENVIRONMENT, "production") and not pydash.is_none(error):
        message = str(error)
    if MEGANNO_LOGGING:
        error_logger.critical(str(error), exc_info=True)
    return Response(response=message, status=500)


@app.errorhandler(500)
def internal_error(error):
    message = "There was an error with the server. Please try again later."
    if not pydash.is_equal(APP_ENVIRONMENT, "production") and not pydash.is_none(error):
        message = str(error)
    if MEGANNO_LOGGING:
        error_logger.critical(str(error), exc_info=True)
    return Response(response=message, status=500)


@app.errorhandler(InvalidRequestJson)
def invalid_api_usage(error):
    return make_response(jsonify({"json_errors": error.errors}), error.status_code)


@app.before_request
def token_verification():
    # redirect all /auth requests
    if request.path.startswith("/auth"):
        try:
            res = requests.request(
                method=request.method,
                url=request.url.replace(request.host_url, f"{AUTH_PATH}/").replace(
                    f"/{project_name}", ""
                ),
                headers={
                    k: v for k, v in request.headers if k.lower() != "host"
                },  # exclude 'host' header
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
            )
            # region exlcude some keys in :res response
            excluded_headers = [
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "connection",
            ]
            headers = [
                (k, v)
                for k, v in res.raw.headers.items()
                if k.lower() not in excluded_headers
            ]
            # END region exlcude some keys in :res response
            return Response(res.content, res.status_code, headers)
        except Exception as ex:
            abort(500, ex)
        # END edirect all /auth requests
    if int(request.args.get("url_check", 0)) == True:
        datetime_now = datetime.datetime.now()
        last_database_check = pydash.objects.get(
            health_check, "database.last_updated", datetime_now
        )
        delta = datetime_now - last_database_check
        if (
            delta.total_seconds() >= 60
            or pydash.objects.has(health_check, "database.last_updated") is False
        ):
            pydash.objects.set_(
                health_check, "database.last_updated", datetime.datetime.now()
            )
            pydash.objects.set_(
                health_check, "database.status", project.database_check()
            )
        if pydash.objects.get(health_check, "database.status", False) is False:
            return DATABASE_503_RESPONSE
        return make_response(
            {
                "version": version,
                "environment": APP_ENVIRONMENT,
                "message": "MEGAnno Service is up and running",
            },
            200,
        )
    if not pydash.objects.has(request.json, "token"):
        abort(401, "Token is missing.")
    # authenticate token
    response = requests.post(
        f"{AUTH_PATH}/auth/users/authenticate",
        json={"token": str(request.json.get("token", ""))},
    )
    if response.status_code == 401:
        abort(401, "Invalid token.")
    request.user = response.json()
    user_id = pydash.objects.get(request.user, "user_id", "-")
    username = pydash.objects.get(request.user, "username", "-")
    if MEGANNO_LOGGING:
        payload = request.json
        del payload["token"]
        traffic_logger.info(
            f"""{request.method} {request.path} - {username}({user_id})\npayload: {json.dumps(payload)}"""
        )


@app.after_request
def logging(response):
    if MEGANNO_LOGGING:
        traffic_logger.info(f"{response.status} ({response.status_code})")
    return response


from app.routes import (
    agents,
    annotations,
    assignments,
    data,
    schemas,
    verifications,
    views,
)
from app.routes.statistics import annotator, embeddings, label
