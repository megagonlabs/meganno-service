import pydash
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
import logging
import logging.handlers as handlers
import os

from app.constants import InvalidRequestJson, bcolors
from app.prefixMiddleware import PrefixMiddleware
from flask import Flask, Response, abort, jsonify, make_response, request

from . import version

app = Flask(__name__)
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix="/auth")
APP_ENVIRONMENT = os.getenv("MEGANNO_FLASK_ENV", "production")
app.config["ENV"] = APP_ENVIRONMENT
MEGANNO_LOGGING = os.getenv("MEGANNO_LOGGING", "False").lower() == "true"
print(f"{bcolors.HEADER}APP_ENVIRONMENT: {APP_ENVIRONMENT}{bcolors.ENDC}")
error_logger = None
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
from app.core.tokens import verify_token
from app.database.sqlite.dao.roleDao import RoleDao
from app.database.sqlite.dao.userDao import UserDao
from app.database.sqlite.dto.roleDto import RoleDto
from app.database.sqlite.dto.userDto import UserDto


@app.errorhandler(404)
def not_found_error(error):
    message = str(error)
    return Response(response=message, status=404)


@app.errorhandler(401)
def internal_error(error):
    return Response(response=str(error), status=401)


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
    if int(request.args.get("url_check", 0)) == True:
        return make_response(
            {
                "version": version,
                "environment": APP_ENVIRONMENT,
                "message": "MEGAnno Auth is up and running",
            },
            200,
        )
    IGNORE_PATH = ["/users/signin", "/users/register"]
    log = f"{request.method} {request.path}"
    if request.path not in IGNORE_PATH:
        # verify token
        token = verify_token(str(request.json.get("token", "")))
        if pydash.is_none(token):
            abort(401, "Invalid token.")
        if str(token["user_id"]).startswith("job_"):
            request.user = {
                "username": token["user_id"],
                "user_id": token["user_id"],
                "id_token": token["id_token"],
                "role_code": "job",
            }
        else:
            user: UserDto = UserDao.get_user_by_user_id(token["user_id"])
            try:
                if pydash.is_none(pydash.objects.get(user, "role_id", None)):
                    return make_response(
                        "401 Unauthorized: This user has no assigned role.",
                        401,
                    )
                if not pydash.objects.get(user, "enabled", False):
                    return make_response(
                        "401 Unauthorized: This account is disabled.", 401
                    )
                role: RoleDto = RoleDao.get_role_by_id(user.role_id)
                request.user = {
                    "username": user.username,
                    "user_id": token["user_id"],
                    "id_token": token["id_token"],
                    "role_code": pydash.objects.get(role, "code", None),
                }
            except Exception as ex:
                abort(500, ex)
        log = f"{request.method} {request.path} - {request.user.get('username', '?')}({request.user.get('user_id', '-?')})"
    if MEGANNO_LOGGING:
        traffic_logger.info(log)


@app.after_request
def logging(response):
    if MEGANNO_LOGGING:
        traffic_logger.info(f"{response.status} ({response.status_code})")
    return response


from app.routes import invitations, tokens, users
