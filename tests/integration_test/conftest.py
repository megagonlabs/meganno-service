import os
import secrets
import sys
import time
import urllib.request

import docker
import requests
from cryptography.fernet import Fernet

TEST_TOKEN = ""
TEST_USER_ID = ""
MEGANNO_PROJECT_NAME = "automated_test_" + str(int(time.time()))
os.environ["MEGANNO_PROJECT_NAME"] = MEGANNO_PROJECT_NAME
MEGANNO_ADMIN_PASSWORD = secrets.token_hex(16)
MEGANNO_NEO4J_PASSWORD = secrets.token_hex(16)
os.environ["MEGANNO_NEO4J_PASSWORD"] = MEGANNO_NEO4J_PASSWORD
os.environ["MEGANNO_AUTH_PORT"] = "15001"
os.environ["MEGANNO_SERVICE_PORT"] = "15000"
os.environ["MEGANNO_NEO4J_PORT"] = "17687"
os.environ["MEGANNO_NEO4J_HOST"] = "bolt://localhost"
os.environ["MEGANNO_AUTH_HOST"] = "http://localhost"
MEGANNO_ENCRYPTION_KEY = Fernet.generate_key().decode()
os.environ["MEGANNO_ENCRYPTION_KEY"] = MEGANNO_ENCRYPTION_KEY
os.environ["MEGANNO_LOGGING"] = "True"


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


neo4j_container = None
auth_container = None


def remove_container(container):
    try:
        container.remove(force=True, v=True)
        print(f"Container {container.id} removed")
    except Exception:
        pass


try:
    client = docker.from_env()
    print(f"Starting neo4j container...")
    neo4j_container = client.containers.run(
        "neo4j:4.4.27-community",
        detach=True,
        ports={7473: 17473, 7474: 17474, 7687: 17687},
        environment={
            "NEO4J_AUTH": f"neo4j/{MEGANNO_NEO4J_PASSWORD}",
            "NEO4JLABS_PLUGINS": '["apoc","graph-data-science"]',
            "NEO4J_dbms_security_procedures_allowlist": "gds.*,apoc.*",
            "NEO4J_dbms_security_procedures_unrestricted": "gds.*,apoc.* ",
        },
        auto_remove=True,
    )
    print(f"Container neo4j-{neo4j_container.id} started")
    while True:
        try:
            time.sleep(10)
            status_code = urllib.request.urlopen("http://localhost:17474").getcode()
            if status_code == 200:
                break
        except Exception:
            pass

    print(f"Starting auth container...")
    auth_container = client.containers.run(
        "megagonlabs/meganno-service:auth-latest",
        detach=True,
        ports={15001: 15001},
        environment={
            "MEGANNO_ADMIN_PASSWORD": MEGANNO_ADMIN_PASSWORD,
            "MEGANNO_ENCRYPTION_KEY": MEGANNO_ENCRYPTION_KEY,
            "MEGANNO_PROJECT_NAME": MEGANNO_PROJECT_NAME,
            "MEGANNO_AUTH_PORT": "15001",
        },
        auto_remove=True,
    )
    print(f"Container auth-{auth_container.id} started")
    while True:
        try:
            time.sleep(10)
            status_code = urllib.request.urlopen(
                f"http://localhost:15001/auth?url_check=1"
            ).getcode()
            if status_code == 200:
                break
        except Exception:
            pass

    response = requests.post(
        f"http://localhost:15001/auth/users/signin",
        json={"username": "admin", "password": MEGANNO_ADMIN_PASSWORD},
    )
    if response.status_code == 200:
        TEST_TOKEN = response.json().get("token")
        TEST_USER_ID = response.json().get("user_id")
    else:
        raise Exception(response.text)

    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../api"))
    )
    from app.flask_app import app

    try:
        APP_TEST_CLIENT = app.test_client()
    except Exception as ex:
        remove_container(neo4j_container)
        remove_container(auth_container)
        raise ex

    class ValueStorage:
        uuid_for_post_annotations = None
        schemas = {
            "label_schema": [
                {
                    "name": "pair_validation",
                    "level": "record",
                    "options": [
                        {"value": "true", "text": "Correct pair"},
                        {"value": "false", "text": "Incorrect pair"},
                        {"value": "unresolved", "text": "Inconclusive pair"},
                    ],
                }
            ]
        }
        labels = {
            "labels_record": [
                {
                    "label_name": "pair_validation",
                    "label_value": ["true"],
                    "label_level": "record",
                }
            ]
        }
        label_condition = {
            "name": "pair_validation",
            "value": ["true"],
            "operator": "==",
        }
        uuid_list = ["WbCm7EbzShfe9xgxNBHgMDHInOo2", "inXH3LFSaHeBepHokZWv1MpfFV72"]

    def pytest_sessionstart(session):
        print(f"  Importing data", flush=True)
        response = APP_TEST_CLIENT.post(
            f"/{MEGANNO_PROJECT_NAME}/data",
            json={
                "url": "https://drive.google.com/uc?id=1w2RcWKYnF-Gj9jwJgh8Ju_uyfnyoghHN&export=download",
                "file_type": "csv",
                "token": TEST_TOKEN,
                "column_mapping": {"id": "sent_id", "content": "content"},
            },
        )
        if response.status_code != 200:
            raise Exception("Failed to import data: {}".format(response.get_data(True)))
        else:
            print(f"  {response.get_data(True)}", flush=True)

    def pytest_sessionfinish(session):
        remove_container(neo4j_container)
        remove_container(auth_container)

except Exception as ex:
    remove_container(neo4j_container)
    remove_container(auth_container)
    raise ex
except KeyboardInterrupt:
    print(
        f"{bcolors.WARNING}  Deleting service(s) due to forced termination{bcolors.ENDC}"
    )
    remove_container(neo4j_container)
    remove_container(auth_container)
