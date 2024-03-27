import bcrypt
from app.flask_app import APP_ENVIRONMENT, MEGANNO_LOGGING, app, error_logger
from flask_sqlalchemy import SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///meganno-auth.db"
database = SQLAlchemy(app)

import os
import uuid

import pydash
from app.constants import bcolors
from app.database.sqlite.dao.roleDao import RoleDao
from app.database.sqlite.dao.userDao import UserDao
from app.database.sqlite.dto.roleDto import RoleDto
from app.database.sqlite.dto.userDto import UserDto
from flask import make_response
from sqlalchemy import exc


@app.errorhandler(exc.SQLAlchemyError)
def database_error(error):
    message = "The database was unable to process your request."
    if not pydash.is_equal(APP_ENVIRONMENT, "production") and not pydash.is_none(error):
        message = str(error)
    if MEGANNO_LOGGING:
        error_logger.critical(str(error))
    return make_response(message, 503)


with app.app_context():
    database.create_all()
    MEGANNO_ADMIN_USERNAME = os.getenv("MEGANNO_ADMIN_USERNAME", "admin")
    MEGANNO_ADMIN_PASSWORD = os.getenv("MEGANNO_ADMIN_PASSWORD", "")
    if pydash.is_empty(MEGANNO_ADMIN_USERNAME):
        raise Exception(
            "Missing required envrionment variable: MEGANNO_ADMIN_USERNAME."
        )
    if pydash.is_empty(MEGANNO_ADMIN_PASSWORD):
        raise Exception(
            "Missing required envrionment variable: MEGANNO_ADMIN_PASSWORD."
        )

    # create default roles: administrator, contributor
    roles = [
        {"code": "administrator", "name": "Administrator"},
        {"code": "contributor", "name": "Contributor"},
    ]
    for role in roles:
        database_role: RoleDto = RoleDao.get_role_by_code(role["code"])
        if pydash.is_none(database_role):
            database_role = RoleDao.add(role["code"], role["name"], None)
            print(
                f"{bcolors.OKBLUE}Created default role: {database_role.name}{bcolors.ENDC}"
            )

    # create default user
    admin_user = UserDao.get_user_by_username(MEGANNO_ADMIN_USERNAME)
    administrator_role: RoleDto = RoleDao.get_role_by_code("administrator")
    if pydash.is_none(admin_user):
        user: UserDto = UserDao.add(
            username=MEGANNO_ADMIN_USERNAME,
            password=bcrypt.hashpw(
                str.encode(MEGANNO_ADMIN_PASSWORD), bcrypt.gensalt()
            ).decode(),
            user_id=str(uuid.uuid4().hex),
            role_id=administrator_role.id,
            invitation_id=None,
        )
        print(
            f"{bcolors.OKBLUE}Created {administrator_role.name} user: {user.username}{bcolors.ENDC}"
        )
